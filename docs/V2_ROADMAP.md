# Veyra V2.0 Complete-Product Roadmap

## Rule

Each phase ends with tests, documentation, and a gate. Do not advance because code exists; advance when behavior is reproducible and understood.

## Phase 1 — Independent foundation

Create the repository, product specification, architecture diagram, glossary, Git workflow, virtual environment, and initial `/health` endpoint. Test clean installation and health response.

## Phase 2 — Multi-provider forecast platform

Implement the provider interface and canonical record schema. Build the first public provider adapter, then add an independently verified NCMRWF/NEPS adapter only when authorized access and stable data formats are available. Compare providers through provenance-aware records rather than provider-specific frontend logic.

**Gate:** fixture tests pass for each adapter, provider failures abstain, units/timestamps are validated, and the provider source is recorded.

## Phase 3 — Historical data and label engine

Build immutable raw-data storage, alignment, deduplication, quality control, reference matching, versioned bust labels, and dataset manifests. Separate future reference observations from live features.

**Gate:** a sample forecast/reference pair can be traced from raw data to error and label with no leakage.

## Phase 4 — Feature and model platform

Implement versioned feature schemas, ensemble/revision/regime/analog features, baseline model, gradient-boosted model, model registry, artifact manifest, and reproducible training runs.

**Gate:** training can be repeated from a manifest, model schema mismatches are rejected, and the baseline is compared with the candidate model.

## Phase 5 — Calibration and conformal uncertainty

Add probability calibration using a held-out validation design. Add split conformal or another justified method to produce prediction intervals/sets. Measure empirical coverage, interval width, conditional behavior, and failure cases. The conformal output is uncertainty information, not proof that the forecast is correct.

**Gate:** calibration and conformal reports are reproducible, coverage is measured on held-out data, and output metadata includes method/version/coverage.

## Phase 6 — OOD and safety intelligence

Implement a documented novelty detector using a training-distribution reference, distance/score, threshold, and policy. Combine OOD, data quality, artifact validity, calibration state, and provider status in the safety evaluator.

**Gate:** known-supported inputs produce results; deliberately novel, malformed, unavailable, and low-quality inputs abstain or receive the documented degraded state.

## Phase 7 — Prediction API and batch jobs

Implement single prediction, batch prediction, asynchronous job status, idempotency, retries, rate limits, structured errors, and trace IDs. Keep the prediction path deterministic and auditable.

**Gate:** mixed batches isolate failures, duplicate jobs do not duplicate outputs, and API contracts are versioned.

## Phase 8 — Accounts and user features

Add authentication, authorization, saved locations, user preferences, alert subscriptions, audit events, and data deletion/export behavior. Keep accounts optional until anonymous core predictions are stable.

**Gate:** one user cannot access another user’s locations, preferences, or alerts; unauthenticated access is limited to intended public features.

## Phase 9 — Frontend and complex maps

Build location search, forecast horizon visualization, ensemble spread view, bust probability, conformal uncertainty, risk, trust, evidence, model/data version, and abstention messaging. Add map layers only after the single-location view is clear.

**Gate:** every API state has a correct UI state, `null` probability is never rendered as zero, and map overlays identify variable, timestamp, units, and provenance.

## Phase 10 — Automated ingestion and retraining

Create scheduled ingestion, data validation, alignment, feature generation, candidate retraining, evaluation, approval, promotion, rollback, and notification workflows. Use deterministic scheduled jobs for deterministic work. Keep human approval between candidate creation and production promotion.

**Gate:** a simulated new-data cycle creates a candidate report without changing production; only an approved candidate can be promoted; rollback works.

## Phase 11 — Distributed serving and job execution

Introduce a queue, worker, persistent job store, idempotency keys, retry/backoff, dead-letter handling, result storage, and horizontal API/worker separation. Keep the architecture simple until load or job duration requires distribution.

**Gate:** worker restart does not lose jobs, retries are bounded, duplicate jobs are safe, and job status is observable.

## Phase 12 — Production monitoring and drift

Add metrics/logs/traces for API, providers, data freshness, feature drift, prediction drift, calibration drift, OOD rate, abstention rate, queue health, retraining jobs, model versions, and data versions. Define alert thresholds and response playbooks.

**Gate:** simulated outages and drift produce alerts, dashboards show the active versions, and no sensitive data appears in logs.

## Phase 13 — Security, privacy, and reliability hardening

Add input limits, authentication/authorization tests, secret management, dependency scanning, signed/hashed artifacts, webhook verification where applicable, backups, restore tests, disaster recovery notes, and threat-model review.

**Gate:** security checklist passes, secrets are absent from Git history/current files, backups restore, and failure modes are documented.

## Phase 14 — Mobile and cross-platform clients

Only after the web product and API are stable, build mobile clients using the same versioned API. Implement offline-safe UI states, notification permission handling, account security, and mobile-specific observability.

**Gate:** mobile clients do not duplicate model logic and correctly represent uncertainty and abstention.

## Phase 15 — V2.0 release

Freeze features, run clean-install and clean-deploy tests, publish model/data manifests, complete evaluation and limitations reports, back up artifacts, tag the release, rehearse the demo, and publish a change log.

**Gate:** an independent user can reproduce the deployed product and understand both its predictions and its limitations.

## V2.0 definition of complete

V2.0 is complete when all fifteen phases have passed their gates and the product supports the documented requirements: multi-provider ingestion including authorized NCMRWF/NEPS access, automated retraining with approval, conformal uncertainty, OOD safety, accounts, distributed jobs, complex map views, mobile access, and production-scale monitoring.
