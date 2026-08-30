# Veyra V2.0 User Stories and Test Strategy

## User stories

| ID | Story | Acceptance |
|---|---|---|
| US-01 | As a user, I enter a location and receive a reliability assessment. | Valid location produces a structured result or safe abstention. |
| US-02 | As a user, I want evidence for elevated risk. | Evidence is tied to available features and avoids causal claims. |
| US-03 | As a user, I want to know whether Veyra trusts its own result. | Trust state and reason are visible. |
| US-04 | As a user, I want to know when Veyra cannot assess risk. | Probability is null and abstention reason is shown. |
| US-05 | As an owner, I want model updates to be reviewable. | Candidate models require evaluation and approval. |
| US-06 | As an operator, I want failures and drift to be visible. | Dashboards and alerts expose service/data/model state. |

## Test pyramid

```text
unit tests
  ↓
contract/schema tests
  ↓
provider fixture tests
  ↓
model/evaluation tests
  ↓
API integration tests
  ↓
frontend tests
  ↓
end-to-end tests
  ↓
security/restore/chaos tests
```

## Mandatory negative tests

Invalid location, missing required fields, duplicate timestamps, invalid units, provider timeout, incomplete data, future-reference leakage, missing model, mismatched feature schema, model exception, OOD input, unauthorized account access, duplicate job, worker restart, notification failure, and stale data.

## Phase rule

Every new capability must add at least one success test, one failure test, and one documentation update.
