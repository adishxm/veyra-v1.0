# Veyra V2.0 Product Specification

## Problem

Forecasts can be useful on average while still failing badly in individual situations. Veyra estimates the probability that a specified forecast will become an unusually large error and communicates how much the system trusts that estimate.

## Primary user

The primary user is a weather-aware decision maker who needs an additional reliability signal before acting on a medium-range forecast. Example users include researchers, planners, disaster-management teams, agricultural users, and energy/transport analysts. V2.0 is decision support; it does not issue official warnings.

## Core user journey

```text
choose location and variable
        ↓
select forecast horizon
        ↓
Veyra gathers one or more forecasts
        ↓
Veyra computes reliability features
        ↓
model estimates bust probability
        ↓
calibration and conformal layer quantify uncertainty
        ↓
OOD/safety layer decides whether to show or withhold the result
        ↓
user sees risk, trust, evidence, and suggested review action
```

## Functional requirements

| ID | Requirement |
|---|---|
| FR-01 | Accept a named location and validated coordinates. |
| FR-02 | Retrieve forecasts through provider adapters. |
| FR-03 | Normalize provider responses into canonical records. |
| FR-04 | Compute issue-time-safe features. |
| FR-05 | Estimate forecast-bust probability using a versioned model. |
| FR-06 | Calibrate probability and expose calibration metadata. |
| FR-07 | Produce conformal intervals/sets where the evaluated method supports them. |
| FR-08 | Detect unsupported or novel inputs and abstain. |
| FR-09 | Explain supporting evidence without causal overclaiming. |
| FR-10 | Support batch and asynchronous processing. |
| FR-11 | Refresh data and propose retraining through an approval-gated workflow. |
| FR-12 | Present results through a responsive web dashboard. |
| FR-13 | Monitor data, model, provider, and service health. |

## Non-functional requirements

The system must be reproducible, versioned, observable, secure by default, testable without a live provider, resilient to provider failure, and explicit about scientific limitations.

## Safety requirements

Veyra must abstain when the location is invalid, the provider is unavailable, required data is missing or invalid, the feature schema does not match the model, artifacts cannot be verified, the input is out of distribution, or inference/calibration fails.

## V2.0 non-goals

Veyra will not replace official forecasts, claim causal weather explanations, guarantee decisions, or silently retrain and deploy models without validation and approval.
