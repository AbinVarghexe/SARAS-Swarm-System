"""
SARAS Swarm Fault Tolerance & Health Monitor
Monitors drone heartbeats, detects lost communications or critical battery states,
and triggers dynamic orphaned sector reassignment to nearest active UAVs.
"""

from __future__ import annotations
import time
import uuid
from typing import Callable, Dict, List, Optional, Tuple

from swarm_core.telemetry_contract import (
    DroneStatus,
    DroneTelemetry,
    SectorModel,
    SectorStatus,
    SwarmAlert,
)
from swarm_core.coordination.allocator import haversine_distance, MarketAuctionAllocator


class SwarmHealthMonitor:
    """
    Real-time watchdog for the autonomous drone swarm.
    Tracks periodic heartbeats, detects dropout failures, handles critical battery
    failsafes, and immediately orchestrates dynamic sector reallocation.
    """

    def __init__(
        self,
        heartbeat_timeout_sec: float = 5.0,
        critical_battery_pct: float = 20.0,
        on_alert_callback: Optional[Callable[[SwarmAlert], None]] = None
    ):
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.critical_battery_pct = critical_battery_pct
        self.on_alert = on_alert_callback

        # Track last heartbeat timestamp per drone
        self.last_heartbeats: Dict[str, float] = {}
        # Track already alerted states to prevent spamming
        self.alerted_drones: Dict[str, str] = {}
        self.alerts_history: List[SwarmAlert] = []

    def record_heartbeat(self, drone_id: str, timestamp: Optional[float] = None) -> None:
        """Records a successful heartbeat receipt from a drone."""
        now = timestamp or time.time()
        self.last_heartbeats[drone_id] = now
        # If drone had previously recovered or joined
        if drone_id in self.alerted_drones and self.alerted_drones[drone_id] == DroneStatus.LOST:
            del self.alerted_drones[drone_id]
            alert = SwarmAlert(
                alert_id=str(uuid.uuid4())[:8],
                timestamp=now,
                level="INFO",
                drone_id=drone_id,
                message=f"Drone {drone_id} restored communication link and resumed heartbeat."
            )
            self._dispatch_alert(alert)

    def _dispatch_alert(self, alert: SwarmAlert) -> None:
        self.alerts_history.append(alert)
        if len(self.alerts_history) > 100:
            self.alerts_history.pop(0)
        if self.on_alert:
            self.on_alert(alert)

    def reassign_orphaned_sector(
        self,
        orphaned_sector: SectorModel,
        drones: Dict[str, DroneTelemetry],
        sectors: Dict[str, SectorModel]
    ) -> Optional[Tuple[str, str]]:
        """
        Finds the nearest active, capable UAV to take over the orphaned sector.
        Returns (selected_drone_id, sector_id) or None if no capable drone is free.
        """
        # Reset sector status to UNSEARCHED and remove dropped drone
        orphaned_sector.status = SectorStatus.UNSEARCHED
        orphaned_sector.assigned_drone_id = None

        # Eligible drones: active (SEARCHING or IDLE), not lost/fault, battery > 25%
        eligible_drones = [
            d for d in drones.values()
            if d.status in (DroneStatus.IDLE, DroneStatus.SEARCHING)
            and d.battery > 25.0
        ]

        if not eligible_drones:
            return None

        # Prefer idle drones first, then active searching drones by distance
        idle_drones = [d for d in eligible_drones if not d.current_sector_id or d.status == DroneStatus.IDLE]
        pool = idle_drones if idle_drones else eligible_drones

        # Pick drone with lowest cost (combination of distance and remaining battery)
        def score(d: DroneTelemetry) -> float:
            dist = haversine_distance(d.lat, d.lon, orphaned_sector.centroid[0], orphaned_sector.centroid[1])
            bat_factor = (100.0 - d.battery) / 50.0
            return dist * (1.0 + bat_factor)

        best_drone = min(pool, key=score)

        # If best_drone was searching another sector, free up that sector if needed or reassign
        old_sector_id = best_drone.current_sector_id
        if old_sector_id and old_sector_id in sectors and old_sector_id != orphaned_sector.sector_id:
            old_sec = sectors[old_sector_id]
            # If old sector is already nearly covered (>85%), let it finish, else requeue
            if old_sec.coverage_pct < 85.0:
                old_sec.status = SectorStatus.UNSEARCHED
                old_sec.assigned_drone_id = None

        # Assign orphan sector to best_drone
        orphaned_sector.status = SectorStatus.SEARCHING
        orphaned_sector.assigned_drone_id = best_drone.drone_id
        best_drone.current_sector_id = orphaned_sector.sector_id
        best_drone.status = DroneStatus.SEARCHING

        return (best_drone.drone_id, orphaned_sector.sector_id)

    def check_health(
        self,
        drones: Dict[str, DroneTelemetry],
        sectors: Dict[str, SectorModel],
        now: Optional[float] = None
    ) -> List[SwarmAlert]:
        """
        Executes a health cycle:
        1. Checks for missed heartbeats (> heartbeat_timeout_sec).
        2. Checks for critical battery depletion (< critical_battery_pct).
        3. Frees or reassigns any incomplete orphaned sectors.
        """
        current_time = now or time.time()
        new_alerts: List[SwarmAlert] = []

        for drone_id, drone in list(drones.items()):
            last_hb = self.last_heartbeats.get(drone_id, drone.timestamp)
            time_since_hb = current_time - last_hb

            # 1. Comms Lost / Dropout Check
            if time_since_hb > self.heartbeat_timeout_sec and drone.status != DroneStatus.LOST:
                drone.status = DroneStatus.LOST
                self.alerted_drones[drone_id] = DroneStatus.LOST

                alert = SwarmAlert(
                    alert_id=str(uuid.uuid4())[:8],
                    timestamp=current_time,
                    level="CRITICAL",
                    drone_id=drone_id,
                    message=f"DROPOUT DETECTED: {drone_id} comms lost ({time_since_hb:.1f}s > {self.heartbeat_timeout_sec}s threshold)."
                )
                self._dispatch_alert(alert)
                new_alerts.append(alert)

                # Handle orphaned sector
                if drone.current_sector_id and drone.current_sector_id in sectors:
                    sec = sectors[drone.current_sector_id]
                    if sec.status != SectorStatus.COVERED:
                        reassigned = self.reassign_orphaned_sector(sec, drones, sectors)
                        if reassigned:
                            takeover_drone, sec_id = reassigned
                            r_alert = SwarmAlert(
                                alert_id=str(uuid.uuid4())[:8],
                                timestamp=current_time,
                                level="WARNING",
                                drone_id=takeover_drone,
                                message=f"DYNAMIC REASSIGNMENT: Orphaned sector {sec_id} reassigned to nearest UAV {takeover_drone}."
                            )
                            self._dispatch_alert(r_alert)
                            new_alerts.append(r_alert)
                        else:
                            sec.status = SectorStatus.UNSEARCHED
                            sec.assigned_drone_id = None

                drone.current_sector_id = None

            # 2. Critical Battery Check
            elif drone.battery <= self.critical_battery_pct and drone.status not in (DroneStatus.RETURNING, DroneStatus.LOST, DroneStatus.FAULT):
                drone.status = DroneStatus.RETURNING
                self.alerted_drones[drone_id] = DroneStatus.RETURNING

                alert = SwarmAlert(
                    alert_id=str(uuid.uuid4())[:8],
                    timestamp=current_time,
                    level="CRITICAL",
                    drone_id=drone_id,
                    message=f"CRITICAL BATTERY: {drone_id} at {drone.battery:.1f}%. Triggered automatic RTH (Return-to-Home)."
                )
                self._dispatch_alert(alert)
                new_alerts.append(alert)

                # Reassign its sector if incomplete
                if drone.current_sector_id and drone.current_sector_id in sectors:
                    sec = sectors[drone.current_sector_id]
                    if sec.status != SectorStatus.COVERED:
                        reassigned = self.reassign_orphaned_sector(sec, drones, sectors)
                        if reassigned:
                            takeover_drone, sec_id = reassigned
                            r_alert = SwarmAlert(
                                alert_id=str(uuid.uuid4())[:8],
                                timestamp=current_time,
                                level="WARNING",
                                drone_id=takeover_drone,
                                message=f"BATTERY FAILSAFE REASSIGNMENT: Sector {sec_id} transferred to {takeover_drone}."
                            )
                            self._dispatch_alert(r_alert)
                            new_alerts.append(r_alert)
                        else:
                            sec.status = SectorStatus.UNSEARCHED
                            sec.assigned_drone_id = None

                drone.current_sector_id = None

        return new_alerts

    def get_system_health(self, drones: Dict[str, DroneTelemetry]) -> str:
        """Returns overall swarm health status: HEALTHY, DEGRADED, or CRITICAL."""
        if not drones:
            return "IDLE"

        lost_count = sum(1 for d in drones.values() if d.status == DroneStatus.LOST)
        crit_count = sum(1 for d in drones.values() if d.status in (DroneStatus.FAULT, DroneStatus.RETURNING))

        if lost_count >= 2 or (lost_count + crit_count) >= len(drones):
            return "CRITICAL"
        elif lost_count > 0 or crit_count > 0:
            return "DEGRADED"
        return "HEALTHY"
