# Veyra V4.0 — Atmospheric Forecast Reliability Platform

[![CI Tests](https://github.com/adishxm/veyra-v1.0/actions/workflows/test.yml/badge.svg)](https://github.com/adishxm/veyra-v1.0/actions/workflows/test.yml)
[![Tests](https://img.shields.io/badge/tests-59%2F59%20passing-brightgreen)](https://github.com/adishxm/veyra-v1.0/actions/workflows/test.yml)
[![Keepalive](https://github.com/adishxm/veyra-v1.0/actions/workflows/keepalive.yml/badge.svg)](https://github.com/adishxm/veyra-v1.0/actions/workflows/keepalive.yml)
[![Version](https://img.shields.io/badge/release-v4.0.0--rc1-purple)](https://veyra-v1-0.onrender.com/docs)

Veyra is an AI-powered atmospheric reliability platform that audits numerical weather prediction (NWP) ensemble forecasts in real-time, estimating the calibrated probability of a severe forecast bust without leaking future ground truth.

---

### Reproducibility & Cryptographically Verified Artifacts

Every model binary, training split, and evaluation report published in this repository is committed and cryptographically verifiable on a fresh clone:

```bash
sha256sum -c CHECKSUMS.txt
```

All published benchmarks reflect true empirical offline holds on historical reanalysis without phantom references:
- **Model Artifact:** `backend/app/ml/artifacts/veyra_model_v2_1_0.joblib`
- **Training & Verification Dataset:** `data/processed/real_training_data.parquet` (4,460 aligned synoptic verification samples across 8 Indian domains)
- **Evaluation Report:** `experiments/eval_chronological_holdout_2024_2025.json`

---

### Key Architectural Strengths

1. **Strict Zero-Future-Leakage Pipeline:**
   - Chronological split: 60% Train, 20% Calibration, 20% Holdout Test.
   - Conditioned $q_{95}$ absolute error bust label fitted strictly on the chronological training split.
   - Features restricted to issue-time information: ensemble spread, variance, atmospheric regime bias, novelty score, and lead hours.

2. **Calibrated ML Engine:**
   - Champion architecture: `HistGradientBoostingClassifier` with monotonic risk constraints (`monotonic_cst=[1, 1, 0, 1, 1]`) ensuring physical risk growth with forecast horizon and ensemble spread.
   - Platt Sigmoid Calibration via `CalibratedClassifierCV` on dedicated holdout calibration data.
   - **Measured Holdout Performance:** PR-AUC **0.4218** vs. spread-only baseline **0.2814** (**+49.89%** empirical gain); Brier score **0.0462**.

3. **Honest Out-of-Domain (OOD) Safety Sentinel:**
   - Geodesic and Mahalanobis novelty distance probes out-of-support domains.
   - Automatic abstention (`abstain: true`, `bust_probability: null`, `risk_level: "ABSTAIN"`) on polar domains ($|\text{lat}| \ge 70^\circ$).
   - Explanatory SHAP attributions and synoptic analog searches are suppressed on abstained domains to avoid false confidence.

4. **Production Defense Hardening:**
   - Sliding-window rate limiting middleware (120 req/min) with automated test-client whitelisting.
   - HTML sanitization neutralizing XSS reflection in location parameters.
   - Strict `404 Not Found` rejection on unregistered replay fixtures (`REPLAY_CASE_NOT_FOUND`).
   - 100% Pydantic `response_model=` typed across all API routes generating complete OpenAPI documentation.

---

### API Endpoint Reference

| Route | Method | Access | Description |
| :--- | :---: | :---: | :--- |
| `/health` | `GET` | Public | System liveness probe, version, and dynamic ML engine status (`ml_engine_error`). |
| `/v1/metadata` | `GET` | Public | Complete platform metadata, label policy, and supported variables. |
| `/v1/data-provenance` | `GET` | Public | Upstream NWP backbone and ERA5 verification references. |
| `/v1/models` | `GET` | Public | Champion model registry with checksums and pre-registered benchmarks. |
| `/v1/metrics` | `GET` | Public | Empirical chronological holdout metrics (`MEASURED` status). |
| `/v1/forecasts` | `GET` | Public | Catalog of deterministic historical replay scenarios. |
| `/v1/predict` | `POST` | User Token | Real-time single target calibrated forecast bust prediction. |
| `/v1/predict/batch` | `POST` | User Token | Multi-coordinate batch evaluation with isolated item failure handling. |
| `/v1/risk-trajectory`| `GET` | User Token | Multi-horizon risk ladder across 24h to 240h lead times. |
| `/v1/risk-map` | `GET` | Public | GeoJSON spatial bust risk distribution across Indian synoptic sectors. |
| `/v1/explanation` | `GET` | Public | Feature attributions and dominant risk drivers (suppressed on abstained points). |
| `/v1/analogs` | `GET` | Public | Synoptic historical atmospheric analog search (suppressed on abstained points). |
| `/v1/export` | `GET` | Public | Filterable audit logs in JSON, CSV, or GeoJSON formats. |
| `/v1/location/resolve`| `GET` | Public | Multi-token geocoding and regional state alias resolver. |
| `/v1/jobs/predict` | `POST` | User Token | Asynchronous persistent prediction job dispatcher. |
| `/v1/jobs/{job_id}` | `GET` | User Token | Status and result retrieval for asynchronous jobs. |
| `/v1/logs` | `GET` | Admin Key | Historical operational prediction telemetry stream. |
| `/v1/admin/retrain` | `POST` | Admin Key | Administrative model retraining and conformal calibration trigger. |
| `/v1/actuals` | `POST` | Admin Key | Ground truth observation ingestion into durable SQLite telemetry. |
| `/metrics` | `GET` | Public | Prometheus-compatible operational scraping metrics. |
| `/v1/historical-bust-timeseries` | `GET` | Public | Multi-cycle initialization dispersion timeline (00Z, 06Z, 12Z, 18Z). |

---

### Local Reproduction & Verification

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run data pipeline and train model
python scripts/build_and_train_real_pipeline.py

# 3. Cryptographically verify committed artifacts
sha256sum -c CHECKSUMS.txt

# 4. Run the full test suite
pytest -v
```

---

### Live Deployment

- **Application Root:** https://veyra-v1-0.onrender.com/
- **Interactive OpenAPI Documentation:** https://veyra-v1-0.onrender.com/docs
- **System Health & Engine Probe:** https://veyra-v1-0.onrender.com/health
- **Evaluation Metrics:** https://veyra-v1-0.onrender.com/v1/metrics