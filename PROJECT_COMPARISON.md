# Veyra V4.0 Project Comparison & Completed Upgrade Plan

## Product Purpose & Motto
> **Know when forecasts may fail.**

Veyra is an atmospheric forecast-reliability sentinel and decision-support layer for operational numerical weather prediction (NWP) models. It evaluates whether an already-issued forecast may fail unusually badly, estimates bust risk, quantifies dynamic conformal uncertainty, detects out-of-distribution atmospheric states, explains evidence, and safely abstains when evidence is insufficient.

## Layer Completion Matrix
- **User Layer**: Complete 3-column NOAA workspace with Leaflet map, Chart.js multi-horizon envelope, and preferences.
- **API Layer**: 11 production REST routes across prediction, batches, async jobs, logs, actuals, and retraining.
- **Provider Layer**: Multi-provider failover hierarchy (Open-Meteo -> NCMRWF/NEPS -> NOAA NWS -> Solar Physics).
- **Data Layer**: Issue-time feature extraction with strict anti-leakage temporal barriers and empirical q95 bust labels.
- **ML Layer**: Platt-calibrated gradient boosting, split-conformal 90% dynamic coverage, and Mahalanobis OOD sentinel.
- **Safety Layer**: Complete trust-state machine (SUPPORTED / DEGRADED / ABSTAIN) with non-zero refusal.
- **Operations Layer**: In-process persistent worker queue, automated database backups, and live Prometheus telemetry.
- **Documentation Layer**: Complete technical documentation suite (Model Card, Data Card, Evaluation Report, Label Policy).
- **Mobile Layer**: Responsive web layout active; native mobile app intentionally deferred.

## Test Matrix Verification
- **Total Test Cases**: 43 / 43 Passing (100% Green)
- **Active Model Checksum**: adaec18c8352a1d7 (veyra-bust-2.1.0)
- **Live Platform Identity**: veyra-v4-platform (v4.0.0-rc1)
