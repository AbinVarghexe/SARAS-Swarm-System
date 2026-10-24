"""MAVLink Flight Controller Telemetry Interface for SARAS Swarm Companion Node.

Connects Raspberry Pi 4/5 companion computer to Pixhawk flight controller via UART/USB
or UDP. Collects high-frequency flight telemetry (GPS, altitude, heading, battery, mode)
and packages Edge ML detections with camera-to-ground georeferenced coordinate projections
into the standardized SARAS Swarm JSON schema.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

from edge_hardware.config.edge_config import EdgeConfig
from edge_hardware.inference.detector import DetectionResult

logger = logging.getLogger("saras.edge.telemetry")

# WGS84 Constants for Kerala/Equatorial latitude
METERS_PER_DEG_LAT = 111000.0


@dataclass
class DroneTelemetry:
    """Standardized snapshot of drone flight and system telemetry."""

    drone_id: str
    connected: bool = False
    source: str = "standby"  # "mavlink", "simulated", "standby"
    timestamp: float = field(default_factory=time.time)

    # Position & Kinematics
    lat: float = 11.5360
    lon: float = 76.1390
    altitude_m: float = 35.0  # Above Ground Level (AGL)
    heading_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    groundspeed_mps: float = 12.0
    climb_rate_mps: float = 0.0

    # Power & System Health
    battery_pct: float = 95.0
    battery_voltage_v: float = 15.8
    flight_mode: str = "AUTO"
    armed: bool = True
    satellites_visible: int = 14
    gps_fix_type: int = 3  # 3 = 3D Fix
    packet_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert telemetry to serializable dictionary."""
        d = asdict(self)
        d["timestamp"] = round(self.timestamp, 3)
        d["lat"] = round(self.lat, 6)
        d["lon"] = round(self.lon, 6)
        d["altitude_m"] = round(self.altitude_m, 1)
        d["heading_deg"] = round(self.heading_deg, 1)
        d["pitch_deg"] = round(self.pitch_deg, 1)
        d["roll_deg"] = round(self.roll_deg, 1)
        d["groundspeed_mps"] = round(self.groundspeed_mps, 1)
        d["battery_pct"] = round(self.battery_pct, 1)
        return d


@dataclass
class GeoEstimate:
    """Georeferenced ground coordinate estimate for camera detection."""

    estimated_lat: float
    estimated_lon: float
    ground_distance_m: float
    bearing_deg: float
    uncertainty_radius_m: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "estimated_lat": round(self.estimated_lat, 6),
            "estimated_lon": round(self.estimated_lon, 6),
            "ground_distance_m": round(self.ground_distance_m, 2),
            "bearing_deg": round(self.bearing_deg, 1),
            "uncertainty_radius_m": round(self.uncertainty_radius_m, 2),
        }


def project_pixel_to_gps(
    drone_lat: float,
    drone_lon: float,
    altitude_m: float,
    heading_deg: float,
    pitch_deg: float,
    norm_cx: float,
    norm_cy: float,
    hfov_deg: float = 78.0,
    vfov_deg: float = 54.0,
) -> GeoEstimate:
    """Project 2D camera detection coordinates to real-world WGS-84 GPS coordinates.

    Uses pinhole camera projection geometry taking into account drone altitude AGL,
    gimbal/drone pitch angle, and heading orientation.
    """
    # Normalized displacement from optical center [-0.5, +0.5]
    dx = norm_cx - 0.5
    dy = norm_cy - 0.5

    # Angular displacement in camera frame (radians)
    azimuth_cam = math.atan(2.0 * dx * math.tan(math.radians(hfov_deg / 2.0)))
    elevation_cam = math.atan(2.0 * dy * math.tan(math.radians(vfov_deg / 2.0)))

    # Total pitch angle relative to nadir (pitch_deg tilts camera forward/backward)
    total_elevation = math.radians(pitch_deg) + elevation_cam

    # Ground distance forward (along camera heading) and cross-track (perpendicular)
    alt = max(2.0, altitude_m)
    # Ground projection distance forward
    d_forward = alt * math.tan(total_elevation)
    d_cross = (alt / math.cos(total_elevation)) * math.tan(azimuth_cam) if math.cos(total_elevation) != 0 else 0.0

    # Total horizontal ground offset
    total_ground_dist = math.hypot(d_forward, d_cross)
    relative_bearing = math.degrees(math.atan2(d_cross, max(0.1, d_forward)))
    absolute_bearing = (heading_deg + relative_bearing) % 360.0

    # Convert distance and bearing to delta lat/lon
    bearing_rad = math.radians(absolute_bearing)
    meters_per_deg_lon = METERS_PER_DEG_LAT * math.cos(math.radians(drone_lat))

    delta_north = total_ground_dist * math.cos(bearing_rad)
    delta_east = total_ground_dist * math.sin(bearing_rad)

    est_lat = drone_lat + (delta_north / METERS_PER_DEG_LAT)
    est_lon = drone_lon + (delta_east / meters_per_deg_lon)

    # Uncertainty scales with altitude and distance
    uncertainty = 1.5 + (alt * 0.05) + (total_ground_dist * 0.08)

    return GeoEstimate(
        estimated_lat=est_lat,
        estimated_lon=est_lon,
        ground_distance_m=total_ground_dist,
        bearing_deg=absolute_bearing,
        uncertainty_radius_m=uncertainty,
    )


