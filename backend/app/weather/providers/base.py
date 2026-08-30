from abc import ABC, abstractmethod
from typing import List
from backend.app.weather.schemas import EnsembleForecast, SupportedVariable


class BaseWeatherProvider(ABC):
    """Abstract interface defining the standard weather provider contract."""

    provider_id: str
    data_version: str

    @abstractmethod
    async def fetch_ensemble(
        self,
        *,
        location: str,
        latitude: float,
        longitude: float,
        variable: SupportedVariable,
        lead_hours: int,
    ) -> EnsembleForecast:
        """Fetch and return a canonicalized EnsembleForecast instance."""
        pass

    def apply_quality_control(
        self, values: List[float], variable: SupportedVariable
    ) -> List[float]:
        """Filter unphysical values, NaNs, and infinite readings."""
        clean_values: List[float] = []
        for val in values:
            if val is None or val != val:
                continue
            # Physical meteorological range bounds
            if variable == "temperature_2m" and not (-80.0 <= val <= 65.0):
                continue
            if variable == "precipitation" and val < 0.0:
                continue
            if variable == "wind_speed_10m" and val < 0.0:
                continue
            clean_values.append(float(val))
        return clean_values