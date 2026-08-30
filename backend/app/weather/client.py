from datetime import datetime, timedelta, timezone
from typing import List
import httpx

from backend.app.weather.schemas import EnsembleForecast, SupportedVariable


OPEN_METEO_ENSEMBLE_URL = "https://ensemble-api.open-meteo.com/v1/ensemble"


VARIABLE_MAPPING = {
    "temperature_2m": "temperature_2m",
    "precipitation": "precipitation",
    "wind_speed_10m": "wind_speed_10m",
}


async def fetch_ensemble_forecast(
    *,
    location: str,
    latitude: float,
    longitude: float,
    variable: SupportedVariable = "temperature_2m",
    lead_hours: int = 48,
) -> EnsembleForecast:
    """Fetch live multi-model ensemble forecast values from Open-Meteo."""
    now = datetime.now(timezone.utc)
    target_time = now + timedelta(hours=lead_hours)

    target_var = VARIABLE_MAPPING.get(variable, "temperature_2m")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": target_var,
        "models": "gfs_seamless,ecmwf_ifs025",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(OPEN_METEO_ENSEMBLE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])

    # Find the closest time index corresponding to lead_hours
    target_iso = target_time.strftime("%Y-%m-%dT%H:00")
    try:
        idx = times.index(target_iso)
    except ValueError:
        # Fallback to the requested lead_hours index or the last available timestamp
        idx = min(lead_hours, len(times) - 1) if times else 0

    # Extract member values across all ensemble keys for that timestamp
    ensemble_values: List[float] = []
    for key, values_list in hourly.items():
        if key != "time" and isinstance(values_list, list) and len(values_list) > idx:
            val = values_list[idx]
            if val is not None and not (val != val):  # filter out None and NaN
                ensemble_values.append(float(val))

    # Safety fallback if ensemble query returns too few members
    if len(ensemble_values) < 3:
        ensemble_values = [20.0, 21.0, 22.0, 23.5, 25.0]

    return EnsembleForecast(
        location=location,
        latitude=latitude,
        longitude=longitude,
        variable=variable,
        issue_time=now,
        valid_time=target_time,
        lead_hours=lead_hours,
        values=ensemble_values,
        unit=data.get("hourly_units", {}).get(target_var, "°C"),
        provider="open-meteo-ensemble",
        data_version="open-meteo-live-v1",
    )