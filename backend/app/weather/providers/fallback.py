from datetime import datetime, timedelta, timezone
from backend.app.weather.providers.base import BaseWeatherProvider
from backend.app.weather.schemas import EnsembleForecast, SupportedVariable


class FallbackEnsembleProvider(BaseWeatherProvider):
    """Regional fallback provider adhering to NCMRWF/NEPS structural specifications."""

    provider_id = "ncmrwf-neps-resilience"
    data_version = "neps-fixture-v2"

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

        # Baseline climatological distribution normalized for latitude
        base_temp = 28.0 - (abs(latitude) * 0.2)
        simulated_members = [
            round(base_temp - 1.8, 2),
            round(base_temp - 0.7, 2),
            round(base_temp + 0.1, 2),
            round(base_temp + 1.2, 2),
            round(base_temp + 2.3, 2),
            round(base_temp + 3.1, 2),
        ]

        clean_values = self.apply_quality_control(simulated_members, variable)

        return EnsembleForecast(
            location=location,
            latitude=latitude,
            longitude=longitude,
            variable=variable,
            issue_time=now,
            valid_time=target_time,
            lead_hours=lead_hours,
            values=clean_values,
            unit="°C",
            provider=self.provider_id,
            data_version=self.data_version,
        )