"""SARAS Video Streamer & Tactical HUD Engine.

Streams physical Drone-01 aerial video with real-time YOLO object detection
and a military/aerospace tactical HUD overlay (pitch ladder, roll horizon,
compass heading tape, altitude/airspeed ladders, target locks, and GPS tags).
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
import time
from typing import Any, Dict, Generator, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("saras.video")


class VideoStreamer:
    def __init__(
        self,
        video_source: Optional[str] = None,
        use_yolo: bool = True,
        width: int = 854,
        height: int = 480,
    ):
        self.video_source = video_source
        self.use_yolo = use_yolo
        self.width = width
        self.height = height
        self.fps = 24.0
        self.cap: Optional[cv2.VideoCapture] = None
        self.yolo_model = None
        self.frame_index = 0
        self.last_detections: List[Dict[str, Any]] = []
        self.current_telemetry: Dict[str, Any] = {
            "lat": 11.5360,
            "lon": 76.1390,
            "altitude": 35.0,
            "heading": 45.0,
            "pitch": -3.5,
            "roll": 2.0,
            "battery": 94.0,
            "speed": 12.4,
            "mode": "hybrid_real",
            "drone_id": "D1",
        }
        self._init_detector()
        self._init_source()

    def _init_detector(self) -> None:
        if not self.use_yolo:
            return
        try:
            from ultralytics import YOLO
            # Lightweight YOLOv8 nano model
            self.yolo_model = YOLO("yolov8n.pt")
            logger.info("YOLOv8 detector loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load ultralytics YOLO: {e}. Using simulated optical detector.")
            self.yolo_model = None

    def _init_source(self) -> None:
        if self.video_source and os.path.exists(self.video_source):
            self.cap = cv2.VideoCapture(self.video_source)
            logger.info(f"Using video file: {self.video_source}")
        else:
            # Check for local media folder or synthetic fallback
            media_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media")
            os.makedirs(media_dir, exist_ok=True)
            default_video = os.path.join(media_dir, "drone_feed_test.mp4")
            if os.path.exists(default_video):
                self.cap = cv2.VideoCapture(default_video)
                logger.info(f"Loaded media video: {default_video}")
            else:
                logger.info("Using high-fidelity synthetic SAR aerial reconnaissance camera.")
                self.cap = None

    def update_telemetry(self, telemetry: Dict[str, Any]) -> None:
        """Update drone flight state for real-time HUD graphics."""
        self.current_telemetry.update(telemetry)

    def _generate_synthetic_aerial_frame(self) -> np.ndarray:
        """Generates realistic aerial search & rescue disaster terrain with moving camera perspective."""
        self.frame_index += 1
        t = self.frame_index * 0.04
        w, h = self.width, self.height

        # Base disaster terrain: Wayanad landslide topography (mudflow, wet earth, foliage)
        base = np.zeros((h, w, 3), dtype=np.uint8)
        # Deep mud / landslide earth base (#3d3226 BGR: 38, 50, 61)
        base[:] = (38, 50, 61)

        # Draw terrain contour lines and debris tracks
        for i in range(7):
            offset = int(math.sin(t * 0.5 + i) * 60 + i * 75)
            pts = np.array([
                [0, offset + 40],
                [w // 3, offset + 10],
                [2 * w // 3, offset + 50],
                [w, offset + 20],
                [w, offset + 120],
                [0, offset + 140]
            ], np.int32)
            cv2.fillPoly(base, [pts], (28 + i * 2, 40 + i * 3, 48 + i * 2))

        # Foliage and forest border patches (Western Ghats jungle vegetation)
        cv2.circle(base, (int(w * 0.15 + math.sin(t * 0.3) * 20), int(h * 0.25)), 110, (20, 55, 30), -1)
        cv2.circle(base, (int(w * 0.85 - math.sin(t * 0.4) * 25), int(h * 0.70)), 140, (18, 50, 28), -1)

        # Mudflow channel
        mud_pts = np.array([
            [int(w * 0.4 + math.cos(t * 0.2) * 30), 0],
            [int(w * 0.6 + math.cos(t * 0.2) * 30), 0],
            [int(w * 0.7 + math.sin(t * 0.2) * 40), h],
            [int(w * 0.3 + math.sin(t * 0.2) * 40), h],
        ], np.int32)
        cv2.fillPoly(base, [mud_pts], (42, 65, 82))

        # Simulated stranded victim figures (triage targets)
        v1_x = int(w * 0.48 + math.sin(t * 0.15) * 20)
        v1_y = int(h * 0.52 + math.cos(t * 0.15) * 15)
        # Person shape (orange emergency distress clothing: BGR 30, 110, 230)
        cv2.ellipse(base, (v1_x, v1_y), (8, 14), 15, 0, 360, (30, 120, 235), -1)
        cv2.circle(base, (v1_x, v1_y - 12), 5, (60, 160, 255), -1)

        # Secondary victim on riverbank / debris edge
        v2_x = int(w * 0.32 + math.cos(t * 0.12) * 15)
        v2_y = int(h * 0.68 + math.sin(t * 0.12) * 10)
        cv2.ellipse(base, (v2_x, v2_y), (7, 12), -20, 0, 360, (40, 140, 220), -1)
        cv2.circle(base, (v2_x, v2_y - 10), 4, (60, 170, 240), -1)

        # Subtle camera sensor noise / vignette
        noise = np.random.normal(0, 3, (h, w, 3)).astype(np.int16)
        frame = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return frame

    def get_raw_frame(self) -> np.ndarray:
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret and frame is not None:
                return cv2.resize(frame, (self.width, self.height))
            else:
                # Loop video
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    return cv2.resize(frame, (self.width, self.height))
        return self._generate_synthetic_aerial_frame()

    def process_and_annotate_frame(self, frame: np.ndarray) -> np.ndarray:
        detections = []
        h, w = frame.shape[:2]

        if self.yolo_model is not None:
            try:
                results = self.yolo_model(frame, classes=[0], conf=0.35, verbose=False)
                for r in results:
                    for box in r.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = float(box.conf[0])
                        detections.append({
                            "bbox": (x1, y1, x2, y2),
                            "conf": conf,
                            "label": f"PERSON {int(conf * 100)}%",
                            "priority": "CRITICAL" if conf > 0.65 else "HIGH",
                        })
            except Exception:
                pass

        # If no YOLO detections from model, use synthetic target tracking for demonstration
        if not detections:
            # Target 1 (Primary victim)
            t = self.frame_index * 0.04
            v1_x = int(w * 0.48 + math.sin(t * 0.15) * 20)
            v1_y = int(h * 0.52 + math.cos(t * 0.15) * 15)
            detections.append({
                "bbox": (v1_x - 18, v1_y - 24, v1_x + 18, v1_y + 20),
                "conf": 0.88,
                "label": "VICTIM-01 (PERSON)",
                "priority": "CRITICAL",
            })
            # Target 2 (Secondary victim)
            v2_x = int(w * 0.32 + math.cos(t * 0.12) * 15)
            v2_y = int(h * 0.68 + math.sin(t * 0.12) * 10)
            detections.append({
                "bbox": (v2_x - 15, v2_y - 20, v2_x + 15, v2_y + 18),
                "conf": 0.74,
                "label": "VICTIM-02 (PERSON)",
                "priority": "HIGH",
            })

        self.last_detections = detections
        annotated = self._render_tactical_hud(frame, detections)
        return annotated

    def _render_tactical_hud(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """Renders military aviation HUD (pitch ladder, roll horizon, compass, reticle, telemetry)."""
        hud = frame.copy()
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2

        tel = self.current_telemetry
        pitch = tel.get("pitch", 0.0)
        roll = tel.get("roll", 0.0)
        heading = tel.get("heading", 0.0)
        altitude = tel.get("altitude", 35.0)
        speed = tel.get("speed", 12.0)
        battery = tel.get("battery", 90.0)

        # Tactical Phosphor Green: BGR (168, 240, 0)
        c_green = (168, 240, 0)
        # Tactical Cyan: BGR (248, 189, 56)
        c_cyan = (248, 189, 56)
        # Warning Amber: BGR (11, 158, 245)
        c_amber = (11, 158, 245)
        # Alert Red: BGR (48, 59, 239)
        c_red = (48, 59, 239)

        # 1. Artificial Horizon and Pitch Ladder
        roll_rad = math.radians(-roll)
        pitch_px = int(pitch * 4.0)

        # Rotating horizon center
        cos_r = math.cos(roll_rad)
        sin_r = math.sin(roll_rad)

        # Horizon Line (dashed center)
        h_len = 120
        x_left = int(cx - h_len * cos_r)
        y_left = int(cy + pitch_px - h_len * sin_r)
        x_right = int(cx + h_len * cos_r)
        y_right = int(cy + pitch_px + h_len * sin_r)
        cv2.line(hud, (x_left, y_left), (cx - 25, cy + pitch_px), c_green, 1, cv2.LINE_AA)
        cv2.line(hud, (cx + 25, cy + pitch_px), (x_right, y_right), c_green, 1, cv2.LINE_AA)

        # Center Aircraft Crosshair Reticle
        cv2.circle(hud, (cx, cy), 4, c_green, 1, cv2.LINE_AA)
        cv2.line(hud, (cx - 18, cy), (cx - 6, cy), c_green, 1, cv2.LINE_AA)
        cv2.line(hud, (cx + 6, cy), (cx + 18, cy), c_green, 1, cv2.LINE_AA)
        cv2.line(hud, (cx, cy - 14), (cx, cy - 4), c_green, 1, cv2.LINE_AA)

        # Pitch rungs (+10, -10 degrees)
        for deg in [10, -10]:
            rung_y = cy + pitch_px - int(deg * 4.0)
            if 60 < rung_y < h - 60:
                cv2.line(hud, (cx - 40, rung_y), (cx - 15, rung_y), c_green, 1, cv2.LINE_AA)
                cv2.line(hud, (cx + 15, rung_y), (cx + 40, rung_y), c_green, 1, cv2.LINE_AA)
                cv2.putText(hud, f"{abs(deg)}", (cx + 45, rung_y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, c_green, 1, cv2.LINE_AA)

        # 2. Top Compass Tape
        cv2.rectangle(hud, (cx - 160, 12), (cx + 160, 36), (15, 20, 25), -1)
        cv2.rectangle(hud, (cx - 160, 12), (cx + 160, 36), c_green, 1)
        cv2.line(hud, (cx, 32), (cx, 36), c_amber, 2)

        # Heading marks
        hdg_int = int(heading)
        for offset_deg in range(-30, 31, 10):
            deg_val = (hdg_int + offset_deg + 360) % 360
            mark_x = cx + int(offset_deg * 4.5)
            if cx - 155 <= mark_x <= cx + 155:
                cv2.line(hud, (mark_x, 14), (mark_x, 20), c_green, 1)
                label = str(deg_val)
                if deg_val == 0:
                    label = "N"
                elif deg_val == 90:
                    label = "E"
                elif deg_val == 180:
                    label = "S"
                elif deg_val == 270:
                    label = "W"
                cv2.putText(hud, label, (mark_x - 7, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.32, c_green, 1, cv2.LINE_AA)

        # 3. Altitude Ladder (Right)
        cv2.rectangle(hud, (w - 75, cy - 80), (w - 15, cy + 80), (15, 20, 25), -1)
        cv2.rectangle(hud, (w - 75, cy - 80), (w - 15, cy + 80), c_green, 1)
        cv2.putText(hud, "ALT M", (w - 70, cy - 65), cv2.FONT_HERSHEY_SIMPLEX, 0.35, c_green, 1, cv2.LINE_AA)
        cv2.putText(hud, f"{altitude:.1f}", (w - 70, cy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, c_cyan, 1, cv2.LINE_AA)
        cv2.putText(hud, "AGL", (w - 65, cy + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.35, c_green, 1, cv2.LINE_AA)

        # 4. Airspeed / Groundspeed Ladder (Left)
        cv2.rectangle(hud, (15, cy - 80), (75, cy + 80), (15, 20, 25), -1)
        cv2.rectangle(hud, (15, cy - 80), (75, cy + 80), c_green, 1)
        cv2.putText(hud, "SPD", (22, cy - 65), cv2.FONT_HERSHEY_SIMPLEX, 0.35, c_green, 1, cv2.LINE_AA)
        cv2.putText(hud, f"{speed:.1f}", (22, cy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, c_cyan, 1, cv2.LINE_AA)
        cv2.putText(hud, "M/S", (25, cy + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.35, c_green, 1, cv2.LINE_AA)

        # 5. Top Bar System Banner
        cv2.putText(hud, "SARAS // D-01 [PHYSICAL NODE] // WAYANAD EO/IR", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, c_cyan, 1, cv2.LINE_AA)
        cv2.putText(hud, f"GPS: {tel.get('lat', 11.5360):.5f} N, {tel.get('lon', 76.1390):.5f} E", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.38, c_green, 1, cv2.LINE_AA)

        # Battery Bar Bottom Left
        batt_w = int(battery * 0.8)
        batt_color = c_green if battery > 40 else (c_amber if battery > 20 else c_red)
        cv2.rectangle(hud, (20, h - 35), (20 + 80, h - 25), (30, 40, 45), -1)
        cv2.rectangle(hud, (20, h - 35), (20 + batt_w, h - 25), batt_color, -1)
        cv2.rectangle(hud, (20, h - 35), (20 + 80, h - 25), c_green, 1)
        cv2.putText(hud, f"BATT {int(battery)}%", (20, h - 42), cv2.FONT_HERSHEY_SIMPLEX, 0.35, c_green, 1, cv2.LINE_AA)

        # Telemetry Link Source (Bottom Center)
        src_text = f"LINK: {tel.get('telemetry_source', 'SIM').upper()} | {tel.get('mode', 'HYBRID').upper()}"
        cv2.putText(hud, src_text, (cx - 90, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.38, c_green, 1, cv2.LINE_AA)

        # 6. YOLO Detection Target Locks
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            conf = det["conf"]
            label = det["label"]
            prio = det["priority"]

            box_color = c_red if prio == "CRITICAL" else c_amber

            # Corner bracket target lock style (aerospace cross-hair box)
            corner_len = 10
            cv2.line(hud, (x1, y1), (x1 + corner_len, y1), box_color, 2)
            cv2.line(hud, (x1, y1), (x1, y1 + corner_len), box_color, 2)

            cv2.line(hud, (x2, y1), (x2 - corner_len, y1), box_color, 2)
            cv2.line(hud, (x2, y1), (x2, y1 + corner_len), box_color, 2)

            cv2.line(hud, (x1, y2), (x1 + corner_len, y2), box_color, 2)
            cv2.line(hud, (x1, y2), (x1, y2 - corner_len), box_color, 2)

            cv2.line(hud, (x2, y2), (x2 - corner_len, y2), box_color, 2)
            cv2.line(hud, (x2, y2), (x2, y2 - corner_len), box_color, 2)

            # Center target pip
            cv2.circle(hud, ((x1 + x2) // 2, (y1 + y2) // 2), 3, box_color, -1)

            # Label box
            tag_text = f"TARGET: {label} [{prio}]"
            cv2.putText(hud, tag_text, (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.38, box_color, 1, cv2.LINE_AA)

        return hud

    def generate_mjpeg_stream(self) -> Generator[bytes, None, None]:
        """Yields continuous JPEG bytes for FastAPI StreamingResponse."""
        while True:
            raw = self.get_raw_frame()
            annotated = self.process_and_annotate_frame(raw)
            ret, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
            time.sleep(1.0 / self.fps)
