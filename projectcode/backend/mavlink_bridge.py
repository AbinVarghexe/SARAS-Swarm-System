"""MAVLink Bridge for SARAS Swarm System.

Listens for MAVLink telemetry from Mission Planner (UDP 14550 / TCP 5760)
or directly from a Pixhawk/SITL instance via pymavlink.
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("saras.mavlink")


class MavlinkBridge:
    def __init__(
        self,
        connection_str: str = "udpin:127.0.0.1:14550",
        on_telemetry_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.connection_str = connection_str
        self.on_telemetry = on_telemetry_callback
        self.is_connected = False
        self.is_running = False
        self.last_heartbeat = 0.0
        self.latest_telemetry: Dict[str, Any] = {
            "connected": False,
            "source": "standby",
            "lat": 11.5360,
            "lon": 76.1390,
            "altitude": 35.0,
            "heading": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "battery": 98.0,
            "health": "active",
            "packet_count": 0,
        }
        self._master = None
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self.is_running = True
        self._task = asyncio.create_task(self._listener_loop())
        logger.info(f"MAVLink Bridge initialized on {self.connection_str}")

    async def stop(self) -> None:
        self.is_running = False
        if self._task:
            self._task.cancel()
        if self._master:
            try:
                self._master.close()
            except Exception:
                pass
        self.is_connected = False
        self.latest_telemetry["connected"] = False

    async def _listener_loop(self) -> None:
        try:
            from pymavlink import mavutil
        except ImportError:
            logger.warning("pymavlink not installed. MAVLink bridge operating in emulation mode.")
            return

        while self.is_running:
            try:
                if self._master is None:
                    # Non-blocking attempt to connect
                    self._master = mavutil.mavlink_connection(
                        self.connection_str,
                        autoreconnect=True,
                        source_system=255,
                    )
                    logger.info(f"Connecting to MAVLink on {self.connection_str}...")

                # Receive messages without blocking asyncio event loop
                msg = await asyncio.to_thread(self._master.recv_match, blocking=False)
                if msg is not None:
                    self._handle_message(msg)
                else:
                    # Check connection timeout (3 seconds without heartbeat)
                    if self.is_connected and (time.time() - self.last_heartbeat > 3.5):
                        self.is_connected = False
                        self.latest_telemetry["connected"] = False
                    await asyncio.sleep(0.02)
            except Exception as e:
                self.is_connected = False
                self.latest_telemetry["connected"] = False
                await asyncio.sleep(1.0)

    def _handle_message(self, msg: Any) -> None:
        msg_type = msg.get_type()

        if msg_type == "HEARTBEAT":
            self.last_heartbeat = time.time()
            self.is_connected = True
            self.latest_telemetry["connected"] = True
            self.latest_telemetry["source"] = "mavlink"
            self.latest_telemetry["packet_count"] += 1

        elif msg_type == "GLOBAL_POSITION_INT":
            # Lat/lon in 1e7 degrees, relative_alt in mm
            lat = msg.lat / 1e7
            lon = msg.lon / 1e7
            alt_m = msg.relative_alt / 1000.0
            hdg_deg = msg.hdg / 100.0 if hasattr(msg, "hdg") else self.latest_telemetry["heading"]

            self.latest_telemetry["lat"] = round(lat, 6)
            self.latest_telemetry["lon"] = round(lon, 6)
            self.latest_telemetry["altitude"] = round(alt_m, 1)
            self.latest_telemetry["heading"] = round(hdg_deg, 1)

            if self.on_telemetry:
                self.on_telemetry(self.latest_telemetry)

        elif msg_type == "ATTITUDE":
            # Pitch and roll in radians
            self.latest_telemetry["pitch"] = round(math.degrees(msg.pitch), 1)
            self.latest_telemetry["roll"] = round(math.degrees(msg.roll), 1)
            self.latest_telemetry["heading"] = round((math.degrees(msg.yaw) + 360) % 360, 1)

            if self.on_telemetry:
                self.on_telemetry(self.latest_telemetry)

        elif msg_type == "SYS_STATUS":
            # battery_remaining is in percentage (0 to 100)
            if hasattr(msg, "battery_remaining") and msg.battery_remaining != -1:
                self.latest_telemetry["battery"] = float(msg.battery_remaining)
                if self.on_telemetry:
                    self.on_telemetry(self.latest_telemetry)
