import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ServiceMetrics:
    total_predictions: int = 0
    abstentions_total: int = 0
    degraded_total: int = 0
    supported_total: int = 0
    total_latency_seconds: float = 0.0
    bust_counts: Dict[str, int] = field(
        default_factory=lambda: {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    )

    def record_inference(
        self, trust_state: str, risk_level: Optional[str], latency: float
    ) -> None:
        self.total_predictions += 1
        self.total_latency_seconds += latency

        if trust_state == "ABSTAINED":
            self.abstentions_total += 1
        elif trust_state == "DEGRADED":
            self.degraded_total += 1
        elif trust_state == "SUPPORTED":
            self.supported_total += 1

        if risk_level and risk_level in self.bust_counts:
            self.bust_counts[risk_level] += 1

    def generate_prometheus_text(self) -> str:
        avg_latency = (
            (self.total_latency_seconds / self.total_predictions)
            if self.total_predictions > 0
            else 0.0
        )
        lines = [
            "# HELP veyra_predictions_total Total count of reliability predictions served.",
            "# TYPE veyra_predictions_total counter",
            f"veyra_predictions_total {self.total_predictions}",
            "",
            "# HELP veyra_abstentions_total Count of predictions where model safely abstained.",
            "# TYPE veyra_abstentions_total counter",
            f"veyra_abstentions_total {self.abstentions_total}",
            "",
            "# HELP veyra_inference_latency_seconds_average Average inference time in seconds.",
            "# TYPE veyra_inference_latency_seconds_average gauge",
            f"veyra_inference_latency_seconds_average {round(avg_latency, 4)}",
            "",
            "# HELP veyra_risk_tier_total Predictions grouped by calibrated risk tiers.",
            "# TYPE veyra_risk_tier_total counter",
            f'veyra_risk_tier_total{{tier="LOW"}} {self.bust_counts["LOW"]}',
            f'veyra_risk_tier_total{{tier="MEDIUM"}} {self.bust_counts["MEDIUM"]}',
            f'veyra_risk_tier_total{{tier="HIGH"}} {self.bust_counts["HIGH"]}',
            f'veyra_risk_tier_total{{tier="CRITICAL"}} {self.bust_counts["CRITICAL"]}',
        ]
        return "\n".join(lines) + "\n"


telemetry = ServiceMetrics()