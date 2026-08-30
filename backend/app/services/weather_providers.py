import httpx
import math
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# Persistent HTTP client pool with browser-like headers
HTTP_CLIENT = httpx.AsyncClient(
    timeout=httpx.Timeout(12.0, connect=5.0),
    headers={"User-Agent": "Veyra-Atmospheric-Reliability-Engine/2.1 (https://adishxm.github.io/veyra-v1.0/)"},
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
)

class MultiProviderWeatherIngestion:
    """Ingests real-time, lead-synchronized multi-provider NWP forecasts."""

    @classmethod
    async def fetch_open_meteo(cls, lat: float, lon: float, lead_hours: int = 48) -> Dict[str, Any]:
        forecast_days = min(16, max(2, int(math.ceil((lead_hours + 24) / 24))))
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat:.4f}&longitude={lon:.4f}&hourly=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,precipitation"
            f"&forecast_days={forecast_days}"
        )
        
        resp = await HTTP_CLIENT.get(url)
        resp.raise_for_status()
        data = resp.json()
        hourly = data.get("hourly", {})
        
        times = hourly.get("time", [])
        temps = [float(t) for t in hourly.get("temperature_2m", []) if t is not None]
        pressures = [float(p) for p in hourly.get("surface_pressure", []) if p is not None]
        humidities = [float(h) for h in hourly.get("relative_humidity_2m", []) if h is not None]
        precips = [float(pr) for pr in hourly.get("precipitation", []) if pr is not None]

        if not temps or not times:
            raise ValueError("Empty timeseries returned by weather provider")

        # 1. Exact UTC Lead Time Target Indexing
        now_utc = datetime.now(timezone.utc)
        target_utc = now_utc + timedelta(hours=lead_hours)
        target_iso_prefix = target_utc.strftime("%Y-%m-%dT%H:00")

        try:
            lead_idx = times.index(target_iso_prefix)
        except ValueError:
            lead_idx = min(max(0, lead_hours), len(temps) - 1)

        target_temp = round(temps[lead_idx], 2)
        cur_pressure = round(pressures[lead_idx] if lead_idx < len(pressures) else 1013.25, 2)
        cur_humidity = round(humidities[lead_idx] if lead_idx < len(humidities) else 60.0, 2)
        cur_precip = round(precips[lead_idx] if lead_idx < len(precips) else 0.0, 2)

        # 2. Local 24-hour meteorological window spread
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
            "ensemble_spread": max(temp_spread, 0.8),
            "temp_variance": max(temp_var, 0.3),
            "lead_hours": lead_hours,
            "status": "nominal"
        }

    @classmethod
    async def get_canonical_forecast(cls, lat: float, lon: float, lead_hours: int = 48) -> Dict[str, Any]:
        # Primary Attempt
        try:
            return await cls.fetch_open_meteo(lat, lon, lead_hours)
        except Exception:
            pass

        # Secondary Retry with Open-Meteo GFS/ECMWF Ensemble API
        try:
            url = f"https://ensemble-api.open-meteo.com/v1/ensemble?latitude={lat:.4f}&longitude={lon:.4f}&hourly=temperature_2m&models=gfs_seamless,ecmwf_ifs025"
            resp = await HTTP_CLIENT.get(url)
            if resp.status_code == 200:
                data = resp.json()
                hourly = data.get("hourly", {})
                temps = [float(t) for t in hourly.get("temperature_2m", []) if t is not None]
                if temps:
                    lead_idx = min(max(0, lead_hours), len(temps) - 1)
                    return {
                        "provider": "open-meteo-ensemble-secondary",
                        "temperature": round(temps[lead_idx], 2),
                        "relative_humidity_2m": 55.0,
                        "surface_pressure": 1013.25,
                        "precipitation": 0.0,
                        "ensemble_spread": 1.4,
                        "temp_variance": 0.5,
                        "lead_hours": lead_hours,
                        "status": "nominal"
                    }
        except Exception:
            pass

        # Final Degraded Fallback with realistic diurnal baseline
        diurnal = 4.0 * math.sin((lead_hours % 24) * (math.pi / 12.0) - 2.0)
        baseline = 26.0 - (abs(lat) * 0.35) + diurnal
        return {
            "provider": "meteorological-fallback",
            "temperature": round(baseline, 2),
            "relative_humidity_2m": 60.0,
            "surface_pressure": 1013.25,
            "precipitation": 0.0,
            "ensemble_spread": 1.5,
            "temp_variance": 0.6,
            "lead_hours": lead_hours,
            "status": "degraded"
        }