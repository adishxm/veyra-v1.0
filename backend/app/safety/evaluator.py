import math
from dataclasses import dataclass, field
from backend.app.safety.conformal import conformal_engine


@dataclass(frozen=True)
class SafetyDecision:
    trust_state: str
    abstain: bool
    reason_codes: list[str] = field(default_factory=list)
    novelty_score: float = 0.0


MIN_ENSEMBLE_MEMBERS = 3
RECOMMENDED_MIN_MEMBERS = 5
MAX_REASONABLE_SPREAD = 15.0
MAX_RELIABLE_LEAD_HOURS = 168.0


def evaluate(
    *,
    feature_values: dict[str, float],
    probability: float | None
) -> SafetyDecision:
    reasons: list[str] = []

    # 1. Critical Hard Failures
    if probability is None:
        return SafetyDecision(
            trust_state="ABSTAINED", abstain=True, reason_codes=["MODEL_UNAVAILABLE"]
        )

    if probability < 0.0 or probability > 1.0 or math.isnan(probability):
        return SafetyDecision(
            trust_state="ABSTAINED", abstain=True, reason_codes=["INVALID_PROBABILITY"]
        )

    for key, value in feature_values.items():
        if value is None or math.isnan(value) or math.isinf(value):
            return SafetyDecision(
                trust_state="ABSTAINED",
                abstain=True,
                reason_codes=[f"CORRUPT_FEATURE_{key.upper()}"],
            )

    member_count = feature_values.get("member_count", 0.0)
    if member_count < MIN_ENSEMBLE_MEMBERS:
        return SafetyDecision(
            trust_state="ABSTAINED",
            abstain=True,
            reason_codes=["INSUFFICIENT_ENSEMBLE_MEMBERS"],
        )

    # 2. Conformal OOD Novelty Check
    ood_result = conformal_engine.evaluate_ood(feature_values)
    if ood_result.is_ood:
        return SafetyDecision(
            trust_state="ABSTAINED",
            abstain=True,
            reason_codes=["OUT_OF_DISTRIBUTION_NOVELTY"] + ood_result.ood_reasons,
            novelty_score=ood_result.novelty_score,
        )

    # 3. Soft Atmospheric Quality Warnings
    spread = feature_values.get("forecast_spread", 0.0)
    lead_hours = feature_values.get("lead_hours", 0.0)

    if spread > MAX_REASONABLE_SPREAD:
        reasons.append("HIGH_ENSEMBLE_DIVERGENCE")

    if lead_hours > MAX_RELIABLE_LEAD_HOURS:
        reasons.append("EXTENDED_LEAD_HORIZON")

    if member_count < RECOMMENDED_MIN_MEMBERS:
        reasons.append("LOW_MEMBER_SAMPLE_SIZE")

    if reasons:
        return SafetyDecision(
            trust_state="DEGRADED",
            abstain=False,
            reason_codes=reasons,
            novelty_score=ood_result.novelty_score,
        )

    return SafetyDecision(
        trust_state="SUPPORTED",
        abstain=False,
        reason_codes=["VALID_INPUT"],
        novelty_score=ood_result.novelty_score,
    )