"""Configuration module for SARAS Edge Hardware & Inference Pipeline.

Defines the EdgeConfig dataclass and environment variable loaders for
onboard camera acquisition, model execution, MAVLink Pixhawk telemetry,
and command-backend communication on Raspberry Pi 4/5 companion computers.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class EdgeConfig:
    """Configuration settings for the SARAS Edge Companion Node."""

    # Drone Identity
    drone_id: str = "Drone-01"

    # Camera Configuration
    # camera_source: int (device index e.g. 0), str (path to video or GStreamer pipeline), or "synthetic"
    camera_source: Union[int, str] = "synthetic"
    camera_width: int = 640
    camera_height: int = 480
    camera_fps: float = 30.0
    camera_reconnect_delay_s: float = 2.0
    camera_max_reconnect_attempts: int = 10
    camera_hfov_deg: float = 78.0  # Horizontal Field of View (e.g. Raspberry Pi Camera v2/v3)
    camera_vfov_deg: float = 54.0  # Vertical Field of View

    # Model & Inference Configuration
    # model_format: "onnx", "pytorch", or "tflite"
    model_format: str = "onnx"
    model_path: str = "yolov8n.onnx"
    input_width: int = 640
    input_height: int = 640
    conf_threshold: float = 0.35
    iou_threshold: float = 0.45
    # Class IDs to retain (e.g. [0] for COCO 'person')
    target_classes: List[int] = field(default_factory=lambda: [0])
    # Execution backend: "cpu", "cuda", "edge_tpu"
    device: str = "cpu"
    # CPU thread allocation (4 cores on Raspberry Pi 4/5)
    num_threads: int = 4

    # MAVLink Flight Controller Telemetry
    # Connection string: e.g. "udpin:127.0.0.1:14550", "/dev/ttyAMA0", or "/dev/ttyACM0"
    mavlink_connection: str = "udpin:127.0.0.1:14550"
    mavlink_baud: int = 57600
    telemetry_rate_hz: float = 10.0
    simulate_pixhawk_if_offline: bool = True
    heartbeat_timeout_s: float = 3.5

    # Geolocation Anchor (Default: Wayanad Chooralmala, Kerala landslide epicenter)
    base_lat: float = 11.5360
    base_lon: float = 76.1390
    base_alt_m: float = 35.0

    # Backend Network Endpoints
    backend_http_url: str = "http://127.0.0.1:8000"
    backend_ws_url: str = "ws://127.0.0.1:8000/ws/telemetry"
    alert_http_endpoint: str = "/api/hazard/report"
    network_timeout_s: float = 3.0
    alert_cooldown_s: float = 2.0  # Min seconds between alerts for same detection

    # Visual HUD & Stream Settings
    hud_overlay_enabled: bool = True
    display_gui: bool = False
    save_detection_snapshots: bool = False
    snapshot_dir: str = "detections_log"

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize configuration to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Persist configuration to a JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EdgeConfig:
        """Create an EdgeConfig instance from a dictionary."""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> EdgeConfig:
        """Load configuration from a JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_env(cls) -> EdgeConfig:
        """Load configuration overriding defaults with SARAS_* environment variables."""
        cfg = cls()

        if "SARAS_DRONE_ID" in os.environ:
            cfg.drone_id = os.environ["SARAS_DRONE_ID"]

        if "SARAS_CAMERA_SOURCE" in os.environ:
            val = os.environ["SARAS_CAMERA_SOURCE"]
            cfg.camera_source = int(val) if val.isdigit() else val

        if "SARAS_MODEL_FORMAT" in os.environ:
            cfg.model_format = os.environ["SARAS_MODEL_FORMAT"].lower()

        if "SARAS_MODEL_PATH" in os.environ:
            cfg.model_path = os.environ["SARAS_MODEL_PATH"]

        if "SARAS_CONF_THRESHOLD" in os.environ:
            cfg.conf_threshold = float(os.environ["SARAS_CONF_THRESHOLD"])

        if "SARAS_MAVLINK_CONN" in os.environ:
            cfg.mavlink_connection = os.environ["SARAS_MAVLINK_CONN"]

        if "SARAS_BACKEND_HTTP" in os.environ:
            cfg.backend_http_url = os.environ["SARAS_BACKEND_HTTP"]

        if "SARAS_BACKEND_WS" in os.environ:
            cfg.backend_ws_url = os.environ["SARAS_BACKEND_WS"]

        if "SARAS_NUM_THREADS" in os.environ:
            cfg.num_threads = int(os.environ["SARAS_NUM_THREADS"])

        return cfg


# Global default configuration instance
default_edge_config = EdgeConfig()
