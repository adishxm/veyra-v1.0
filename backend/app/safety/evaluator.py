import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SafetyDecision:
    trust_state: str
    abstain: bool
    reason_codes: list[str] = field(default_factory=list)


# Domain Thresholds
MIN_ENSEMBLE_MEMBERS = 3
RECOMMENDED_MIN_MEMBERS = 5
MAX_REASONABLE_SPREAD = 15.0  # °C standard deviation threshold for temperature
MAX_RELIABLE_LEAD_HOURS = 168.0  # 7 days


def evaluate(
    *, 
    feature_values: dict[str, float], 
    probability: float | None
) -> SafetyDecision:
    reasons: list[str] = []

    # 1. Critical Hard Failures -> ABSTAIN
    if probability is None:
        return SafetyDecision(
            trust_state="ABSTAINED", 
            abstain=True, 
            reason_codes=["MODEL_UNAVAILABLE"]
        )

    if probability < 0.0 or probability > 1.0 or math.isnan(probability):
        return SafetyDecision(
            trust_state="ABSTAINED", 
            abstain=True, 
            reason_codes=["INVALID_PROBABILITY"]
        )

    # Check for NaN / Infinite values in computed features
    for key, value in feature_values.items():
        if value is None or math.isnan(value) or math.isinf(value):
            return SafetyDecision(
                trust_state="ABSTAINED", 
                abstain=True, 
                reason_codes=[f"CORRUPT_FEATURE_{key.upper()}"]
            )

    member_count = feature_values.get("member_count", 0.0)
    if member_count < MIN_ENSEMBLE_MEMBERS:
        return SafetyDecision(
            trust_state="ABSTAINED", 
            abstain=True, 
            reason_codes=["INSUFFICIENT_ENSEMBLE_MEMBERS"]
        )

    # 2. Atmospheric & Data Quality Checks -> DEGRADED or SUPPORTED
    spread = feature_values.get("forecast_spread", 0.0)
    lead_hours = feature_values.get("lead_hours", 0.0)

    if spread > MAX_REASONABLE_SPREAD:
        reasons.append("HIGH_ENSEMBLE_DIVERGENCE")

    if lead_hours > MAX_RELIABLE_LEAD_HOURS:
        reasons.append("EXTENDED_LEAD_HORIZON")

    if member_count < RECOMMENDED_MIN_MEMBERS:
        reasons.append("LOW_MEMBER_SAMPLE_SIZE")

    # If soft warnings exist, mark as DEGRADED but do not force hard abstention
    if reasons:
        return SafetyDecision(
            trust_state="DEGRADED",
            abstain=False,
            reason_codes=reasons
        )

    return SafetyDecision(
        trust_state="SUPPORTED", 
        abstain=False, 
        reason_codes=["VALID_INPUT"]
    )