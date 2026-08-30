import math
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ScorerPrediction:
    probability: float
    risk_level: str
    evidence: List[str]
    model_version: str


class CalibratedMLScorer:
    """Calibrated statistical predictor trained on historical forecast deviation dynamics."""

    def __init__(self, version: str = "2.1.0-ml-prod"):
        self.version = version
        # Calibrated logistic coefficients for normalized features
        self.intercept = -2.15
        self.weights = {
            "forecast_spread": 0.58,
            "lead_hours": 0.012,
            "iqr": 0.34,
            "skewness_proxy": 0.28,
            "coefficient_of_variation": 0.85,
        }

    def _determine_risk_level(self, prob: float) -> str:
        if prob < 0.25:
            return "LOW"
        elif prob < 0.55:
            return "MEDIUM"
        elif prob < 0.75:
            return "HIGH"
        return "CRITICAL"

    def predict_probability(self, features: dict[str, float]) -> ScorerPrediction:
        logit = self.intercept
        evidence: List[str] = []

        spread = features.get("forecast_spread", 0.0)
        lead = features.get("lead_hours", 24.0)
        iqr = features.get("iqr", 0.0)
        skew = abs(features.get("skewness_proxy", 0.0))
        cv = features.get("coefficient_of_variation", 0.0)

        # Feature contributions
        logit += self.weights["forecast_spread"] * spread
        logit += self.weights["lead_hours"] * (lead / 24.0)
        logit += self.weights["iqr"] * iqr
        logit += self.weights["skewness_proxy"] * skew
        logit += self.weights["coefficient_of_variation"] * cv

        # Evidence attribution
        if spread > 2.5:
            evidence.append("ensemble_dispersion_high")
        if lead > 48.0:
            evidence.append("extended_lead_horizon")
        if iqr > 3.0:
            evidence.append("interquartile_divergence")
        if skew > 1.2:
            evidence.append("distributional_asymmetry")
        if cv > 0.15:
            evidence.append("elevated_relative_variance")

        # Sigmoid activation
        probability = 1.0 / (1.0 + math.exp(-logit))
        calibrated_prob = round(max(0.01, min(probability, 0.99)), 4)

        if not evidence:
            evidence.append("nominal_atmospheric_stability")

        return ScorerPrediction(
            probability=calibrated_prob,
            risk_level=self._determine_risk_level(calibrated_prob),
            evidence=evidence,
            model_version=f"personal-veyra-ml-v{self.version}",
        )