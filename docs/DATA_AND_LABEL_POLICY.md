# Veyra V2.0 Data and Label Policy

## Data layers

```text
raw provider files
        ↓
validated canonical records
        ↓
aligned forecast/reference dataset
        ↓
issue-time-safe features
        ↓
labels and evaluation outcomes
```

Raw files are immutable. Processed files are reproducible from raw files and code versions. Training labels may use later reference observations; live features may not.

## Provider strategy

V2.0 uses an adapter interface. Start with one reproducible public provider and add others only through the same canonical schema.

NCMRWF/NEPS integration is an optional operational adapter that requires an authorized, stable access path and documented terms. Public material describes NEPS as a 10-day ensemble system with 23 members, but operational access and archive availability must be verified before using it for claims or training. [7]

## Bust label

The label policy must be versioned and specify threshold formula, conditioning dimensions, reference dataset, missing-reference behavior, and gray-band handling. A percentile threshold can be useful for a prototype, but it is not a universal definition of failure.

## Data quality

Reject or flag impossible physical values, duplicate timestamps, missing member identity, incomplete required records, inconsistent units, stale data, timestamp misalignment, and provider-version changes.

## Privacy and licensing

Store only the location information required for the product. Record API/data licenses and attribution in `docs/REFERENCES.md`. Do not publish restricted datasets or credentials.
