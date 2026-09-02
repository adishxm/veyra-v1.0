import logging
import time
from typing import Dict, Tuple, Any

from backend.app.weather.providers.base import BaseWeatherProvider
from backend.app.weather.providers.fallback import FallbackEnsembleProvider
from backend.app.weather.providers.open_meteo import OpenMeteoProvider
from backend.app.weather.schemas import EnsembleForecast, SupportedVariable

logger = logging.getLogger("veyra.weather.service")


class WeatherService:
    def __init__(self):
        self.providers: list[BaseWeatherProvider] = [
            OpenMeteoProvider(),
            FallbackEnsembleProvider(),
        ]
        # In-memory bounded TTL cache: (lat, lon, variable, lead_hours) -> (timestamp, EnsembleForecast)
        self._cache: Dict[Tuple[float, float, str, int], Tuple[float, EnsembleForecast]] = {}
        self.cache_ttl_seconds: float = 900.0  # 15 minutes TTL

    def _get_from_cache(
        self, latitude: float, longitude: float, variable: str, lead_hours: int
    ) -> EnsembleForecast | None:
        key = (round(latitude, 2), round(longitude, 2), variable, lead_hours)
        if key in self._cache:
            timestamp, cached_forecast = self._cache[key]
            if time.time() - timestamp < self.cache_ttl_seconds:
                return cached_forecast
            del self._cache[key]
        return None

    def _store_in_cache(
        self, latitude: float, longitude: float, variable: str, lead_hours: int, forecast: EnsembleForecast
    ) -> None:
        key = (round(latitude, 2), round(longitude, 2), variable, lead_hours)
        # Bounded cache eviction if size exceeds 2,000 entries
        if len(self._cache) > 2000:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        self._cache[key] = (time.time(), forecast)

    async def get_forecast(
        self,
        *,
        location: str,
        latitude: float,
        longitude: float,
        variable: SupportedVariable = "temperature_2m",
        lead_hours: int = 48,
    ) -> EnsembleForecast:
        # 1. Check TTL cache
        cached = self._get_from_cache(latitude, longitude, str(variable), lead_hours)
        if cached is not None:
            return cached

        errors = []
        # 2. Iterate through configured providers with automatic failover
        for provider in self.providers:
            try:
                forecast = await provider.fetch_ensemble(
                    location=location,
                    latitude=latitude,
                    longitude=longitude,
                    variable=variable,
                    lead_hours=lead_hours,
                )
                self._store_in_cache(latitude, longitude, str(variable), lead_hours, forecast)
                return forecast
            except Exception as e:
                logger.warning(
                    "Weather provider %s failed: %s. Attempting next provider.",
                    provider.provider_id,
                    str(e),
                )
                errors.append(f"{provider.provider_id}: {str(e)}")

        # 3. If primary and fallback providers both raise, synthesize an emergency safety forecast
        logger.error("All configured weather providers failed: %s", "; ".join(errors))
        fallback_provider = FallbackEnsembleProvider()
        emergency_forecast = await fallback_provider.fetch_ensemble(
            location=location,
            latitude=latitude,
            longitude=longitude,
            variable=variable,
            lead_hours=lead_hours,
        )
        self._store_in_cache(latitude, longitude, str(variable), lead_hours, emergency_forecast)
        return emergency_forecast


weather_service = WeatherService()