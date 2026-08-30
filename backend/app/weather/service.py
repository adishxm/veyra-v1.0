import logging
from backend.app.weather.providers.base import BaseWeatherProvider
from backend.app.weather.providers.fallback import FallbackEnsembleProvider
from backend.app.weather.providers.open_meteo import OpenMeteoProvider
from backend.app.weather.schemas import EnsembleForecast, SupportedVariable

logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(self):
        self.providers: list[BaseWeatherProvider] = [
            OpenMeteoProvider(),
            FallbackEnsembleProvider(),
        ]

    async def get_forecast(
        self,
        *,
        location: str,
        latitude: float,
        longitude: float,
        variable: SupportedVariable = "temperature_2m",
        lead_hours: int = 48,
    ) -> EnsembleForecast:
        errors = []
        for provider in self.providers:
            try:
                forecast = await provider.fetch_ensemble(
                    location=location,
                    latitude=latitude,
                    longitude=longitude,
                    variable=variable,
                    lead_hours=lead_hours,
                )
                return forecast
            except Exception as e:
                logger.warning(
                    "Provider %s failed: %s. Attempting fallback.",
                    provider.provider_id,
                    str(e),
                )
                errors.append(f"{provider.provider_id}: {str(e)}")

        raise RuntimeError(f"All weather providers failed: {'; '.join(errors)}")


weather_service = WeatherService()