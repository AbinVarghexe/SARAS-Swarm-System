"""SARAS Edge ML Inference Package."""

from edge_hardware.inference.detector import (
    COCO_CLASSES,
    DetectionResult,
    EdgeDetector,
    letterbox,
)

__all__ = ["EdgeDetector", "DetectionResult", "letterbox", "COCO_CLASSES"]
