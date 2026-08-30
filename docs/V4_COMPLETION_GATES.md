# Veyra V4.0 Completion Gates

V4.0 becomes a final independent product only after every gate below is demonstrated in the personal repository and a clean deployment. Mobile is the only intentionally deferred product area; all other gates are required.

| Gate | Evidence required |
|---|---|
| Provider gate | At least two working provider adapters, canonical normalization, provenance, timeout/retry tests, and authorized NCMRWF/NEPS verification where applicable. |
| Data gate | Reproducible raw-to-curated pipeline, immutable manifests, timestamp alignment, QC, and reference-data lineage. |
| Label gate | Versioned bust definition with examples, gray-band policy, and leakage audit. |
| Model gate | Reproducible baseline and advanced model training, versioned artifacts, checksums, registry, and rollback. |
| Calibration gate | Held-out calibration report with Brier/reliability results. |
| Conformal gate | Held-out coverage and width/set-size report with method/version metadata. |
| OOD gate | Novelty score, threshold selection, known/novel evaluation, and safe action policy. |
| API gate | Single, batch, and asynchronous APIs with versioned schemas, idempotency, retries, and structured failures. |
| Account gate | Authentication, authorization, saved locations, alerts, audit events, deletion/export tests. |
| Frontend gate | Functional dashboard for success, loading, error, degraded, abstention, uncertainty, evidence, and map states. |
| Automation gate | Scheduled ingestion and candidate retraining with evaluation and explicit approval before promotion. |
| Distributed-operation gate | Persistent queue/jobs, worker restart recovery, dead-letter handling, and queue observability. |
| Monitoring gate | Service, provider, data, model, calibration, conformal, OOD, queue, and abstention dashboards/alerts. |
| Security gate | Secrets protection, input/rate controls, authorization, artifact verification, dependency scan, backup and restore. |
| Deployment gate | Clean deployment, readiness checks, rollback procedure, and reproducible environment configuration. |
| Documentation gate | README, specifications, contracts, evaluation, operations, limitations, references, and release notes match the code. |
| Mobile gate | Explicitly deferred by product decision and clearly labeled outside V4.0 scope. |

A green documentation table is not evidence by itself. Each gate requires executable tests, artifacts, logs, or a reproducible demonstration.
