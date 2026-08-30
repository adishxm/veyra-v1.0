import math
from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineResult:
    probability: float
    risk_level: str
    evidence: list[str]
    model_version: str


class BaselineReliabilityScorer:
    """Transparent calibrated development baseline for forecast reliability scoring."""

    model_version = "personal-veyra-transparent-baseline-v2"

    # Risk Classification Thresholds
    LOW_THRESHOLD = 0.25
    MEDIUM_THRESHOLD = 0.55
    HIGH_THRESHOLD = 0.75

    def _calculate_risk_level(self, probability: float) -> str:
        if probability < self.LOW_THRESHOLD:
            return "LOW"
        elif probability < self.MEDIUM_THRESHOLD:
            return "MEDIUM"
        elif probability < self.HIGH_THRESHOLD:
            return "HIGH"
        return "CRITICAL"

    def predict_probability(self, features: dict[str, float]) -> BaselineResult:
        spread = features.get("forecast_spread", 0.0)
        lead = features.get("lead_hours", 24.0)
        iqr = features.get("iqr", spread * 1.349)
        skew_proxy = abs(features.get("skewness_proxy", 0.0))

        evidence: list[str] = []

        # 1. Spread contribution via logistic transition
        spread_term = 0.50 / (1.0 + math.exp(-0.6 * (spread - 3.0)))
        if spread > 2.5:
            evidence.append("ensemble_spread")

        # 2. Lead time uncertainty growth
        lead_term = 0.25 * min(lead / 168.0, 1.0)
        if lead > 48.0:
            evidence.append("extended_lead_time")

        # 3. Interquartile dispersion contribution
        iqr_term = 0.15 * min(iqr / 5.0, 1.0)
        if iqr > 3.0:
            evidence.append("distribution_dispersion")

        # 4. Asymmetry / Skew contribution
        if skew_proxy > 1.0:
            evidence.append("ensemble_asymmetry")

        # Base baseline uncertainty floor
        base_uncertainty = 0.05

        raw_prob = (
            base_uncertainty
            + spread_term
            + lead_term
            + iqr_term
            + (0.05 if skew_proxy > 1.0 else 0.0)
        )
        
        # Bounded between 1% and 98%
        probability = round(max(0.01, min(raw_prob, 0.98)), 4)

        if not evidence:
            evidence.append("nominal_conditions")

        risk_level = self._calculate_risk_level(probability)

        return BaselineResult(
            probability=probability,
            risk_level=risk_level,
            evidence=evidence,
            model_version=self.model_version,
        )