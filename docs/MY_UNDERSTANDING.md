# My Understanding of Veyra V2.0

## What Veyra is

Veyra estimates whether an already-issued weather forecast may fail unusually badly and communicates the estimate together with uncertainty, trust, evidence, and abstention behavior.

## What Veyra is not

Veyra is not an official forecast provider, warning authority, causal weather-explanation engine, or guarantee of a decision outcome.

## The live path

```text
location → provider → canonical records → issue-time-safe features → model → calibration → conformal uncertainty → OOD → safety → response → UI
```

## Questions I must answer while building

- What does each feature mean?
- What data was available at issue time?
- How was the bust label created?
- What does the probability mean?
- When does the system abstain?
- Which model/data/calibration version produced the response?
- What evidence supports the result?
- What remains scientifically unvalidated?

## Learning record

Add dated notes below as the project grows.

### Date: 

What I learned:

What I implemented:

What I still do not understand:
