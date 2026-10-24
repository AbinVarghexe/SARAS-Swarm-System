"""Standalone Edge Node Runner for SARAS Autonomous Swarm Companion Computer.

Integrates:
  CameraStream (USB / PiCamera / Synthetic Fallback)
    -> EdgeDetector (ONNX Runtime / YOLOv8 / TFLite)
      -> TelemetryClient (Pixhawk MAVLink / Auto-Simulation)
        -> Command Backend (HTTP Alerts & WebSocket Telemetry)

Designed for 24/7 onboard execution on Raspberry Pi 4/5 companion computers.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2

# Add package root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_PARENT = SCRIPT_DIR.parent
if str(PROJECT_PARENT) not in sys.path:
    sys.path.insert(0, str(PROJECT_PARENT))

from edge_hardware.camera.capture import CameraStream
from edge_hardware.config.edge_config import EdgeConfig
from edge_hardware.inference.detector import EdgeDetector
from edge_hardware.telemetry.mavlink_client import TelemetryClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s): %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("saras.edge.node")


class SarasEdgeNode:
    """Master controller coordinating camera, inference, telemetry, and network uplink."""

    def __init__(self, config: EdgeConfig):
        self.config = config
        self.is_running = False

        logger.info(f"Initializing SARAS Companion Node: {self.config.drone_id}")
        self.camera = CameraStream(self.config)
        self.detector = EdgeDetector(self.config)
        self.telemetry_client = TelemetryClient(self.config)

        # Performance monitoring
        self.loop_count = 0
        self.total_detections = 0
        self.start_time = 0.0

    def start(self) -> None:
        """Start all subsystem threads and begin main processing pipeline."""
        self.is_running = True
        self.start_time = time.time()

        # Handle system interrupts (SIGINT, SIGTERM)
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)

        # Launch hardware threads
        self.camera.start()
        self.telemetry_client.start()

        logger.info("=" * 70)
        logger.info(f"SARAS EDGE COMPANION NODE ONLINE: {self.config.drone_id}")
        logger.info(f"Camera Source:    {self.config.camera_source}")
        logger.info(f"Inference Model:  {self.config.model_format.upper()} ({self.detector.model_path})")
        logger.info(f"MAVLink Channel:  {self.config.mavlink_connection}")
        logger.info(f"Backend Uplink:   {self.config.backend_http_url}")
        logger.info("=" * 70)

        self._main_loop()

    def _main_loop(self) -> None:
        """Core real-time perception-telemetry loop."""
        fps_timer = time.time()
        frames_in_sec = 0
        current_fps = 0.0

        try:
            while self.is_running:
                loop_start = time.perf_counter()

                # 1. Acquire lowest-latency frame from camera
                has_frame, frame = self.camera.read()
                if not has_frame or frame is None:
                    time.sleep(0.01)
                    continue

                # 2. Run Edge ML Inference
                detections = self.detector.detect(frame)
                self.loop_count += 1
                frames_in_sec += 1

                # 3. Read current Pixhawk telemetry state
                telem = self.telemetry_client.get_telemetry()

                # 4. Handle Detections & Alert Packaging
                if detections:
                    for det in detections:
                        self.total_detections += 1
                        # Push georeferenced alert to backend if critical/high
                        if det.confidence >= self.config.conf_threshold:
                            self.telemetry_client.push_detection_alert(det)

                # 5. Visual HUD Rendering (optional GUI or headless)
                annotated_frame = None
                if self.config.hud_overlay_enabled or self.config.display_gui:
                    annotated_frame = self.detector.draw_tactical_hud(
                        frame,
                        detections,
                        drone_info=telem.to_dict(),
                    )

                if self.config.display_gui and annotated_frame is not None:
                    cv2.imshow(f"SARAS Edge HUD - {self.config.drone_id}", annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        logger.info("User requested exit from GUI window.")
                        break

                # 6. Periodic Diagnostic Console Logs (every 2 seconds)
                now = time.time()
                if now - fps_timer >= 2.0:
                    current_fps = frames_in_sec / (now - fps_timer)
                    frames_in_sec = 0
                    fps_timer = now

                    logger.info(
                        f"[{self.config.drone_id}] FPS: {current_fps:.1f} | "
                        f"Infer: {self.detector.last_inference_latency_ms:.1f}ms | "
                        f"MAVLink: {telem.source} ({telem.flight_mode}) | "
                        f"Alt: {telem.altitude_m:.1f}m | Batt: {telem.battery_pct:.0f}% | "
                        f"Targets: {len(detections)}"
                    )

                # Maintain target cycle rate
                target_interval = 1.0 / max(1.0, self.config.camera_fps)
                elapsed = time.perf_counter() - loop_start
                sleep_needed = target_interval - elapsed
                if sleep_needed > 0:
                    time.sleep(sleep_needed)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received.")
        finally:
            self.stop()

    def stop(self) -> None:
        """Gracefully release camera, telemetry, and window handles."""
        if not self.is_running:
            return

        logger.info("Shutting down SARAS Edge Companion Node...")
        self.is_running = False

        self.camera.stop()
        self.telemetry_client.stop()

        if self.config.display_gui:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass

        runtime_s = time.time() - self.start_time
        logger.info(
            f"Node terminated. Total Runtime: {runtime_s:.1f}s | "
            f"Frames Processed: {self.loop_count} | Total Detections: {self.total_detections}"
        )

    def _handle_shutdown_signal(self, signum: int, frame: Any) -> None:
        logger.info(f"Received termination signal ({signum}). Initiating clean shutdown...")
        self.is_running = False


def parse_arguments() -> EdgeConfig:
    """Parse command line flags into EdgeConfig."""
    parser = argparse.ArgumentParser(description="SARAS Companion Computer Edge Node Runner")
    parser.add_argument("--drone-id", type=str, default="Drone-01", help="Drone vehicle identifier")
    parser.add_argument(
        "--camera",
        type=str,
        default="synthetic",
        help="Camera source: index ('0'), file path, or 'synthetic'",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="onnx",
        choices=["onnx", "pytorch", "tflite"],
        help="Inference model format",
    )
    parser.add_argument("--model-path", type=str, default="yolov8n.onnx", help="Path to weights file")
    parser.add_argument(
        "--mavlink",
        type=str,
        default="udpin:127.0.0.1:14550",
        help="MAVLink connection URI (e.g. /dev/ttyAMA0 or udpin:127.0.0.1:14550)",
    )
    parser.add_argument("--baud", type=int, default=57600, help="MAVLink serial baudrate")
    parser.add_argument("--backend", type=str, default="http://127.0.0.1:8000", help="SARAS command backend URL")
    parser.add_argument("--threads", type=int, default=4, help="CPU thread allocation for inference")
    parser.add_argument("--conf", type=float, default=0.35, help="Confidence threshold")
    parser.add_argument("--gui", action="store_true", help="Display OpenCV tactical HUD window")
    parser.add_argument("--config-file", type=str, default=None, help="Path to JSON configuration file")

    args = parser.parse_args()

    if args.config_file and Path(args.config_file).exists():
        cfg = EdgeConfig.from_file(args.config_file)
    else:
        cfg = EdgeConfig()

    cfg.drone_id = args.drone_id
    cfg.camera_source = int(args.camera) if args.camera.isdigit() else args.camera
    cfg.model_format = args.format
    cfg.model_path = args.model_path
    cfg.mavlink_connection = args.mavlink
    cfg.mavlink_baud = args.baud
    cfg.backend_http_url = args.backend
    cfg.num_threads = args.threads
    cfg.conf_threshold = args.conf
    cfg.display_gui = args.gui

    return cfg


def main() -> None:
    config = parse_arguments()
    node = SarasEdgeNode(config)
    node.start()


if __name__ == "__main__":
    main()
