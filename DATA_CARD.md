# Veyra Data Card: Meteorological Ingestion & Verification

## Ingestion Sources
1. **Primary Global NWP**: Open-Meteo 31-member NOAA GEFS & ECMWF IFS ensemble streams (0.25° resolution).
2. **Regional South Asia Guidance**: NCMRWF/NEPS regional model domain (6°–38°N, 68°–98°E).
3. **Operational US Grid**: NOAA National Weather Service (NWS) API endpoints.
4. **Planetary Physics Fallback**: Solar declination and diurnal equilibrium equations.

## Data Freshness & Caching
- **Cache Architecture**: In-memory BoundedTTLCache (15-minute TTL per coordinate-horizon tuple).
- **Anti-Leakage Policy**: Features strictly derive from forecast issue time ({	ext{issue}}$). Ground-truth observations ({	ext{valid}}$) are stored separately.
