# Veyra V4.0 Release Audit

## Audit date

2026-08-30

## Audit conclusion

The current independent codebase is not yet a verified V4.0 final release. It contains a working early backend vertical slice: health endpoint, prediction endpoint, request validation, canonical ensemble schema, basic issue-time-safe features, transparent baseline scoring, safety evaluation, and three passing tests.

The repository does not currently contain verified implementations for real provider ingestion, NCMRWF/NEPS access, multiple providers, historical data and labels, trained production models, calibration, conformal uncertainty, OOD detection, accounts, frontend, maps, automated retraining, distributed jobs, monitoring, deployment, security hardening, backups, or mobile clients.

## Why this document exists

Release documentation must describe verified behavior, not desired behavior. A V4.0 label may be used for the documentation track, but the product should be called a V4.0 release candidate until the completion gates in `docs/V4_COMPLETION_GATES.md` pass.

## Current verified scope

| Area | Verified evidence |
|---|---|
| FastAPI application | `backend/app/main.py` |
| Health endpoint | `GET /health` |
| Prediction endpoint | `POST /v1/predict` |
| Request/schema validation | `backend/app/weather/schemas.py` |
| Basic feature builder | `backend/app/features/basic.py` |
| Transparent baseline scorer | `backend/app/model/baseline.py` |
| Safety evaluator | `backend/app/safety/evaluator.py` |
| Automated tests | `3 passed` in the current local run |

## Release-integrity rule

The following claims must not appear as completed until implementation, tests, operational evidence, and documentation are present: production-ready, fully supported, complete, operational NCMRWF integration, automated retraining, conformal coverage, OOD performance, distributed serving, production monitoring, and final deployment.

Mobile is intentionally deferred by product decision, but it is not the only unverified area in the current codebase.
