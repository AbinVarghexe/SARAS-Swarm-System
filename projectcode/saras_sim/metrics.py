from __future__ import annotations

from typing import Any, Dict


class SimulationMetrics:
    """Aggregates the key measurable indicators for SARAS evaluation."""

    def __init__(self) -> None:
        self.metrics: Dict[str, Any] = {
            "coverage_ratio": 0.0,
            "victim_detection_count": 0,
            "failure_count": 0,
            "reassigned_sector_count": 0,
            "steps_completed": 0,
            "average_detection_latency": 0.0,
        }

    def update(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            self.metrics[key] = value

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.metrics)
