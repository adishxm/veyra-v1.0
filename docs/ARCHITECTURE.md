# Veyra V2.0 Architecture

## High-level architecture

```text
Web client
   ↓ HTTPS
API gateway
   ↓
Prediction service ───── Location service
   ↓                         ↓
Feature service ← Provider adapter registry
   ↓                         ↓
Model registry          GEFS / NCMRWF / other providers
   ↓
Calibration + conformal uncertainty
   ↓
OOD and safety decision
   ↓
Explanation and response

Background job system
   ├── forecast ingestion
   ├── historical alignment
   ├── feature generation
   ├── evaluation
   ├── retraining proposal
   └── monitoring aggregation

Storage
   ├── object storage: raw/processed forecasts and artifacts
   ├── relational metadata store: versions, runs, users, jobs
   └── metrics store: service/data/model monitoring
```

## Services

| Service | Responsibility | Must not own |
|---|---|---|
| Location service | Resolve names/coordinates and validate geography. | Model decisions. |
| Provider adapters | Translate each provider into canonical records. | Frontend response semantics. |
| Canonical data service | Validate units, timestamps, membership, and quality. | Training labels. |
| Feature service | Build issue-time-safe features. | Future observations during live inference. |
| Model registry | Load approved, versioned models. | Automatic unvalidated deployment. |
| Calibration service | Apply approved calibration objects. | Label creation. |
| Conformal service | Produce intervals/sets and coverage metadata. | Pretending coverage is guaranteed without evaluation. |
| OOD service | Measure novelty/support. | Replacing domain review. |
| Safety service | Decide risk/trust/abstention. | Fabricating fallback probabilities. |
| Job service | Run queued ingestion/evaluation/retraining jobs. | Direct uncontrolled model promotion. |
| Monitoring service | Collect service/data/model signals. | Editing predictions silently. |

## Data flow rule

Every record must carry provenance: provider, issue time, valid time, location, variable, unit, data version, and processing version.

## Hosting strategy

Begin with a simple web deployment and one worker. Move to a queue-backed distributed setup only when forecast ingestion, retraining, or user traffic requires it. Scheduled deterministic jobs should run as application background jobs or cron jobs rather than launching an AI session for each poll. For always-on workers, use persistent managed hosting within the platform limits first; use a full cloud machine only if Docker, OS-level control, custom runtimes, GPU, or larger resources are genuinely required. [5] [6]
