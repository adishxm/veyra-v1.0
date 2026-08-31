# Veyra Meteorological Bust Label Policy (v4.0.0)

## 1. Mathematical Definition
A forecast bust occurs when the absolute difference between the numerical prediction ({	ext{fc}}$) and verified observation ({	ext{truth}}$) exceeds the empirical 95th percentile error threshold ({95}$):

clearY = \mathbb{I}(|y_{	ext{fc}} - y_{	ext{truth}}| \ge 	au_{q95})clear

## 2. Parameter Specifications
- **label_policy_version**: veyra-label-policy-v4.0
- **variable**: temperature_2m (°C)
- **threshold ($	au_{q95}$)**: 2.50°C
- **gray_band**: ±0.20°C boundary zone around threshold where abstention reason codes flag border cases.
- **missingness_policy**: If valid-time ground truth observation is unavailable within 3 hours of verification timestamp, record is flagged PENDING_VERIFICATION and omitted from calibration re-fit.
- **correction_history**: Corrections append immutable versioned log entries to SQLite actuals table without mutating historical raw ingestion records.
