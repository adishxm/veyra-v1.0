from statistics import mean, median, pstdev
from backend.app.weather.schemas import EnsembleForecast

FEATURE_SCHEMA_VERSION = "personal-veyra-features-v2"


def _percentile(sorted_data: list[float], percent: float) -> float:
    """Calculate the percentile value from a sorted list of floats."""
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * (percent / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_data) - 1)
    d = k - f
    return sorted_data[f] + (sorted_data[c] - sorted_data[f]) * d


def build_features(forecast: EnsembleForecast) -> dict[str, float]:
    values = sorted(forecast.values)
    n = len(values)
    
    avg = mean(values)
    med = median(values)
    spread = pstdev(values)
    val_min = values[0]
    val_max = values[-1]
    
    # Quantiles for robust distribution analysis
    p10 = _percentile(values, 10.0)
    p25 = _percentile(values, 25.0)
    p75 = _percentile(values, 75.0)
    p90 = _percentile(values, 90.0)
    iqr = p75 - p25

    # Relative dispersion metric
    coef_var = (spread / abs(avg)) if abs(avg) > 1e-4 else 0.0

    return {
        # Core baseline features
        "forecast_mean": round(avg, 4),
        "forecast_median": round(med, 4),
        "forecast_spread": round(spread, 4),
        "forecast_range": round(val_max - val_min, 4),
        "lead_hours": float(forecast.lead_hours),
        "latitude": forecast.latitude,
        "longitude": forecast.longitude,
        "member_count": float(n),

        # Advanced distributional features
        "iqr": round(iqr, 4),
        "p10": round(p10, 4),
        "p90": round(p90, 4),
        "skewness_proxy": round(avg - med, 4),
        "coefficient_of_variation": round(coef_var, 4),
    }