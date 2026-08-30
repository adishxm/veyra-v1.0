from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineResult:
    probability: float
    model_version: str


class BaselineReliabilityScorer:
    """Transparent development baseline; not the final trained Veyra model."""

    model_version = "personal-veyra-transparent-baseline-v1"

    def predict_probability(self, features: dict[str, float]) -> BaselineResult:
        spread = features["forecast_spread"]
        lead = features["lead_hours"]
        # Monotonic development baseline: uncertainty rises with spread and lead.
        raw = 0.10 + min(spread / 20.0, 0.60) + min(lead / 240.0, 0.20)
        probability = max(0.0, min(raw, 0.95))
        return BaselineResult(probability=probability, model_version=self.model_version)
