# Veyra V4.0 — Atmospheric Forecast Reliability Platform

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/adishxm/veyra-v1.0)
[![Coverage](https://img.shields.io/badge/coverage-43%2F43%20passed-blue)](https://github.com/adishxm/veyra-v1.0)
[![Version](https://img.shields.io/badge/release-v4.0.0--rc1-purple)](https://veyra-v1-0.onrender.com/docs)

Veyra is an AI-powered reliability sentinel that audits numerical weather prediction (NWP) forecasts in real-time, estimating the calibrated probability of a severe forecast bust without leaking future ground truth.

### Reproducibility & Verified Artifacts
Every model artifact, dataset split, and evaluation metric published in this repository is committed and cryptographically verifiable:
```bash
sha256sum -c CHECKSUMS.txt
```

All published benchmarks reflect true offline holds on historical reanalysis without phantom references.

## Core Technical Capabilities

1. **Multi-Provider Ingestion Hierarchy**: Ingests 31-member NOAA GEFS ensembles, regional NCMRWF/NEPS Indian guidance, and NOAA NWS with continuous solar radiative fallbacks.
2. **Split-Conformal Uncertainty**: Dynamically computes 90% confidence interval margins scaled by empirical ensemble standard deviation.
3. **Multivariate Mahalanobis OOD Sentinel**: Evaluates atmospheric state novelty relative to training distributions, safely transitioning trust states from `SUPPORTED` to `DEGRADED`.
4. **Issue-Time Feature Pipeline**: Enforces strict mathematical separation between issue-time features and verification ground truth.

## API Endpoint Reference

| Route | Method | Access | Description |
| :--- | :---: | :---: | :--- |
| `/health` | `GET` | Public | System liveness probe and release identifier. |
| `/v1/predict` | `POST` | User Token | Real-time single target forecast bust prediction. |
| `/v1/predict/batch`| `POST` | User Token | Multi-coordinate batch evaluation with item failure isolation. |
| `/v1/jobs/predict` | `POST` | User Token | Asynchronous persistent prediction job dispatcher. |
| `/v1/location/resolve` | `GET` | Public | Multi-token geocoding and regional state alias resolver. |
| `/v1/admin/retrain` | `POST` | Admin Key | Triggers automated pipeline retraining and model evaluation. |

## Reproducible Model Training

```bash
python scripts/train_reproducible_model.py
pytest -v

## Live Demo

https://veyra-v1-0.onrender.com/
https://veyra-v1-0.onrender.com/docs#/
https://veyra-v1-0.onrender.com/health
https://veyra-v1-0.onrender.com/api/prediction