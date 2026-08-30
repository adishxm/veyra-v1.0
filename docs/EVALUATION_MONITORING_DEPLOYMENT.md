# Veyra V2.0 Evaluation, Monitoring, and Deployment Plan

## Evaluation

Every model version must be evaluated with time-safe splits and reported by location, variable, lead time, and regime where data permits. Required metrics include PR-AUC, precision, recall, F1, Brier score, reliability/calibration results, abstention rate, and coverage/width for conformal intervals.

## Monitoring

Track service uptime, latency, provider success/failure, data freshness, missingness, feature drift, prediction distribution, calibration drift, OOD rate, abstention rate, active model version, active data version, and job failures.

## Deployment environments

```text
local → test/staging → production
```

Each environment has separate configuration and secrets. Production model promotion is versioned and reversible.

## Deployment checklist

- dependencies are pinned or bounded intentionally;
- secrets are environment variables;
- artifacts are verified by checksum;
- database/storage migrations are documented;
- CORS is restricted;
- HTTPS is enabled;
- health and readiness checks exist;
- logs contain no secrets;
- rollback target is known;
- background jobs have retries and dead-letter handling;
- monitoring dashboards and alerts are configured.

## Security baseline

Validate all external inputs, limit request size/rate, authenticate account endpoints, authorize saved locations and alerts, protect job triggers, verify webhook signatures when webhooks exist, and avoid exposing internal tracebacks or private data.
