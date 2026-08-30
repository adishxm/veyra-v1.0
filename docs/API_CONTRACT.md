# Veyra V2.0 API Contract

## Public endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check. |
| GET | `/ready` | Readiness including provider/model status. |
| POST | `/v1/predict` | Single-location reliability assessment. |
| POST | `/v1/predict/batch` | Multiple-location assessment with isolated failures. |
| POST | `/v1/jobs` | Create an asynchronous ingestion/evaluation/retraining job. |
| GET | `/v1/jobs/{job_id}` | Read job status. |
| GET | `/v1/models/active` | Read active model/data/calibration versions. |

## Prediction request

```json
{
  "location": "Kolkata",
  "variable": "temperature_2m",
  "lead_hours": 48,
  "issue_time": "2026-08-29T00:00:00Z"
}
```

## Prediction response

```json
{
  "location": "Kolkata",
  "bust_probability": null,
  "probability_interval": null,
  "risk_level": null,
  "trust_state": "ABSTAINED",
  "abstain": true,
  "reason_codes": ["MODEL_UNAVAILABLE"],
  "evidence": [],
  "model_version": null,
  "data_version": null
}
```

All response fields must be documented, versioned, and stable for the frontend. Internal tracebacks must never be returned to clients.
