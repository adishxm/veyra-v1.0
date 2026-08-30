# Veyra V2.0 Model and Reliability Contract

## Model input

Live inference receives only information available at forecast issue time. The input contains location, variable, lead time, forecast/ensemble information, issue-time revisions, quality flags, and feature-schema version.

Forbidden live fields include `observed_value`, `reference_value`, `actual_value`, `ground_truth`, `bust_label`, and any later observation.

## Versioned contract

```text
model_version
feature_schema_version
label_policy_version
calibration_version
conformal_version
ood_policy_version
data_version
```

All versions must be written into prediction metadata and monitoring events.

## Output contract

```json
{
  "bust_probability": 0.0,
  "probability_interval": {"lower": 0.0, "upper": 1.0},
  "risk_level": "LOW",
  "trust_state": "SUPPORTED",
  "abstain": false,
  "reason_codes": ["VALID_INPUT"],
  "evidence": [],
  "model_version": "personal-veyra-model-v1",
  "data_version": "provider-data-v1"
}
```

If safety rejects the inference, `bust_probability` must be `null`, risk must be `null`, and the response must contain a reason code.

## Calibration

A calibrator may transform raw model scores into probabilities. It must be fitted only on an approved validation split and versioned with the model.

## Conformal uncertainty

The conformal layer must report the method, target coverage, empirical validation coverage, interval width or prediction-set size, calibration data version, and any conditional-coverage limitations. It must not claim universal coverage without supporting evaluation.

## OOD policy

OOD detection must define the reference training distribution, distance/novelty measure, threshold, threshold version, and action. A novel input should lower trust or trigger abstention according to a tested policy.

## Replacement rule

A new model may be promoted only if its feature schema, label policy, calibration, conformal method, evaluation report, artifact checksum, and rollback target are registered together.
