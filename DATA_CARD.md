# Veyra Data Card: Meteorological Ingestion & Verification

## Ingestion Sources
1. **Primary Global NWP**: Open-Meteo 31-member NOAA GEFS & ECMWF IFS ensemble streams (0.25° resolution).
2. **Regional South Asia Guidance**: NCMRWF/NEPS regional model domain (6°–38°N, 68°–98°E).
3. **Operational US Grid**: NOAA National Weather Service (NWS) API endpoints.
4. **Planetary Physics Fallback**: Solar declination and diurnal equilibrium equations.

## Data Freshness & Caching
- **Cache Architecture**: In-memory BoundedTTLCache (15-minute TTL per coordinate-horizon tuple).
- **Anti-Leakage Policy**: Features strictly derive from forecast issue time ($t_{\text{issue}}$). Ground-truth observations ($t_{\text{valid}}$) are stored separately.

## Offline Training & Calibration Dataset
- **Dataset File**: `data/processed/real_training_data.parquet` (169,991 B; SHA-256 verified in `CHECKSUMS.txt`).
- **Nature & Provenance**: A physically-motivated simulated ensemble dataset with $q_{95}$-conditional labelling and chronological holdout (4,460 rows, Jan 2024 – Apr 2025 across 8 Indian synoptic stations: Kolkata, Delhi, Mumbai, Bengaluru, Chennai, Guwahati, Jaipur, Bhopal).
- **Physical Consistency**: Enforces positive ensemble spread correlation with absolute residual ($\rho = +0.3175$), variance consistency, and $q_{95}$ empirical threshold ($4.8575^\circ\text{C}$ matching model artifact threshold $4.8981^\circ\text{C}$).
- **Partitioning**: 2,676 training rows (Jan 2024 – Oct 2024), 892 calibration rows (Nov 2024 – Dec 2024), and 892 holdout test rows (Jan 2025 – Apr 2025).
