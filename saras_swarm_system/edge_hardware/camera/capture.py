"""Thread-Safe Camera Capture Engine for SARAS Edge Companion Computer.

Provides the CameraStream class for zero-latency frame acquisition from USB webcams,
Raspberry Pi Camera Modules (CSI via libcamera / v4l2), recorded video files,
or high-fidelity synthetic aerial SAR video fallback with automated reconnection.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from typing import Optional, Tuple, Union

import cv2
import numpy as np

from edge_hardware.config.edge_config import EdgeConfig

logger = logging.getLogger("saras.edge.camera")


class CameraStream:
    """Thread-safe, non-blocking camera stream with auto-reconnection and zero-latency buffer."""

    def __init__(self, config: Optional[EdgeConfig] = None):
        self.config = config or EdgeConfig()
        self.source = self.config.camera_source
        self.width = self.config.camera_width
        self.height = self.config.camera_height
        self.target_fps = self.config.camera_fps

        self.cap: Optional[cv2.VideoCapture] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Frame buffer (only latest frame retained to eliminate queue lag)
        self._latest_frame: Optional[np.ndarray] = None
        self._last_frame_time: float = 0.0
        self.is_connected: bool = False
        self.is_synthetic: bool = False

        # Telemetry / Performance counters
        self.frames_captured: int = 0
        self.frames_dropped: int = 0
        self.fps_measured: float = 0.0
        self._fps_counter: int = 0
        self._fps_timer: float = time.time()
        self._synthetic_step: int = 0

    def start(self) -> CameraStream:
        """Start the background acquisition thread."""
        if self._running:
            return self

        self._running = True
        self._init_capture()

        self._thread = threading.Thread(target=self._capture_worker, daemon=True, name="SarasCameraWorker")
        self._thread.start()
        logger.info(f"Camera stream started on source: {self.source} ({self.width}x{self.height} @ {self.target_fps}fps)")
        return self

    def stop(self) -> None:
        """Stop background acquisition and release hardware resources."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._release_capture()
        self.is_connected = False
        logger.info("Camera stream stopped.")

    def __enter__(self) -> CameraStream:
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Fetch the most recent frame in a non-blocking manner.

        Returns:
            (success, frame_bgr): Tuple of status flag and NumPy array.
        """
        with self._lock:
            if self._latest_frame is not None:
                return True, self._latest_frame.copy()
            return False, None

    def _init_capture(self) -> None:
        """Attempt to open hardware camera or fall back to synthetic generator."""
        self._release_capture()

        if self.source == "synthetic":
            logger.info("Using synthetic aerial SAR video generator.")
            self.is_synthetic = True
            self.is_connected = True
            return

        try:
            # Check if source is an integer device index or file/pipeline
            if isinstance(self.source, int) or (isinstance(self.source, str) and self.source.isdigit()):
                dev_idx = int(self.source)
                # Attempt V4L2 on Linux or DSHOW on Windows
                backend = cv2.CAP_DSHOW if cv2.videoio_registry.getBackendName(cv2.CAP_DSHOW) else cv2.CAP_ANY
                self.cap = cv2.VideoCapture(dev_idx, backend)
            elif isinstance(self.source, str) and self.source.startswith("libcamerasrc"):
                # Raspberry Pi Camera GStreamer pipeline
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_GSTREAMER)
            else:
                self.cap = cv2.VideoCapture(str(self.source))

            if self.cap and self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
                self.is_connected = True
                self.is_synthetic = False
                logger.info(f"Hardware camera opened successfully: {self.source}")
            else:
                logger.warning(
                    f"Unable to open camera source '{self.source}'. Engaging high-fidelity SAR synthetic stream."
                )
                self.is_synthetic = True
                self.is_connected = True
        except Exception as e:
            logger.error(f"Error initializing camera: {e}. Switching to synthetic fallback.")
            self.is_synthetic = True
            self.is_connected = True

    def _release_capture(self) -> None:
        """Safely release cv2.VideoCapture object."""
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def _capture_worker(self) -> None:
        """Background thread continuously polling frames with zero lag."""
        reconnect_attempts = 0
        frame_interval = 1.0 / max(1.0, self.target_fps)

        while self._running:
            loop_start = time.perf_counter()

            if self.is_synthetic:
                frame = self._generate_synthetic_aerial_frame()
                with self._lock:
                    self._latest_frame = frame
                    self._last_frame_time = time.time()
                    self.frames_captured += 1
                self._update_fps()
            else:
                if self.cap is None or not self.cap.isOpened():
                    self.is_connected = False
                    if reconnect_attempts < self.config.camera_max_reconnect_attempts:
                        reconnect_attempts += 1
                        logger.warning(
                            f"Camera disconnected. Reconnection attempt {reconnect_attempts}/"
                            f"{self.config.camera_max_reconnect_attempts} in {self.config.camera_reconnect_delay_s}s..."
                        )
                        time.sleep(self.config.camera_reconnect_delay_s)
                        self._init_capture()
                        continue
                    else:
                        logger.error("Exceeded maximum camera reconnect attempts. Falling back to synthetic.")
                        self.is_synthetic = True
                        self.is_connected = True
                        continue

                ret, frame = self.cap.read()
                if ret and frame is not None:
                    reconnect_attempts = 0
                    self.is_connected = True
                    if frame.shape[1] != self.width or frame.shape[0] != self.height:
                        frame = cv2.resize(frame, (self.width, self.height))

                    with self._lock:
                        self._latest_frame = frame
                        self._last_frame_time = time.time()
                        self.frames_captured += 1
                    self._update_fps()
                else:
                    # Check if file reached end of stream -> loop
                    if isinstance(self.source, str) and not self.source.isdigit():
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    else:
                        logger.warning("Failed to grab camera frame. Retrying...")
                        self.is_connected = False
                        time.sleep(0.1)

            # Throttle to target FPS
            elapsed = time.perf_counter() - loop_start
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _update_fps(self) -> None:
        """Update measured FPS computation."""
        self._fps_counter += 1
        now = time.time()
        if now - self._fps_timer >= 1.0:
            self.fps_measured = self._fps_counter / (now - self._fps_timer)
            self._fps_counter = 0
            self._fps_timer = now

    def _generate_synthetic_aerial_frame(self) -> np.ndarray:
        """Generate high-fidelity aerial disaster search terrain (Wayanad landslide)."""
        self._synthetic_step += 1
        t = self._synthetic_step * 0.035
        w, h = self.width, self.height

        # Base mud/landslide earth
        base = np.full((h, w, 3), (38, 50, 61), dtype=np.uint8)

        # Dynamic contour lines
        for i in range(6):
            offset = int(math.sin(t * 0.4 + i) * 45 + i * (h // 6))
            pts = np.array(
                [
                    [0, offset + 30],
                    [w // 3, offset + 10],
                    [2 * w // 3, offset + 40],
                    [w, offset + 15],
                    [w, offset + 90],
                    [0, offset + 100],
                ],
                np.int32,
            )
            cv2.fillPoly(base, [pts], (26 + i * 3, 38 + i * 3, 46 + i * 2))

        # Forest border patches
        cv2.circle(base, (int(w * 0.15 + math.sin(t * 0.25) * 15), int(h * 0.25)), int(h * 0.22), (20, 55, 30), -1)
        cv2.circle(base, (int(w * 0.85 - math.sin(t * 0.3) * 20), int(h * 0.72)), int(h * 0.26), (18, 50, 28), -1)

        # River / mudflow path
        mud_pts = np.array(
            [
                [int(w * 0.42 + math.cos(t * 0.2) * 25), 0],
                [int(w * 0.58 + math.cos(t * 0.2) * 25), 0],
                [int(w * 0.68 + math.sin(t * 0.2) * 35), h],
                [int(w * 0.32 + math.sin(t * 0.2) * 35), h],
            ],
            np.int32,
        )
        cv2.fillPoly(base, [mud_pts], (42, 65, 82))

        # Primary victim figure (distress orange clothing)
        v1_x = int(w * 0.48 + math.sin(t * 0.5) * (w * 0.05))
        v1_y = int(h * 0.52 + math.cos(t * 0.5) * (h * 0.04))
        cv2.ellipse(base, (v1_x, v1_y), (8, 14), 15, 0, 360, (30, 120, 235), -1)
        cv2.circle(base, (v1_x, v1_y - 12), 5, (60, 160, 255), -1)

        # Add camera sensor noise
        noise = np.random.normal(0, 2.5, (h, w, 3)).astype(np.int16)
        frame = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return frame
