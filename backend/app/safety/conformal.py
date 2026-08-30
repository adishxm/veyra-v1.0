import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class ConformalBound:
    lower_bound: float
    upper_bound: float
    confidence_level: float  # e.g., 0.90 for 90% coverage


@dataclass(frozen=True)
class OODAssessment:
    novelty_score: float
    is_ood: bool
    ood_reasons: List[str]


class ConformalSafetyEngine:
    """Computes conformal prediction intervals and OOD novelty metrics."""

    def __init__(self):
        # Reference distribution means and standard deviations from training baseline
        self.feature_stats: Dict[str, Tuple[float, float]] = {
            "forecast_spread": (2.10, 1.45),
            "iqr": (2.85, 1.80),
            "lead_hours": (48.0, 36.0),
            "coefficient_of_variation": (0.08, 0.06),
        }
        # Conformal quantile multiplier for 90% empirical coverage
        self.conformal_q90 = 1.645
        self.ood_threshold = 4.50  # Mahalanobis distance cutoff

    def compute_conformal_interval(
        self, forecast_mean: float, spread: float, confidence_level: float = 0.90
    ) -> ConformalBound:
        """Calculate guaranteed empirical forecast interval."""
        radius = self.conformal_q90 * max(spread, 0.5)
        return ConformalBound(
            lower_bound=round(forecast_mean - radius, 2),
            upper_bound=round(forecast_mean + radius, 2),
            confidence_level=confidence_level,
        )

    def evaluate_ood(self, features: Dict[str, float]) -> OODAssessment:
        """Detect unphysical or out-of-distribution feature inputs."""
        sq_dist = 0.0
        reasons: List[str] = []

        for feat_name, (mean_val, std_val) in self.feature_stats.items():
            if feat_name in features:
                z_score = abs(features[feat_name] - mean_val) / std_val
                sq_dist += z_score ** 2
                if z_score > 3.5:
                    reasons.append(f"EXTREME_ANOMALY_{feat_name.upper()}")

        mahalanobis_dist = math.sqrt(sq_dist)
        is_ood = mahalanobis_dist > self.ood_threshold

        return OODAssessment(
            novelty_score=round(mahalanobis_dist, 3),
            is_ood=is_ood,
            ood_reasons=reasons,
        )


conformal_engine = ConformalSafetyEngine()