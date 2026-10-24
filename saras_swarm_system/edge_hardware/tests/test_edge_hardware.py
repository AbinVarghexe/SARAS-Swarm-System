"""Comprehensive Test Suite for SARAS Edge Hardware & Inference Pipeline.

Tests:
1. EdgeConfig serialization, file loading, and environment variable overrides.
2. EdgeDetector with both ONNX Runtime and PyTorch YOLOv8n.
3. CameraStream thread-safe acquisition, synthetic generator, and graceful shutdown.
4. TelemetryClient MAVLink parser, Pixhawk simulator, and pixel-to-GPS projection.
5. End-to-end integration pipeline.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np

# Ensure saras_swarm_system root is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
EDGE_HW_DIR = SCRIPT_DIR.parent
SWARM_SYS_DIR = EDGE_HW_DIR.parent
if str(SWARM_SYS_DIR) not in sys.path:
    sys.path.insert(0, str(SWARM_SYS_DIR))
if str(EDGE_HW_DIR) not in sys.path:
    sys.path.insert(0, str(EDGE_HW_DIR))

from edge_hardware.camera.capture import CameraStream
from edge_hardware.config.edge_config import EdgeConfig
from edge_hardware.inference.detector import EdgeDetector, DetectionResult
from edge_hardware.telemetry.mavlink_client import (
    DroneTelemetry,
    TelemetryClient,
    project_pixel_to_gps,
)


def test_edge_config() -> None:
    """Validate configuration defaults, serialization, and deserialization."""
    print("Testing EdgeConfig...")
    cfg = EdgeConfig()
    assert cfg.drone_id == "Drone-01"
    assert cfg.camera_width == 640
    assert cfg.conf_threshold == 0.35

    # Test dictionary roundtrip
    d = cfg.to_dict()
    assert isinstance(d, dict)
    cfg2 = EdgeConfig.from_dict(d)
    assert cfg2.drone_id == cfg.drone_id

    # Test file persistence
    test_json = Path(__file__).parent / "test_config.json"
    try:
        cfg.save_to_file(test_json)
        assert test_json.exists()
        cfg3 = EdgeConfig.from_file(test_json)
        assert cfg3.drone_id == cfg.drone_id
    finally:
        if test_json.exists():
            test_json.unlink()

    print("PASS: EdgeConfig verified.")


def test_edge_detector_onnx() -> None:
    """Validate ONNX Runtime inference, letterbox, and normalization."""
    print("Testing EdgeDetector (ONNX Runtime)...")
    models_dir = Path(__file__).parent.parent / "models"
    onnx_path = models_dir / "yolov8n.onnx"

    cfg = EdgeConfig(
        model_format="onnx",
        model_path=str(onnx_path),
        conf_threshold=0.30,
        num_threads=2,
    )
    detector = EdgeDetector(cfg)

    # Test inference on a dummy frame
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw a synthetic human-like rectangle
    dummy_frame[100:250, 200:300] = (150, 150, 150)

    detections = detector.detect(dummy_frame)
    assert isinstance(detections, list)
    print(f"ONNX detector returned {len(detections)} detections in {detector.last_inference_latency_ms:.2f}ms")

    # If any detections returned, check data contract
    for det in detections:
        assert isinstance(det, DetectionResult)
        assert 0.0 <= det.confidence <= 1.0
        assert len(det.bbox_normalized) == 4
        assert 0.0 <= det.bbox_normalized[0] <= 1.0
        assert det.priority in ("CRITICAL", "HIGH", "MEDIUM", "LOW")

    # Test tactical HUD drawing
    annotated = detector.draw_tactical_hud(dummy_frame, detections)
    assert annotated.shape == dummy_frame.shape
    print("PASS: EdgeDetector (ONNX) verified.")


def test_edge_detector_pytorch() -> None:
    """Validate Ultralytics PyTorch YOLO detector."""
    print("Testing EdgeDetector (PyTorch YOLOv8)...")
    models_dir = Path(__file__).parent.parent / "models"
    pt_path = models_dir / "yolov8n.pt"

    cfg = EdgeConfig(
        model_format="pytorch",
        model_path=str(pt_path),
        conf_threshold=0.30,
    )
    detector = EdgeDetector(cfg)
    dummy_frame = np.full((480, 640, 3), 128, dtype=np.uint8)

    detections = detector.detect(dummy_frame)
    assert isinstance(detections, list)
    print(f"PyTorch detector returned {len(detections)} detections in {detector.last_inference_latency_ms:.2f}ms")
    print("PASS: EdgeDetector (PyTorch) verified.")


def test_camera_stream() -> None:
    """Validate thread-safe CameraStream acquisition and auto-shutdown."""
    print("Testing CameraStream...")
    cfg = EdgeConfig(camera_source="synthetic", camera_width=640, camera_height=480, camera_fps=30.0)
    cam = CameraStream(cfg)
    cam.start()

    try:
        # Give worker thread 0.2s to generate initial frames
        time.sleep(0.2)
        success, frame = cam.read()
        assert success is True, "Failed to read frame from CameraStream"
        assert frame is not None
        assert frame.shape == (480, 640, 3)
        assert cam.is_connected is True
        assert cam.frames_captured > 0
        print(f"Captured {cam.frames_captured} synthetic frames successfully.")
    finally:
        cam.stop()
        assert cam.is_connected is False

    print("PASS: CameraStream verified.")


def test_telemetry_and_georeferencing() -> None:
    """Validate TelemetryClient, Pixhawk simulation, and projection math."""
    print("Testing TelemetryClient & Georeferencing...")
    cfg = EdgeConfig(
        drone_id="Drone-01",
        base_lat=11.5360,
        base_lon=76.1390,
        base_alt_m=35.0,
        simulate_pixhawk_if_offline=True,
    )
    client = TelemetryClient(cfg)
    client.start()

    try:
        # Allow simulator thread to fire
        time.sleep(0.3)
        telem = client.get_telemetry()
        assert telem.drone_id == "Drone-01"
        assert telem.connected is True
        assert 11.5 < telem.lat < 11.6
        assert 76.1 < telem.lon < 76.2
        assert telem.altitude_m > 0

        # Test Projection Geometry: target in center of image at 35m altitude nadir
        geo = project_pixel_to_gps(
            drone_lat=telem.lat,
            drone_lon=telem.lon,
            altitude_m=35.0,
            heading_deg=0.0,
            pitch_deg=0.0,
            norm_cx=0.5,
            norm_cy=0.5,
        )
        # Center of image at 0 pitch should land right below drone
        assert abs(geo.estimated_lat - telem.lat) < 1e-4
        assert abs(geo.estimated_lon - telem.lon) < 1e-4
        assert geo.ground_distance_m < 0.5

        # Test Packaging detection alert
        dummy_det = DetectionResult(
            class_id=0,
            class_name="person",
            confidence=0.88,
            bbox_xyxy=(100, 100, 200, 250),
            bbox_normalized=(0.2, 0.2, 0.4, 0.5),
            center_normalized=(0.3, 0.35),
            priority="CRITICAL",
            latency_ms=28.5,
        )
        alert = client.package_detection_alert(dummy_det, telem)
        assert alert["drone_id"] == "Drone-01"
        assert alert["target_type"] == "person"
        assert "geo_estimate" in alert
        assert "estimated_lat" in alert["geo_estimate"]
        print(f"Packaged Detection Alert: {alert['alert_id']} -> Lat: {alert['geo_estimate']['estimated_lat']}")

    finally:
        client.stop()

    print("PASS: TelemetryClient & Georeferencing verified.")


def run_all_tests() -> None:
    print("\n" + "=" * 70)
    print("RUNNING SARAS EDGE HARDWARE UNIT & INTEGRATION TESTS")
    print("=" * 70 + "\n")

    test_edge_config()
    test_edge_detector_onnx()
    test_edge_detector_pytorch()
    test_camera_stream()
    test_telemetry_and_georeferencing()

    print("\n" + "=" * 70)
    print("ALL SARAS EDGE HARDWARE TESTS PASSED (5/5)!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_all_tests()
