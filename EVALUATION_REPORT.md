# Veyra V4.0 ML Scientific Evaluation Report

## 1. Temporal & Geographic Partitioning
- **Temporal Split**: 70% Training (historical baseline), 15% Held-Out Validation (Platt calibration & conformal quantile calibration), 15% Held-Out Test (final benchmark).
- **Anti-Leakage Guarantee**: Temporal barrier strictly enforced; zero future valid-time observations enter feature extraction.
- **Geographic Envelope**: Evaluated across 13 international WMO stations and regional South Asian monsoon coordinates.

## 2. Discrimination & Calibration Metrics
- **ROC-AUC Score**: 0.884
- **Calibrated Brier Loss**: 0.098 (uncalibrated baseline: 0.204)
- **Expected Calibration Error (ECE)**: 0.031
- **Optimal Decision Threshold (τ)**: 0.280

## 3. Conformal Coverage & Uncertainty Quality
- **Target Coverage**: 90.0% (1 - alpha = 0.90)
- **Empirical Held-Out Coverage**: 91.4%
- **Dynamic Interval Bounds**: [2.80°C, 8.50°C] margin scaled by live ensemble spread $\sigma_{	ext{ens}}$ and horizon dilation.

## 4. OOD & Novelty Robustness
- **Methodology**: Multivariate Mahalanobis statistical distance evaluated over [temperature, ensemble_spread, temp_variance, lead_hours].
- **Threshold Policy**: Novelty >= 3.20 automatically shifts trust state from SUPPORTED to DEGRADED.
- **False Alarm Rate on In-Distribution Data**: 2.3%

## 5. Operational Quality & Latency
- **Average Inference Latency**: 84.2 ms
- **Availability / Success Rate**: 99.8%
- **Abstention Policy**: Immediate non-zero refusal on non-finite coordinates or malformed payloads without converting nulls to zero.
