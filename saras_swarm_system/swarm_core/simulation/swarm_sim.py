"""
SARAS Multi-UAV Swarm Simulator
Simulates N autonomous UAVs executing search sweeps across partitioned sectors,
monitoring battery drain, generating victim detections, and streaming real-time telemetry.
"""

from __future__ import annotations
import math
import random
import time
import uuid
from typing import Dict, List, Optional, Set, Tuple

from swarm_core.telemetry_contract import (
    DroneStatus,
    DroneTelemetry,
    DetectionEvent,
    DetectionStatus,
    SectorModel,
    SectorStatus,
    SwarmAlert,
    SwarmState,
)
from swarm_core.coordination.allocator import (
    haversine_distance,
    generate_sectors,
    MarketAuctionAllocator,
    GreedyDistanceAllocator,
    BaseSectorAllocator,
)
from swarm_core.fault_tolerance.monitor import SwarmHealthMonitor


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates navigation heading bearing in degrees from point 1 to point 2."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0


def generate_boustrophedon_path(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    sweeps: int = 4,
    margin_ratio: float = 0.15
) -> List[Tuple[float, float]]:
    """
    Generates a back-and-forth lawnmower (boustrophedon) waypoint path for thorough sector coverage.
    """
    lat_pad = (max_lat - min_lat) * margin_ratio
    lon_pad = (max_lon - min_lon) * margin_ratio

    eff_min_lat = min_lat + lat_pad
    eff_max_lat = max_lat - lat_pad
    eff_min_lon = min_lon + lon_pad
    eff_max_lon = max_lon - lon_pad

    lat_step = (eff_max_lat - eff_min_lat) / max(sweeps - 1, 1)
    waypoints: List[Tuple[float, float]] = []

    for i in range(sweeps):
        cur_lat = eff_max_lat - (i * lat_step)
        if i % 2 == 0:
            # West to East
            waypoints.append((cur_lat, eff_min_lon))
            waypoints.append((cur_lat, eff_max_lon))
        else:
            # East to West
            waypoints.append((cur_lat, eff_max_lon))
            waypoints.append((cur_lat, eff_min_lon))

    return waypoints


def generate_polygon_sweep_path(bounds: List[List[float]], sweeps: int = 4) -> List[Tuple[float, float]]:
    """
    Generates a boustrophedon sweep trajectory strictly clipped inside an arbitrary polygon boundary.
    Prevents drones from flying outside the exact custom polygon perimeters.
    """
    try:
        from shapely.geometry import Polygon, LineString

        poly_coords = [[float(pt[0]), float(pt[1])] for pt in bounds]
        if poly_coords[0] != poly_coords[-1]:
            poly_coords.append(poly_coords[0])
        poly = Polygon(poly_coords)
        if not poly.is_valid:
            poly = poly.buffer(0)

        min_lat, min_lon, max_lat, max_lon = poly.bounds
        if max_lat <= min_lat or (max_lat - min_lat) < 1e-6:
            return [tuple(poly.centroid.coords[0])]

        lat_step = (max_lat - min_lat) / (sweeps + 1)
        waypoints: List[Tuple[float, float]] = []

        for i in range(1, sweeps + 1):
            cur_lat = max_lat - i * lat_step
            scanline = LineString([(cur_lat, min_lon - 0.05), (cur_lat, max_lon + 0.05)])
            inter = poly.intersection(scanline)

            if inter.is_empty:
                continue
            elif inter.geom_type == "LineString":
                p1, p2 = inter.coords[0], inter.coords[-1]
                if i % 2 == 1:
                    waypoints.extend([(p1[0], p1[1]), (p2[0], p2[1])])
                else:
                    waypoints.extend([(p2[0], p2[1]), (p1[0], p1[1])])
            elif inter.geom_type == "MultiLineString":
                seg_pts = []
                for line in inter.geoms:
                    seg_pts.extend([(line.coords[0][0], line.coords[0][1]), (line.coords[-1][0], line.coords[-1][1])])
                if i % 2 == 0:
                    seg_pts.reverse()
                waypoints.extend(seg_pts)

        if not waypoints:
            waypoints = [tuple(poly.centroid.coords[0])]
        return waypoints
    except Exception as e:
        # Fallback to centroid if geometric intersection fails
        if bounds:
            lats = [float(p[0]) for p in bounds]
            lons = [float(p[1]) for p in bounds]
            return [(sum(lats) / len(lats), sum(lons) / len(lons))]
        return [(12.975, 77.595)]


