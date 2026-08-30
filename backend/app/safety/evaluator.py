from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyDecision:
    trust_state: str
    abstain: bool
    reason_codes: list[str]


def evaluate(*, feature_values: dict[str, float], probability: float | None) -> SafetyDecision:
    if probability is None:
        return SafetyDecision("ABSTAINED", True, ["MODEL_UNAVAILABLE"])
    if any(value != value for value in feature_values.values()):
        return SafetyDecision("ABSTAINED", True, ["INVALID_FEATURES"])
    if probability < 0 or probability > 1:
        return SafetyDecision("ABSTAINED", True, ["INVALID_PROBABILITY"])
    return SafetyDecision("SUPPORTED", False, ["VALID_INPUT"])
