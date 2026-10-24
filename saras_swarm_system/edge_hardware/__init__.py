"""SARAS Swarm System - Edge Hardware & Inference Pipeline.

Lead: Member 1 (Hardware & Edge ML Lead)
Provides edge model deployment (ONNX/PyTorch/TFLite), thread-safe camera capture,
MAVLink telemetry integration with Pixhawk flight controllers, and empirical benchmarking.
"""

from edge_hardware.config.edge_config import EdgeConfig
from edge_hardware.inference.detector import EdgeDetector, DetectionResult
from edge_hardware.camera.capture import CameraStream
from edge_hardware.telemetry.mavlink_client import TelemetryClient, DroneTelemetry, GeoEstimate

__all__ = [
    "EdgeConfig",
    "EdgeDetector",
    "DetectionResult",
    "CameraStream",
    "TelemetryClient",
    "DroneTelemetry",
    "GeoEstimate",
]
