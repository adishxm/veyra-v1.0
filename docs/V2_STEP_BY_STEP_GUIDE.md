# Veyra V2.0 — Step-by-Step Full-Product Guide

## Working rule

Every phase ends with: implementation, documentation, focused tests, failure tests, and a written definition of done. Do not build all advanced capabilities at once. Each phase must produce a usable increment.

## Phase 1 — Independent foundation

1. Create the personal GitHub repository.
2. Add `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/MY_UNDERSTANDING.md`, `docs/DECISIONS.md`, and `docs/REFERENCES.md`.
3. Create the Python environment and minimal FastAPI health endpoint.
4. Add a basic CI workflow that installs dependencies and runs tests.
5. Make the first personal commit.

**Test:** clean install, `pytest -q`, and `curl /health`.

## Phase 2 — Forecast-provider adapter platform

1. Define `ForecastProvider` as an interface.
2. Implement a fixture-backed provider for tests.
3. Implement one public provider adapter.
4. Normalize all providers into your canonical record.
5. Add provider provenance and data-version fields.
6. Add timeout, retry, rate-limit, and provider-error handling.
7. Add the NCMRWF/NEPS adapter only after authorized access, format verification, and terms review.
8. Compare providers on the same canonical schema.

**Test:** each provider passes fixture tests; provider failure produces a controlled unavailable state; units and timestamps are validated.

## Phase 3 — Historical data and label pipeline

1. Store raw forecast files immutably.
2. Store later reference/observation files separately.
3. Implement timestamp and location alignment.
4. Remove duplicates and flag missing records.
5. Calculate forecast error and absolute error.
6. Implement a versioned bust-label policy.
7. Produce a dataset manifest containing source, period, location, variable, version, and hash.
8. Create a leakage audit that proves future reference values cannot enter live features.

**Test:** a small known forecast/reference fixture produces the expected error and label.

## Phase 4 — Feature engineering

1. Build basic temporal and location features.
2. Add ensemble mean, spread, range, and quantiles.
3. Add forecast revision features across issue cycles.
4. Add regime/season indicators.
5. Add analog similarity only after a valid historical index exists.
6. Add multi-provider disagreement when at least two providers are available.
7. Preserve missingness explicitly.
8. Version the feature schema and write feature metadata.

**Test:** deterministic feature output, exact feature order, no future fields, and expected handling of incomplete ensembles.

## Phase 5 — Baseline and advanced model platform

1. Train a simple baseline model.
2. Define train/validation/test splits by time.
3. Compare a stronger model against the baseline.
4. Save the classifier, metadata, feature schema, label version, and training manifest together.
5. Build a model registry with candidate, staging, active, and rollback states.
6. Implement schema checks before inference.
7. Store checksums for all artifacts.

**Test:** save/load, schema mismatch rejection, reproducible inference, and rollback to the previous model.

## Phase 6 — Calibration

1. Generate raw probabilities.
2. Fit calibration only on an approved validation split.
3. Measure Brier score and reliability.
4. Version the calibrator with the classifier.
5. Store calibration data period and method in metadata.
6. Reject or flag a model whose calibration is materially worse than the active model.

**Test:** calibration report exists and probability outputs remain in `[0, 1]`.

## Phase 7 — Conformal uncertainty

1. Choose a method appropriate to the target: interval for continuous forecast error or prediction set for classification.
2. Separate training, calibration, and evaluation data.
3. Fit the conformal nonconformity score.
4. Generate intervals/sets with target coverage.
5. Measure empirical coverage and interval width by location, variable, lead, and regime where possible.
6. Record method, target coverage, observed coverage, and version.
7. Expose limitations: marginal coverage is not automatically conditional coverage.
8. Make the safety layer lower trust or abstain when conformal support is invalid.

**Test:** held-out coverage and output-shape tests; deliberately insufficient calibration data must fail safely.

## Phase 8 — OOD and safety intelligence

1. Define the reference training distribution.
2. Choose a novelty score such as standardized distance, density score, or ensemble/feature support measure.
3. Set thresholds on validation data.
4. Test known and synthetic-novel inputs.
5. Combine OOD, missing data, provider status, artifact status, calibration, and conformal status.
6. Produce `SUPPORTED`, `DEGRADED`, or `ABSTAINED` states with reason codes.

**Test:** novel inputs do not receive high-confidence predictions without evidence.

## Phase 9 — API, batch, and asynchronous jobs

