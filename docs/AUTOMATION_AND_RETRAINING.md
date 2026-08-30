# Veyra V2.0 Automation and Retraining Policy

## Principle

Automation may collect data, validate it, create candidate datasets, evaluate candidates, and propose a model. It must not silently deploy a model that has not passed validation and human approval.

## Scheduled workflow

```text
scheduled trigger
        ↓
forecast/reference ingestion
        ↓
data-quality checks
        ↓
alignment and label generation
        ↓
feature generation
        ↓
candidate training
        ↓
evaluation and calibration
        ↓
conformal/OOD validation
        ↓
approval gate
        ↓
registry promotion or rejection
        ↓
monitoring and rollback readiness
```

## Job types

| Job | Frequency | Output | Approval required |
|---|---|---|---|
| Provider ingestion | Scheduled/near-real-time | Raw and canonical data | No, but quality gates apply. |
| Historical alignment | Scheduled | Curated forecast/reference data | No, but failed jobs must alert. |
| Evaluation | After new data/model | Metrics report | No for report generation. |
| Retraining proposal | Periodic | Candidate artifact and report | Yes. |
| Model promotion | Manual or approved workflow | Active registry pointer | Yes. |
| Drift monitoring | Continuous/periodic | Metrics and alerts | No for alerts; yes for model changes. |

## Promotion gate

A candidate cannot be promoted unless it has:

- reproducible training run;
- valid artifact checksum;
- schema compatibility;
- no leakage audit failure;
- acceptable performance against the current model;
- calibration report;
- conformal coverage report where applicable;
- OOD policy evaluation;
- rollback target;
- documented approval.

## Hosting decision

Use deterministic application jobs or cron for scheduled ingestion and retraining. Do not launch a full AI session for each periodic data poll. Use a persistent worker/queue only when jobs need asynchronous execution, retries, or multiple independent tasks. Prefer managed web hosting for the first deployment; use a full cloud machine only when custom runtimes, Docker, OS control, GPU, or larger resources are genuinely necessary. [5] [6]