class TelemetryClient:
    """MAVLink telemetry receiver with automated Pixhawk simulation fallback."""

    def __init__(
        self,
        config: Optional[EdgeConfig] = None,
        on_telemetry_callback: Optional[Callable[[DroneTelemetry], None]] = None,
    ):
        self.config = config or EdgeConfig()
        self.on_telemetry = on_telemetry_callback

        self.telemetry = DroneTelemetry(
            drone_id=self.config.drone_id,
            lat=self.config.base_lat,
            lon=self.config.base_lon,
            altitude_m=self.config.base_alt_m,
        )

        self._lock = threading.Lock()
        self._running = False
        self._listener_thread: Optional[threading.Thread] = None
        self._sim_thread: Optional[threading.Thread] = None
        self._master: Any = None
        self.last_heartbeat_time: float = 0.0

        # Alert throttling tracker: {target_key: last_alert_timestamp}
        self._alert_cooldowns: Dict[str, float] = {}

    def start(self) -> TelemetryClient:
        """Start telemetry receiver and background connection management."""
        if self._running:
            return self

        self._running = True
        self._listener_thread = threading.Thread(
            target=self._mavlink_worker,
            daemon=True,
            name="SarasMavlinkWorker",
        )
        self._listener_thread.start()
        logger.info(f"Telemetry client initialized. Connecting to: {self.config.mavlink_connection}")
        return self

    def stop(self) -> None:
        """Stop background telemetry listener."""
        self._running = False
        if self._master:
            try:
                self._master.close()
            except Exception:
                pass
            self._master = None
        logger.info("Telemetry client stopped.")

    def get_telemetry(self) -> DroneTelemetry:
        """Fetch a thread-safe copy of latest drone telemetry."""
        with self._lock:
            return DroneTelemetry(**asdict(self.telemetry))

    def _mavlink_worker(self) -> None:
        """Worker thread attempting MAVLink connection or launching simulator."""
        try:
            from pymavlink import mavutil
        except ImportError:
            logger.warning("pymavlink not installed. Initiating internal Pixhawk flight simulator.")
            self._run_simulator()
            return

        reconnect_delay = 2.0
        while self._running:
            try:
                logger.info(f"Opening MAVLink link on {self.config.mavlink_connection} (baud={self.config.mavlink_baud})...")
                # Handle serial vs UDP connections
                if (
                    self.config.mavlink_connection.startswith("/dev/")
                    or self.config.mavlink_connection.startswith("COM")
                ):
                    self._master = mavutil.mavlink_connection(
                        self.config.mavlink_connection,
                        baud=self.config.mavlink_baud,
                        autoreconnect=True,
                        source_system=255,
                    )
                else:
                    self._master = mavutil.mavlink_connection(
                        self.config.mavlink_connection,
                        autoreconnect=True,
                        source_system=255,
                    )

                logger.info("MAVLink connection created. Waiting for Pixhawk heartbeat...")

                # Connection monitor loop
                while self._running:
                    msg = self._master.recv_match(blocking=False)
                    if msg is not None:
                        self._handle_mavlink_msg(msg)
                    else:
                        # Check hardware heartbeat timeout only if previously connected via mavlink
                        now = time.time()
                        if self.telemetry.source == "mavlink" and (now - self.last_heartbeat_time > self.config.heartbeat_timeout_s):
                            logger.warning("Pixhawk hardware heartbeat lost. Transitioning to fallback simulator.")
                            with self._lock:
                                self.telemetry.connected = False
                                self.telemetry.source = "offline"

                        # If physical hardware is not broadcasting, drive trajectory via internal simulator
                        if self.telemetry.source != "mavlink" and self.config.simulate_pixhawk_if_offline:
                            self._step_simulation()

                        time.sleep(1.0 / max(5.0, self.config.telemetry_rate_hz))

            except Exception as e:
                logger.warning(f"MAVLink connection error: {e}. Retrying in {reconnect_delay}s...")
                with self._lock:
                    self.telemetry.connected = False
                if self.config.simulate_pixhawk_if_offline:
                    self._step_simulation()
                time.sleep(reconnect_delay)

    def _handle_mavlink_msg(self, msg: Any) -> None:
        """Parse raw MAVLink packets into standardized drone telemetry."""
        msg_type = msg.get_type()

        with self._lock:
            self.telemetry.timestamp = time.time()
            self.telemetry.packet_count += 1

            if msg_type == "HEARTBEAT":
                self.last_heartbeat_time = time.time()
                self.telemetry.connected = True
                self.telemetry.source = "mavlink"

                # Check armed status
                if hasattr(msg, "base_mode"):
                    self.telemetry.armed = bool(msg.base_mode & 128)  # MAV_MODE_FLAG_SAFETY_ARMED = 128

                # Extract flight mode string if available via mavutil
                if hasattr(self._master, "flightmode"):
                    self.telemetry.flight_mode = str(self._master.flightmode).upper()

            elif msg_type == "GLOBAL_POSITION_INT":
                self.telemetry.lat = msg.lat / 1e7
                self.telemetry.lon = msg.lon / 1e7
                self.telemetry.altitude_m = msg.relative_alt / 1000.0
                if hasattr(msg, "hdg") and msg.hdg != 65535:
                    self.telemetry.heading_deg = msg.hdg / 100.0

            elif msg_type == "ATTITUDE":
                self.telemetry.roll_deg = math.degrees(msg.roll)
                self.telemetry.pitch_deg = math.degrees(msg.pitch)
                yaw_deg = math.degrees(msg.yaw)
                self.telemetry.heading_deg = (yaw_deg + 360.0) % 360.0

            elif msg_type == "SYS_STATUS":
                if hasattr(msg, "battery_remaining") and msg.battery_remaining >= 0:
                    self.telemetry.battery_pct = float(msg.battery_remaining)
                if hasattr(msg, "voltage_battery") and msg.voltage_battery != 65535:
                    self.telemetry.battery_voltage_v = msg.voltage_battery / 1000.0

            elif msg_type == "VFR_HUD":
                if hasattr(msg, "groundspeed"):
                    self.telemetry.groundspeed_mps = float(msg.groundspeed)
                if hasattr(msg, "climb"):
                    self.telemetry.climb_rate_mps = float(msg.climb)

            elif msg_type == "GPS_RAW_INT":
                if hasattr(msg, "satellites_visible"):
                    self.telemetry.satellites_visible = int(msg.satellites_visible)
                if hasattr(msg, "fix_type"):
                    self.telemetry.gps_fix_type = int(msg.fix_type)

        if self.on_telemetry:
            self.on_telemetry(self.get_telemetry())

    def _step_simulation(self) -> None:
        """Simulate realistic drone search trajectory over Wayanad disaster zone."""
        t = time.time() * 0.1
        radius_m = 120.0

        # Simulate lawnmower / circular search orbit
        offset_n = math.cos(t) * radius_m + math.sin(t * 0.2) * 30.0
        offset_e = math.sin(t) * radius_m + math.cos(t * 0.3) * 20.0

        meters_per_deg_lon = METERS_PER_DEG_LAT * math.cos(math.radians(self.config.base_lat))

        with self._lock:
            self.telemetry.connected = True
            self.telemetry.source = "simulated"
            self.telemetry.timestamp = time.time()
            self.telemetry.lat = self.config.base_lat + (offset_n / METERS_PER_DEG_LAT)
            self.telemetry.lon = self.config.base_lon + (offset_e / meters_per_deg_lon)
            self.telemetry.altitude_m = self.config.base_alt_m + math.sin(t * 0.5) * 1.5
            self.telemetry.heading_deg = (math.degrees(t + math.pi / 2) + 360) % 360
            self.telemetry.pitch_deg = math.sin(t * 0.8) * 3.0
            self.telemetry.roll_deg = math.cos(t * 0.8) * 4.0
            self.telemetry.groundspeed_mps = 11.5 + math.sin(t) * 1.5
            # Slow battery discharge: ~1% every 2 minutes
            self.telemetry.battery_pct = max(10.0, 98.0 - (time.time() % 7200) * (90.0 / 7200))
            self.telemetry.flight_mode = "AUTO_SEARCH"
            self.telemetry.armed = True
            self.telemetry.satellites_visible = 16
            self.telemetry.gps_fix_type = 3
            self.telemetry.packet_count += 1

        if self.on_telemetry:
            self.on_telemetry(self.get_telemetry())

    def _run_simulator(self) -> None:
        """Run pure simulation loop when pymavlink is absent."""
        interval = 1.0 / max(1.0, self.config.telemetry_rate_hz)
        while self._running:
            self._step_simulation()
            time.sleep(interval)

    def package_detection_alert(
        self,
        detection: DetectionResult,
        telemetry: Optional[DroneTelemetry] = None,
    ) -> Dict[str, Any]:
        """Package an edge detection event with telemetry and georeferencing."""
        telem = telemetry or self.get_telemetry()
        norm_cx, norm_cy = detection.center_normalized

        geo = project_pixel_to_gps(
            drone_lat=telem.lat,
            drone_lon=telem.lon,
            altitude_m=telem.altitude_m,
            heading_deg=telem.heading_deg,
            pitch_deg=telem.pitch_deg,
            norm_cx=norm_cx,
            norm_cy=norm_cy,
            hfov_deg=self.config.camera_hfov_deg,
            vfov_deg=self.config.camera_vfov_deg,
        )

        now = time.time()
        det_id = f"DET-{telem.drone_id}-{int(now * 1000) % 1000000}"

        alert_payload = {
            "alert_id": det_id,
            "drone_id": telem.drone_id,
            "timestamp": now,
            "target_type": detection.class_name,
            "confidence": detection.confidence,
            "priority": detection.priority,
            "bbox_normalized": list(detection.bbox_normalized),
            "inference_latency_ms": detection.latency_ms,
            "drone_telemetry": telem.to_dict(),
            "geo_estimate": geo.to_dict(),
        }

        return alert_payload

    def push_detection_alert(self, detection: DetectionResult) -> bool:
        """Send georeferenced detection alert to backend HTTP endpoint with cooldown."""
        now = time.time()
        key = f"{detection.class_name}_{detection.priority}"

        # Throttle duplicate alerts within cooldown window
        if key in self._alert_cooldowns and (now - self._alert_cooldowns[key] < self.config.alert_cooldown_s):
            return False

        self._alert_cooldowns[key] = now
        payload = self.package_detection_alert(detection)
        url = f"{self.config.backend_http_url.rstrip('/')}{self.config.alert_http_endpoint}"

        try:
            resp = requests.post(url, json=payload, timeout=self.config.network_timeout_s)
            if resp.status_code in (200, 201, 202):
                logger.info(f"Detection alert dispatched successfully: {payload['alert_id']} ({detection.class_name})")
                return True
            else:
                logger.warning(f"Backend responded with code {resp.status_code} for alert: {resp.text}")
                return False
        except Exception as e:
            logger.warning(f"Could not reach backend at {url} ({e}). Alert logged locally.")
            return False