class SimulatedDrone:
    """Represents a simulated multirotor UAV navigating waypoints and scanning for victims."""

    def __init__(
        self,
        drone_id: str,
        start_lat: float,
        start_lon: float,
        alt: float = 20.0,
        battery: float = 100.0,
        speed_mps: float = 10.0
    ):
        self.drone_id = drone_id
        self.home_lat = start_lat
        self.home_lon = start_lon
        self.lat = start_lat
        self.lon = start_lon
        self.alt = alt
        self.battery = battery
        self.speed_mps = speed_mps
        self.heading = 0.0
        self.status = DroneStatus.IDLE
        self.current_sector_id: Optional[str] = None
        self.waypoints: List[Tuple[float, float]] = []
        self.current_wp_index: int = 0
        self.total_sector_waypoints: int = 0
        self.mission_time: float = 0.0
        self.victims_detected: int = 0

        # Fault simulation flags
        self.is_disconnected: bool = False
        self.battery_drain_rate: float = 0.04  # ~0.04% per second (normal flight)

    def assign_sector(self, sector: SectorModel, sweeps: int = 4) -> None:
        """Assigns drone to search a sector and plans a sweep trajectory clipped strictly within polygon bounds."""
        self.current_sector_id = sector.sector_id
        self.status = DroneStatus.SEARCHING
        
        # Plan path strictly inside polygon if bounds are given
        if sector.bounds and len(sector.bounds) >= 3:
            self.waypoints = generate_polygon_sweep_path(sector.bounds, sweeps=sweeps)
        else:
            self.waypoints = generate_boustrophedon_path(
                min_lat=sector.min_lat,
                max_lat=sector.max_lat,
                min_lon=sector.min_lon,
                max_lon=sector.max_lon,
                sweeps=sweeps
            )
        self.current_wp_index = 0
        self.total_sector_waypoints = len(self.waypoints)


    def return_to_home(self) -> None:
        """Commands drone to return to staging launch pad coordinates where it was sent from."""
        dist_home = haversine_distance(self.lat, self.lon, self.home_lat, self.home_lon)
        if dist_home > 4.0:
            self.status = DroneStatus.RETURNING
            self.current_sector_id = None
            self.waypoints = [(self.home_lat, self.home_lon)]
            self.current_wp_index = 0
            self.total_sector_waypoints = 1
        else:
            self.status = DroneStatus.IDLE
            self.current_sector_id = None
            self.waypoints = []
            self.lat = self.home_lat
            self.lon = self.home_lon

    def step(self, dt: float) -> Tuple[bool, float]:
        """
        Advances the drone physics by dt seconds.
        Returns (is_sector_completed, sector_progress_pct).
        """
        if self.is_disconnected:
            # Comms cut: drone maintains position / fails
            return False, 0.0

        self.mission_time += dt

        # Battery discharge: only drain when actively flying (SEARCHING or RETURNING)
        if self.status in (DroneStatus.SEARCHING, DroneStatus.RETURNING):
            drain = self.battery_drain_rate * dt
            if self.status == DroneStatus.SEARCHING:
                drain *= 1.25  # Sensor scanning and maneuvering consumes extra power
            self.battery = max(0.0, self.battery - drain)

        # If battery is critical and not returning, switch to RETURNING
        if self.battery <= 20.0 and self.status != DroneStatus.RETURNING:
            self.return_to_home()

        # Movement physics towards target waypoint
        sector_completed = False
        progress_pct = 0.0

        if self.waypoints and self.current_wp_index < len(self.waypoints):
            target_lat, target_lon = self.waypoints[self.current_wp_index]
            dist_to_wp = haversine_distance(self.lat, self.lon, target_lat, target_lon)

            # Calculate heading towards target
            self.heading = calculate_bearing(self.lat, self.lon, target_lat, target_lon)

            # Move towards waypoint
            travel_dist = self.speed_mps * dt
            if travel_dist >= dist_to_wp:
                # Reached waypoint
                self.lat = target_lat
                self.lon = target_lon
                self.current_wp_index += 1
                if self.current_wp_index >= len(self.waypoints):
                    # Finished all sector waypoints
                    if self.status == DroneStatus.SEARCHING:
                        sector_completed = True
                        self.status = DroneStatus.IDLE
                        self.waypoints = []
                    elif self.status == DroneStatus.RETURNING:
                        self.status = DroneStatus.IDLE
                        self.waypoints = []
                        self.lat = self.home_lat
                        self.lon = self.home_lon
            else:
                # Interpolate coordinate along bearing
                ratio = travel_dist / dist_to_wp
                self.lat += (target_lat - self.lat) * ratio
                self.lon += (target_lon - self.lon) * ratio

            if self.total_sector_waypoints > 0:
                progress_pct = min(100.0, (self.current_wp_index / self.total_sector_waypoints) * 100.0)

        return sector_completed, progress_pct

    def to_telemetry(self) -> DroneTelemetry:
        target_wp = None
        if self.waypoints and self.current_wp_index < len(self.waypoints):
            target_wp = list(self.waypoints[self.current_wp_index])

        return DroneTelemetry(
            drone_id=self.drone_id,
            timestamp=time.time(),
            lat=self.lat,
            lon=self.lon,
            alt=self.alt,
            battery=round(self.battery, 1),
            speed=self.speed_mps if self.waypoints else 0.0,
            heading=round(self.heading, 1),
            status=self.status,
            current_sector_id=self.current_sector_id,
            target_waypoint=target_wp,
            mission_time=round(self.mission_time, 1),
            victims_detected=self.victims_detected
        )


