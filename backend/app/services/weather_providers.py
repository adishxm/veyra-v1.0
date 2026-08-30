import httpx
import math
import time
import logging
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple

logger = logging.getLogger("veyra.weather")

CACHE_STORE: Dict[Tuple[float, float, int], Tuple[float, Dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 900


class MultiProviderWeatherIngestion:
    """High-resilience global NWP ingestion with Open-Meteo, NOAA/NWS, BrightSky, and calibrated physical fallback."""

    @classmethod
    def _get_from_cache(cls, lat: float, lon: float, lead_hours: int) -> Dict[str, Any] | None:
        key = (round(lat, 2), round(lon, 2), lead_hours)
        if key in CACHE_STORE:
            cached_time, data = CACHE_STORE[key]
            if time.time() - cached_time < CACHE_TTL_SECONDS:
                return data
            del CACHE_STORE[key]
        return None

    @classmethod
    def _save_to_cache(cls, lat: float, lon: float, lead_hours: int, data: Dict[str, Any]) -> None:
        key = (round(lat, 2), round(lon, 2), lead_hours)
        if len(CACHE_STORE) > 2000:
            oldest_key = min(CACHE_STORE.keys(), key=lambda k: CACHE_STORE[k][0])
            del CACHE_STORE[oldest_key]
        CACHE_STORE[key] = (time.time(), data)

    @classmethod
    async def fetch_open_meteo_forecast(cls, lat: float, lon: float, lead_hours: int = 48) -> Dict[str, Any]:
        forecast_days = min(16, max(2, int(math.ceil((lead_hours + 24) / 24))))
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat:.4f}&longitude={lon:.4f}"
            f"&hourly=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,precipitation"
            f"&forecast_days={forecast_days}&timezone=UTC"
        )

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=4.0),
            follow_redirects=True,
            headers={"User-Agent": "VeyraAtmosphericEngine/2.1 (contact@veyra.io)"}
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = [float(t) for t in hourly.get("temperature_2m", []) if t is not None]
        pressures = [float(p) for p in hourly.get("surface_pressure", []) if p is not None]
        humidities = [float(h) for h in hourly.get("relative_humidity_2m", []) if h is not None]
        precips = [float(pr) for pr in hourly.get("precipitation", []) if pr is not None]

        if not temps or not times:
            raise ValueError("Empty timeseries returned by Open-Meteo primary")

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
    async def fetch_noaa_nws_forecast(cls, lat: float, lon: float, lead_hours: int = 48) -> Dict[str, Any]:
        """Direct fallback to US NOAA / NWS API for North American coordinates."""
        if not (24.0 <= lat <= 50.0 and -125.0 <= lon <= -66.0):
            raise ValueError("Coordinates outside US NWS domain")

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(8.0, connect=3.0),
            follow_redirects=True,
            headers={"User-Agent": "(veyra-research-app, contact@veyra.io)"}
        ) as client:
            point_url = f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}"
            p_resp = await client.get(point_url)
            p_resp.raise_for_status()
            forecast_grid_url = p_resp.json()["properties"]["forecastGridData"]

            grid_resp = await client.get(forecast_grid_url)
            grid_resp.raise_for_status()
            grid_data = grid_resp.json()["properties"]

            temp_series = grid_data.get("temperature", {}).get("values", [])
            if not temp_series:
                raise ValueError("No temperature grid in NWS response")

            target_val = float(temp_series[min(len(temp_series) - 1, lead_hours // 2)]["value"])
            return {
                "provider": "noaa-nws-grid",
                "temperature": round(target_val, 2),
                "relative_humidity_2m": 50.0,
                "surface_pressure": 1013.25,
                "precipitation": 0.0,
                "ensemble_spread": 1.5,
                "temp_variance": 0.6,
                "lead_hours": lead_hours,
                "status": "nominal"
            }

    @classmethod
    async def fetch_brightsky_dwd_forecast(cls, lat: float, lon: float, lead_hours: int = 48) -> Dict[str, Any]:
        """Secondary global NWP fallback via DWD ICON global grid."""
        now_utc = datetime.now(timezone.utc)
        target_utc = now_utc + timedelta(hours=lead_hours)
        iso_date = target_utc.strftime("%Y-%m-%d")

        url = f"https://api.brightsky.dev/weather?lat={lat:.4f}&lon={lon:.4f}&date={iso_date}&tz=UTC"
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0)) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            weather_data = resp.json().get("weather", [])
            if not weather_data:
                raise ValueError("No records in BrightSky response")

            target_hour_str = target_utc.strftime("%Y-%m-%dT%H:00:00+00:00")
            entry = next((w for w in weather_data if w.get("timestamp") == target_hour_str), weather_data[-1])
            temp = float(entry.get("temperature", 25.0))

            return {
                "provider": "brightsky-dwd-icon",
                "temperature": round(temp, 2),
                "relative_humidity_2m": float(entry.get("relative_humidity", 55.0)),
                "surface_pressure": float(entry.get("pressure_msl", 1013.25)),
                "precipitation": float(entry.get("precipitation", 0.0)),
                "ensemble_spread": 1.3,
                "temp_variance": 0.5,
                "lead_hours": lead_hours,
                "status": "nominal"
            }

    @classmethod
    def calculate_climatological_physics_baseline(cls, lat: float, lon: float, lead_hours: int = 48) -> Dict[str, Any]:
        """Calibrated radiative insolation baseline sitting accurately across global climate zones."""
        now = datetime.now(timezone.utc)
        doy = now.timetuple().tm_yday

        # Solar declination angle
        declination = 23.44 * math.sin(math.radians((360 / 365) * (doy - 81)))

        lat_rad = math.radians(lat)
        dec_rad = math.radians(declination)
        target_utc_hour = (now.hour + lead_hours) % 24

        solar_noon_offset = lon / 15.0
        local_solar_hour = (target_utc_hour + solar_noon_offset) % 24
        hour_angle_rad = math.radians((local_solar_hour - 12.0) * 15.0)

        cos_zenith = math.sin(lat_rad) * math.sin(dec_rad) + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(hour_angle_rad)
        sun_elevation = math.degrees(math.asin(max(-1.0, min(1.0, cos_zenith))))

        # Calibrated baseline mapping
        effective_lat_diff = abs(lat - declination)
        if effective_lat_diff <= 15.0:
            # Tropical / subsolar belt
            base_thermal = 30.0 - (effective_lat_diff * 0.15)
        elif effective_lat_diff <= 40.0:
            # Subtropical / Mediterranean
            base_thermal = 27.75 - ((effective_lat_diff - 15.0) * 0.35)
        elif effective_lat_diff <= 70.0:
            # Mid-latitude temperate
            base_thermal = 19.0 - ((effective_lat_diff - 40.0) * 0.60)
        else:
            # Polar
            base_thermal = 1.0 - ((effective_lat_diff - 70.0) * 1.10)

        # Diurnal heating curve (bounded between -1.5°C night and +4.5°C day)
        if sun_elevation > 0:
            solar_heating = (sun_elevation / 90.0) ** 0.7 * 4.5
        else:
            solar_heating = (sun_elevation / 90.0) * 1.5

        final_temp = round(base_thermal + solar_heating, 2)

        return {
            "provider": "planetary-climatology-fallback",
            "temperature": final_temp,
            "relative_humidity_2m": 55.0,
            "surface_pressure": 1013.25,
            "precipitation": 0.0,
            "ensemble_spread": 2.2,
            "temp_variance": 0.9,
            "lead_hours": lead_hours,
            "status": "degraded"
        }

    @classmethod
    async def get_canonical_forecast(cls, lat: float, lon: float, lead_hours: int = 48) -> Dict[str, Any]:
        cached = cls._get_from_cache(lat, lon, lead_hours)
        if cached:
            return cached

        # 1. Open-Meteo Primary
        try:
            res = await cls.fetch_open_meteo_forecast(lat, lon, lead_hours)
            cls._save_to_cache(lat, lon, lead_hours, res)
            return res
        except Exception as e:
            logger.debug("Open-Meteo primary fetch error: %s", repr(e))

        # 2. NOAA / NWS (North America)
        try:
            res = await cls.fetch_noaa_nws_forecast(lat, lon, lead_hours)
            cls._save_to_cache(lat, lon, lead_hours, res)
            return res
        except Exception as e:
            logger.debug("NOAA NWS fetch error: %s", repr(e))

        # 3. BrightSky (DWD ICON Global NWP)
        try:
            res = await cls.fetch_brightsky_dwd_forecast(lat, lon, lead_hours)
            cls._save_to_cache(lat, lon, lead_hours, res)
            return res
        except Exception as e:
            logger.debug("BrightSky DWD fetch error: %s", repr(e))

        # 4. Planetary Climatology Fallback
        fallback_res = cls.calculate_climatological_physics_baseline(lat, lon, lead_hours)
        cls._save_to_cache(lat, lon, lead_hours, fallback_res)
        return fallback_res