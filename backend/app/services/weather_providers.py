import httpx
import math
import numpy as np
from typing import Dict, Any

class MultiProviderWeatherIngestion:
    """Ingests authentic multi-day NWP hourly forecast series per location and lead time."""

    @classmethod
    async def fetch_open_meteo(cls, lat: float, lon: float, lead_hours: int = 48) -> Dict[str, Any]:
        forecast_days = min(14, max(3, (lead_hours // 24) + 2))
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,precipitation"
            f"&forecast_days={forecast_days}"
        )
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            hourly = data.get("hourly", {})
            
            temps = [float(t) for t in hourly.get("temperature_2m", []) if t is not None and not math.isnan(float(t))]
            pressures = [float(p) for p in hourly.get("surface_pressure", []) if p is not None and not math.isnan(float(p))]
            humidities = [float(h) for h in hourly.get("relative_humidity_2m", []) if h is not None and not math.isnan(float(h))]
            precips = [float(pr) for pr in hourly.get("precipitation", []) if pr is not None and not math.isnan(float(pr))]

            if not temps:
                raise ValueError("No valid temperature timeseries returned")

            lead_idx = min(max(0, lead_hours), len(temps) - 1)
            target_temp = round(temps[lead_idx], 2)
            cur_pressure = round(pressures[lead_idx] if lead_idx < len(pressures) else 1013.25, 2)
            cur_humidity = round(humidities[lead_idx] if lead_idx < len(humidities) else 60.0, 2)
            cur_precip = round(precips[lead_idx] if lead_idx < len(precips) else 0.0, 2)

            # Atmospheric variability across the 24-hour temporal window around the target lead
            window_start = max(0, lead_idx - 12)
            window_end = min(len(temps), lead_idx + 13)
            window_temps = temps[window_start:window_end]

            temp_spread = round(float(np.std(window_temps)), 2) if len(window_temps) > 1 else 1.2
            temp_var = round(float(np.var(window_temps)), 2) if len(window_temps) > 1 else 0.45

            return {
                "provider": "open-meteo-primary",
                "temperature": target_temp,
                "relative_humidity_2m": cur_humidity,
                "surface_pressure": cur_pressure,
                "precipitation": cur_precip,
                "ensemble_spread": max(temp_spread, 0.75),
                "temp_variance": max(temp_var, 0.25),
                "lead_hours": lead_hours,
                "status": "nominal"
            }

    @classmethod
    async def get_canonical_forecast(cls, lat: float, lon: float, lead_hours: int = 48) -> Dict[str, Any]:
        try:
            return await cls.fetch_open_meteo(lat, lon, lead_hours)
        except Exception:
            pass

        # Geophysical latitude-gradient and diurnal fallback
        diurnal = 3.0 * math.sin((lead_hours % 24) * (math.pi / 12.0) - 2.0)
        simulated_temp = round(32.0 - (abs(lat) * 0.58) + diurnal, 2)
        return {
            "provider": "geophysical-model-fallback",
            "temperature": simulated_temp,
            "relative_humidity_2m": 60.0,
            "surface_pressure": 1013.25,
            "precipitation": 0.0,
            "ensemble_spread": 1.40,
            "temp_variance": 0.50,
            "lead_hours": lead_hours,
            "status": "degraded"
        }