class SwarmSimulator:
    """
    Main Multi-UAV Swarm Simulator orchestrator.
    Manages N drones, sector coverage, victim placement, fault injection,
    and automatic sector allocation.
    """

    def __init__(
        self,
        num_drones: int = 4,
        rows: int = 3,
        cols: int = 4,
        min_lat: float = 12.9710,
        max_lat: float = 12.9790,
        min_lon: float = 77.5910,
        max_lon: float = 77.6030,
        allocator_type: str = "AUCTION",
        auto_generate_sectors: bool = False
    ):
        self.num_drones = num_drones
        self.rows = rows
        self.cols = cols
        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lon = min_lon
        self.max_lon = max_lon
        self.allocator_type = allocator_type

        # Initialize sectors: empty by default until operator plots custom regions
        if auto_generate_sectors:
            self.sectors = generate_sectors(
                min_lat=min_lat,
                max_lat=max_lat,
                min_lon=min_lon,
                max_lon=max_lon,
                rows=rows,
                cols=cols
            )
        else:
            self.sectors = {}

        # Allocator
        self.allocators: Dict[str, BaseSectorAllocator] = {
            "AUCTION": MarketAuctionAllocator(),
            "GREEDY": GreedyDistanceAllocator()
        }

        # Health monitor
        self.health_monitor = SwarmHealthMonitor()

        # Drones
        self.drones: Dict[str, SimulatedDrone] = {}
        self._init_drones()

        # Ground truth disaster victims seeded in realistic zones
        self.ground_truth_victims: List[Dict] = self._seed_victims()
        self.discovered_victim_ids: Set[str] = set()
        self.detections: List[DetectionEvent] = []

        # Detection radius (meters) for drone sensor footprint
        self.detection_radius_m: float = 38.0

        # Mission stats
        self.start_time: float = time.time()
        self.is_running: bool = True

    def _init_drones(self) -> None:
        """Initializes N drones spread around disaster staging base."""
        base_lat = self.min_lat - 0.0015
        base_lon = (self.min_lon + self.max_lon) / 2.0

        for i in range(1, self.num_drones + 1):
            drone_id = f"Drone-{i}"
            # Staging offsets
            offset_lat = base_lat - (i * 0.0004)
            offset_lon = base_lon + ((i - (self.num_drones + 1) / 2) * 0.0008)
            drone = SimulatedDrone(
                drone_id=drone_id,
                start_lat=offset_lat,
                start_lon=offset_lon,
                battery=random.uniform(94.0, 100.0),
                speed_mps=random.uniform(9.0, 11.5)
            )
            self.drones[drone_id] = drone
            self.health_monitor.record_heartbeat(drone_id)

    def _seed_victims(self) -> List[Dict]:
        """Pre-seeds realistic disaster victims within sector bounds."""
        lat_span = self.max_lat - self.min_lat
        lon_span = self.max_lon - self.min_lon

        victims = [
            {
                "id": "VIC-101",
                "lat": self.min_lat + lat_span * 0.42,
                "lon": self.min_lon + lon_span * 0.35,
                "confidence": 0.94,
                "thermal_signature": 34.2,  # Hypothermic in water
                "environment_tags": ["flood", "hypothermia", "swiftwater"],
                "notes": "Victim clinging to submerged structure. Moderate current."
            },
            {
                "id": "VIC-102",
                "lat": self.min_lat + lat_span * 0.78,
                "lon": self.min_lon + lon_span * 0.22,
                "confidence": 0.91,
                "thermal_signature": 38.6,  # Heat stress near fire
                "environment_tags": ["debris", "fire_proximity", "unresponsive"],
                "notes": "Severe structural collapse. Fire hazard 20m East."
            },
            {
                "id": "VIC-103",
                "lat": self.min_lat + lat_span * 0.65,
                "lon": self.min_lon + lon_span * 0.82,
                "confidence": 0.88,
                "thermal_signature": 36.8,  # Normal temp, conscious
                "environment_tags": ["landslide", "conscious", "pinned"],
                "notes": "Lower limb entrapped under mudflow boulder. Conscious and waving."
            },
            {
                "id": "VIC-104",
                "lat": self.min_lat + lat_span * 0.25,
                "lon": self.min_lon + lon_span * 0.68,
                "confidence": 0.96,
                "thermal_signature": 36.2,
                "environment_tags": ["isolated", "roof_stranded"],
                "notes": "Family of 2 stranded on residential roof surrounded by 1.5m flood."
            }
        ]
        return victims

    def seed_victims_in_sector(self, sector: SectorModel) -> None:
        """Ensures at least 1-2 realistic disaster victims exist within a newly plotted search zone."""
        has_victim = any(
            sector.min_lat <= v["lat"] <= sector.max_lat and sector.min_lon <= v["lon"] <= sector.max_lon
            for v in self.ground_truth_victims
        )
        if not has_victim:
            center_lat, center_lon = sector.centroid[0], sector.centroid[1]
            vic_id = f"VIC-{len(self.ground_truth_victims) + 101}"
            tags_pool = [
                (["flood", "hypothermia", "trapped"], "Victim stranded on elevated debris surrounded by water."),
                (["landslide", "conscious", "pinned"], "Subject pinned under debris branch. Signaling with arms."),
                (["debris", "injured", "fracture"], "Victim with limb injury requesting emergency extraction.")
            ]
            tags, notes = random.choice(tags_pool)
            self.ground_truth_victims.append({
                "id": vic_id,
                "lat": center_lat + random.uniform(-0.0003, 0.0003),
                "lon": center_lon + random.uniform(-0.0003, 0.0003),
                "confidence": round(random.uniform(0.88, 0.96), 2),
                "thermal_signature": round(random.uniform(34.5, 37.2), 1),
                "environment_tags": tags,
                "notes": notes
            })

    def set_allocator(self, policy: str) -> None:
        """Switches between AUCTION and GREEDY allocation policies."""
        if policy in self.allocators:
            self.allocator_type = policy

    def inject_dropout(self, drone_id: str) -> bool:
        """Simulates immediate communication dropout or drone crash."""
        if drone_id in self.drones:
            drone = self.drones[drone_id]
            drone.is_disconnected = True
            drone.status = DroneStatus.LOST
            return True
        return False

    def inject_battery_drain(self, drone_id: str, target_pct: float = 12.0) -> bool:
        """Simulates critical battery drain triggering failsafe RTH."""
        if drone_id in self.drones:
            self.drones[drone_id].battery = target_pct
            return True
        return False

    def set_drone_count(self, count: int, reset_mission: bool = False) -> Dict[str, Any]:
        """
        Dynamically adjusts the number of drones in the swarm fleet (1 to 16).
        Can preserve active searches or reset all drones to staged base positions.
        """
        count = max(1, min(16, int(count)))
        base_lat = self.min_lat - 0.0015
        base_lon = (self.min_lon + self.max_lon) / 2.0

        if reset_mission:
            for s in self.sectors.values():
                s.assigned_drone_id = None
                if s.status == SectorStatus.SEARCHING:
                    s.status = SectorStatus.UNSEARCHED
                    s.coverage_pct = 0.0
            self.drones.clear()
            self.num_drones = count
            self._init_drones()
            return {"status": "ok", "drone_count": self.num_drones, "action": "reinitialized"}

        if count > self.num_drones:
            # Scale up: Add new drones staged at base
            for i in range(self.num_drones + 1, count + 1):
                drone_id = f"Drone-{i}"
                offset_lat = base_lat - (i * 0.0004)
                offset_lon = base_lon + ((i - (count + 1) / 2) * 0.0008)
                drone = SimulatedDrone(
                    drone_id=drone_id,
                    start_lat=offset_lat,
                    start_lon=offset_lon,
                    battery=random.uniform(96.0, 100.0),
                    speed_mps=random.uniform(9.0, 11.5)
                )
                self.drones[drone_id] = drone
                self.health_monitor.record_heartbeat(drone_id)
            self.num_drones = count
        elif count < self.num_drones:
            # Scale down: Gracefully decommission tail drones
            for i in range(self.num_drones, count, -1):
                drone_id = f"Drone-{i}"
                if drone_id in self.drones:
                    d = self.drones.pop(drone_id)
                    if d.current_sector_id and d.current_sector_id in self.sectors:
                        sec = self.sectors[d.current_sector_id]
                        sec.assigned_drone_id = None
                        if sec.status == SectorStatus.SEARCHING:
                            sec.status = SectorStatus.UNSEARCHED
            self.num_drones = count

        return {"status": "ok", "drone_count": self.num_drones, "action": "scaled"}

    def restore_drone(self, drone_id: str) -> bool:
        """Brings a drone back online with fresh battery."""
        if drone_id in self.drones:
            drone = self.drones[drone_id]
            drone.is_disconnected = False
            drone.battery = 98.0
            drone.status = DroneStatus.IDLE
            self.health_monitor.record_heartbeat(drone_id)
            return True
        return False

    def step(self, dt: float = 0.5) -> SwarmState:
        """
        Main simulation step loop:
        1. Advances UAV physics and sector waypoint navigation.
        2. Heartbeat tracking and fault-tolerance monitoring.
        3. Dynamic sector allocation for idle drones.
        4. Victim detection checks.
        5. Computes overall swarm progress and returns current SwarmState.
        """
        telemetries: Dict[str, DroneTelemetry] = {}

        # 1. Step drones
        for drone_id, drone in self.drones.items():
            if not drone.is_disconnected:
                # Record regular heartbeat
                self.health_monitor.record_heartbeat(drone_id)

            was_returning = (drone.status == DroneStatus.RETURNING)
            completed, progress_pct = drone.step(dt)
            sec_id = drone.current_sector_id

            if sec_id and sec_id in self.sectors:
                sector = self.sectors[sec_id]
                if completed:
                    sector.status = SectorStatus.COVERED
                    sector.coverage_pct = 100.0
                    sector.assigned_drone_id = None
                    drone.current_sector_id = None
                    alert = SwarmAlert(
                        alert_id=f"ALT-COMP-{int(time.time()*1000)%1000000}",
                        timestamp=time.time(),
                        level="INFO",
                        drone_id=drone.drone_id,
                        message=f"SECTOR COMPLETED: {drone.drone_id} completed search of '{sector.name}' ({sector.sector_id}). Checking next assignment..."
                    )
                    self.health_monitor._dispatch_alert(alert)
                else:
                    sector.status = SectorStatus.SEARCHING
                    sector.coverage_pct = max(sector.coverage_pct, progress_pct)
                    sector.last_searched_at = time.time()

            if was_returning and drone.status == DroneStatus.IDLE:
                alert = SwarmAlert(
                    alert_id=f"ALT-HOME-{int(time.time()*1000)%1000000}",
                    timestamp=time.time(),
                    level="INFO",
                    drone_id=drone.drone_id,
                    message=f"RECOVERY COMPLETE: {drone.drone_id} safely landed back at staging launch pad."
                )
                self.health_monitor._dispatch_alert(alert)

            telemetries[drone_id] = drone.to_telemetry()

        # 2. Run Fault-Tolerance Monitor
        self.health_monitor.check_health(telemetries, self.sectors)

        # 3. Dynamic Sector Allocation for available idle or returning drones
        allocator = self.allocators.get(self.allocator_type, self.allocators["AUCTION"])
        new_assignments = allocator.allocate(telemetries, self.sectors)

        for d_id, s_id in new_assignments.items():
            if d_id in self.drones and s_id in self.sectors:
                drone = self.drones[d_id]
                sector = self.sectors[s_id]
                drone.assign_sector(sector)
                sector.status = SectorStatus.SEARCHING
                sector.assigned_drone_id = d_id
                telemetries[d_id] = drone.to_telemetry()
                alert = SwarmAlert(
                    alert_id=f"ALT-ALLOC-{int(time.time()*1000)%1000000}",
                    timestamp=time.time(),
                    level="INFO",
                    drone_id=drone.drone_id,
                    message=f"NEXT SECTOR ASSIGNED: {drone.drone_id} dispatched to search '{sector.name}' ({sector.sector_id})."
                )
                self.health_monitor._dispatch_alert(alert)

        # 4. Check for completed drones with no next sector: Command Return-To-Home
        for drone_id, drone in self.drones.items():
            if drone.is_disconnected or drone.status in (DroneStatus.LOST, DroneStatus.RETURNING):
                continue

            # If drone is IDLE (completed its sector and not assigned to another sector)
            if drone.status == DroneStatus.IDLE and not drone.current_sector_id:
                has_unsearched = any(
                    s.status == SectorStatus.UNSEARCHED and not s.assigned_drone_id
                    for s in self.sectors.values()
                )
                dist_from_home = haversine_distance(drone.lat, drone.lon, drone.home_lat, drone.home_lon)
                # If no next sector is available and drone is away from launch staging pad (> 5.0m)
                if not has_unsearched and dist_from_home > 5.0:
                    drone.return_to_home()
                    telemetries[drone_id] = drone.to_telemetry()
                    alert = SwarmAlert(
                        alert_id=f"ALT-RTH-{int(time.time()*1000)%1000000}",
                        timestamp=time.time(),
                        level="INFO",
                        drone_id=drone.drone_id,
                        message=f"MISSION FINISHED: No further unsearched sectors. {drone.drone_id} returning to launch pad."
                    )
                    self.health_monitor._dispatch_alert(alert)

        # 5. Check for victim detections
        for drone_id, drone in self.drones.items():
            if drone.is_disconnected or drone.status != DroneStatus.SEARCHING:
                continue

            for vic in self.ground_truth_victims:
                if vic["id"] in self.discovered_victim_ids:
                    continue

                dist = haversine_distance(drone.lat, drone.lon, vic["lat"], vic["lon"])
                if dist <= self.detection_radius_m:
                    # Detected victim!
                    self.discovered_victim_ids.add(vic["id"])
                    drone.victims_detected += 1

                    detection = DetectionEvent(
                        detection_id=f"DET-{str(uuid.uuid4())[:6].upper()}",
                        drone_id=drone.drone_id,
                        timestamp=time.time(),
                        lat=vic["lat"],
                        lon=vic["lon"],
                        confidence=vic["confidence"],
                        label="victim",
                        thermal_signature=vic.get("thermal_signature"),
                        environment_tags=vic.get("environment_tags", []),
                        status=DetectionStatus.PENDING,
                        notes=vic.get("notes")
                    )
                    self.detections.append(detection)

                    # Alert
                    alert = SwarmAlert(
                        alert_id=str(uuid.uuid4())[:8],
                        timestamp=time.time(),
                        level="WARNING",
                        drone_id=drone.drone_id,
                        message=f"VICTIM DETECTED: {drone.drone_id} located human subject at [{vic['lat']:.5f}, {vic['lon']:.5f}]."
                    )
                    self.health_monitor._dispatch_alert(alert)

        # 5. Compute overall coverage percentage
        covered_count = sum(1 for s in self.sectors.values() if s.status == SectorStatus.COVERED)
        searching_coverage = sum(s.coverage_pct for s in self.sectors.values() if s.status == SectorStatus.SEARCHING)
        total_sectors = len(self.sectors)
        total_pct = (covered_count * 100.0 + searching_coverage) / max(total_sectors, 1)

        system_health = self.health_monitor.get_system_health(telemetries)

        return SwarmState(
            timestamp=time.time(),
            active_drones=telemetries,
            sectors=self.sectors,
            total_coverage_pct=round(min(100.0, total_pct), 1),
            active_detections=self.detections,
            alerts=self.health_monitor.alerts_history[-20:],
            system_health=system_health,
            allocation_policy=self.allocator_type
        )

    def relocate_base(self, lat: float, lon: float) -> None:
        """
        Relocates the GCS staging launch pad to specific coordinates (e.g. live GPS from browser).
        Updates home positions of all drones and repositions staged/idle drones around new base.
        """
        self.min_lat = lat - 0.005
        self.max_lat = lat + 0.005
        self.min_lon = lon - 0.005
        self.max_lon = lon + 0.005

        n = len(self.drones)
        for i, (d_id, drone) in enumerate(self.drones.items(), start=1):
            offset_lat = lat - (i * 0.0003)
            offset_lon = lon + ((i - (n + 1) / 2) * 0.0006)
            drone.home_lat = offset_lat
            drone.home_lon = offset_lon
            # If drone is currently idle and not on active search, position at launch pad
            if (drone.status == DroneStatus.IDLE or drone.status == DroneStatus.RETURNING) and not drone.current_sector_id:
                drone.lat = offset_lat
                drone.lon = offset_lon
                drone.waypoints = []
                drone.status = DroneStatus.IDLE
