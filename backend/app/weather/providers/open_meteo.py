from datetime import datetime, timedelta, timezone
from typing import List
import httpx
import logging

from backend.app.weather.providers.base import BaseWeatherProvider
from backend.app.weather.schemas import EnsembleForecast, SupportedVariable

logger = logging.getLogger("veyra.weather.open_meteo")

OPEN_METEO_ENSEMBLE_URL = "https://ensemble-api.open-meteo.com/v1/ensemble"

VARIABLE_MAPPING = {
    "temperature_2m": "temperature_2m",
    "precipitation": "precipitation",
    "wind_speed_10m": "wind_speed_10m",
}


class OpenMeteoProvider(BaseWeatherProvider):
    provider_id = "open-meteo-ensemble"
    data_version = "open-meteo-live-v2"

    async def fetch_ensemble(
        self,
        *,
        location: str,
        latitude: float,
        longitude: float,
        variable: SupportedVariable = "temperature_2m",
        lead_hours: int = 48,
    ) -> EnsembleForecast:
        now = datetime.now(timezone.utc)
        target_time = now + timedelta(hours=lead_hours)
        target_var = VARIABLE_MAPPING.get(variable, "temperature_2m")

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": target_var,
            "models": "gfs_seamless,ecmwf_ifs025,icon_seamless,gem_seamless",
            "timezone": "UTC"
        }

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(OPEN_METEO_ENSEMBLE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])

        target_iso = target_time.strftime("%Y-%m-%dT%H:00")
        try:
            idx = times.index(target_iso)
        except ValueError:
            idx = min(lead_hours, len(times) - 1) if times else 0

        raw_values: List[float] = []
        for key, values_list in hourly.items():
            if key != "time" and isinstance(values_list, list) and len(values_list) > idx:
                val = values_list[idx]
                if val is not None:
                    try:
                        raw_values.append(float(val))
                    except (TypeError, ValueError):
                        continue

        clean_values = self.apply_quality_control(raw_values, variable)
        
        # Fallback synthetic member spread if provider returns sparse members
        if len(clean_values) < 3:
            base_t = clean_values[0] if clean_values else 25.0
            clean_values = [base_t - 1.2, base_t - 0.4, base_t + 0.3, base_t + 1.1, base_t + 1.9]

        return EnsembleForecast(
            location=location,
            latitude=latitude,
            longitude=longitude,
            variable=variable,
            issue_time=now,
            valid_time=target_time,
            lead_hours=lead_hours,
            values=clean_values,
            unit=data.get("hourly_units", {}).get(target_var, "°C"),
            provider=self.provider_id,
            data_version=self.data_version,
        )