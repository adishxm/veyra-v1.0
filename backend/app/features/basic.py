from statistics import mean, pstdev

from backend.app.weather.schemas import EnsembleForecast


FEATURE_SCHEMA_VERSION = "personal-veyra-features-v1"


def build_features(forecast: EnsembleForecast) -> dict[str, float]:
    values = forecast.values
    average = mean(values)
    spread = pstdev(values)
    return {
        "forecast_mean": average,
        "forecast_spread": spread,
        "forecast_range": max(values) - min(values),
        "lead_hours": float(forecast.lead_hours),
        "latitude": forecast.latitude,
        "longitude": forecast.longitude,
        "member_count": float(len(values)),
    }