1. Implement versioned single-prediction request/response schemas.
2. Add batch prediction with isolated failures.
3. Add trace IDs and idempotency keys.
4. Add a persistent job record for long-running work.
5. Add bounded retries and exponential backoff.
6. Add a status endpoint for asynchronous jobs.
7. Add rate limits and request-size limits.

**Test:** duplicate job submission is safe, worker failure is recoverable, and one failed location does not erase valid batch results.

## Phase 10 — Accounts, saved locations, and alerts

1. Add authentication only after anonymous core prediction works.
2. Define user, saved location, preference, alert, and audit schemas.
3. Enforce authorization on every user-owned resource.
4. Add saved locations and alert thresholds.
5. Add notification delivery with retry and opt-out.
6. Add account deletion/export behavior.
7. Never expose another user’s locations or alerts.

**Test:** authentication, authorization, deletion, duplicate alerts, and notification failure isolation.

## Phase 11 — Frontend and complex maps

1. Build location search and forecast selection.
2. Add loading, success, error, degraded, and abstention states.
3. Display probability, risk, trust, evidence, conformal uncertainty, horizon, and versions.
4. Add ensemble spread and forecast revision visualizations.
5. Add map layers only after the single-location view is correct.
6. Label every map layer with variable, units, valid time, source, and version.
7. Never render `null` probability as zero.

**Test:** browser tests for every API state and visual checks for map legends/units.

## Phase 12 — Automated ingestion and retraining

1. Schedule deterministic forecast ingestion.
2. Schedule reference-data ingestion when available.
3. Validate freshness, completeness, schema, and provenance.
4. Build a candidate dataset.
5. Train a candidate model in an isolated job.
6. Run evaluation, calibration, conformal, and OOD reports.
7. Require human approval before promotion.
8. Register the candidate and retain rollback metadata.
9. Notify on failure or approval requirement.

**Test:** a simulated retraining run creates a candidate without changing production; promotion changes production only after approval; rollback restores the previous version.

## Phase 13 — Distributed serving and workers

1. Keep API requests stateless.
2. Move long-running work into workers.
3. Add a queue and persistent job store.
4. Add retry/backoff and dead-letter handling.
5. Make jobs idempotent.
6. Add worker health and queue-depth metrics.
7. Scale API and workers independently only when measured load requires it.
8. Use managed hosting first; use a full cloud machine only for hard requirements such as Docker, custom system packages, GPU, or resources beyond the managed limit. [5] [6]

**Test:** restart a worker during a job and confirm recovery without duplicated final output.

## Phase 14 — Production monitoring and drift

1. Add structured logs with request/job/model/data IDs.
2. Track API uptime, latency, errors, provider health, and queue health.
3. Track freshness, missingness, feature drift, prediction drift, OOD rate, and abstention rate.
4. Track calibration and conformal coverage after reference outcomes become available.
5. Add model/data version dashboards.
6. Define alert thresholds and response playbooks.
7. Test alerting with simulated failures and drift.

**Test:** every simulated failure produces a visible, actionable signal without leaking secrets.

## Phase 15 — Security, backup, and resilience

1. Threat-model public endpoints, accounts, jobs, webhooks, and artifacts.
2. Validate and limit external input.
3. Protect secrets through environment/configuration management.
4. Verify webhook signatures if a provider supports webhooks.
5. Scan dependencies and container images where used.
6. Back up metadata, user data, model registry, and configuration.
7. Perform a restore drill.
8. Document incident response and rollback.

**Test:** unauthorized access, invalid payloads, secret scanning, backup restore, and artifact tampering tests pass.

## Phase 16 — Mobile clients

1. Reuse the versioned API; do not duplicate model logic.
2. Build mobile location input and result screens.
3. Handle network loss, stale results, notifications, permissions, and abstention.
4. Add mobile crash/error monitoring.
5. Test against API version compatibility.

**Test:** mobile clients correctly represent valid, degraded, error, and abstained responses.

## Phase 17 — V2.0 release

1. Freeze features.
2. Re-run clean installation and deployment.
3. Verify provider/data/model manifests.
4. Run full unit, integration, end-to-end, security, and restore tests.
5. Publish evaluation, calibration, conformal, OOD, and limitations reports.
6. Rehearse the demo.
7. Tag the release and publish a change log.

**Final test:** an independent user can reproduce the product and understand both its predictions and its limitations.
