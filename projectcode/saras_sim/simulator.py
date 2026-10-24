from __future__ import annotations

import math
import random
from math import atan2, degrees, hypot
from typing import Any, Dict, List, Optional, Tuple

from .agents import KnowledgeAgent, RescueAgent
from .allocator import SectorAllocator
from .config import SimulationConfig
from .models import (
    Drone,
    HazardZone,
    RescueRecommendation,
    Sector,
    SimulationReport,
    Victim,
    local_to_gps,
)


class SwarmSimulation:
    """Enterprise-grade multi-drone SAR simulation with dual-mode operations and disaster hazards."""

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        self.random = random.Random(42)
        self.sectors: List[Sector] = []
        self.drones: List[Drone] = []
        self.victims: List[Victim] = []
        self.hazards: List[HazardZone] = []
        self.rescue_agent = RescueAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.mode: str = self.config.mode  # "pure_sim" or "hybrid_real"
        self.step_count: int = 0
        self.metrics: Dict[str, Any] = {
            "coverage_ratio": 0.0,
            "victim_detections": 0,
            "failed_drones": 0,
            "reassigned_sectors": 0,
            "total_steps": 0,
            "active_hazards": 0,
        }

    def initialize(self) -> None:
        self.step_count = 0
        self.sectors = self._create_sectors()
        self.drones = self._create_drones(self.config.drone_count)
        self.victims = self._create_victims()
        self.hazards = self._create_hazards()
        self.metrics["active_hazards"] = len(self.hazards)
        self._apply_mode_settings()
        self._assign_initial_sectors()

    def set_mode(self, mode: str) -> None:
        """Switch between 'pure_sim' (hazardous simulation) and 'hybrid_real' (1 real drone + N virtual)."""
        self.mode = mode
        self.config.mode = mode
        self._apply_mode_settings()

    def _apply_mode_settings(self) -> None:
        if not self.drones:
            return
        if self.mode == "hybrid_real":
            # Drone 1 is the physical drone
            for idx, drone in enumerate(self.drones):
                if idx == 0:
                    drone.is_physical = True
                    drone.video_feed_active = True
                    if drone.telemetry_source == "sim":
                        drone.telemetry_source = "emulated"
                else:
                    drone.is_physical = False
                    drone.video_feed_active = False
                    drone.telemetry_source = "sim"
        else:
            # Pure Simulation: All drones are virtual
            for drone in self.drones:
                drone.is_physical = False
                drone.video_feed_active = False
                drone.telemetry_source = "sim"

    def set_drone_count(self, new_count: int) -> None:
        """Dynamically adjust swarm fleet size (1 to 10) and reallocate sectors."""
        new_count = max(1, min(12, new_count))
        current_count = len(self.drones)
        if new_count == current_count:
            return

        if new_count > current_count:
            # Add drones
            for i in range(current_count, new_count):
                drone_id = f"D{i + 1}"
                angle = (2 * math.pi * i) / new_count
                orbit_r = min(self.config.arena_width, self.config.arena_height) * 0.15
                x = self.config.arena_width * 0.5 + orbit_r * math.cos(angle)
                y = self.config.arena_height * 0.5 + orbit_r * math.sin(angle)
                new_drone = Drone(
                    drone_id=drone_id,
                    x=x,
                    y=y,
                    battery=95.0,
                    health="active",
                    altitude=35.0,
                    telemetry_source="sim",
                )
                self.drones.append(new_drone)
        else:
            # Remove excess drones (from the end, keeping D1)
            removed = self.drones[new_count:]
            self.drones = self.drones[:new_count]
            # Release sectors held by removed drones
            for d in removed:
                if d.sector_id:
                    s = self._get_sector(d.sector_id)
                    if s and not s.covered:
                        s.status = "available"
                        s.assigned_to = None

        self.config.drone_count = new_count
        self._apply_mode_settings()
        # Trigger sector re-allocation for unassigned/uncovered sectors
        self.reallocate_sectors()

    def reallocate_sectors(self) -> None:
        """Re-run auction allocation on all available sectors."""
        allocator = SectorAllocator(self.sectors, self.drones)
        allocator.assign()

    def _create_sectors(self) -> List[Sector]:
        sectors: List[Sector] = []
        grid_w = self.config.arena_width / self.config.sector_cols
        grid_h = self.config.arena_height / self.config.sector_rows
        for row in range(self.config.sector_rows):
            for col in range(self.config.sector_cols):
                x = (col + 0.5) * grid_w
                y = (row + 0.5) * grid_h
                sector_id = f"S{row + 1}{col + 1}"
                sectors.append(Sector(sector_id=sector_id, x=x, y=y, width=grid_w, height=grid_h))
        return sectors

    def _create_drones(self, count: int) -> List[Drone]:
        drones: List[Drone] = []
        for index in range(count):
            angle = (2 * math.pi * index) / max(count, 1)
            orbit_radius = min(self.config.arena_width, self.config.arena_height) * 0.12
            x = self.config.arena_width * 0.5 + orbit_radius * math.cos(angle)
            y = self.config.arena_height * 0.5 + orbit_radius * math.sin(angle)
            drones.append(
                Drone(
                    drone_id=f"D{index + 1}",
                    x=x,
                    y=y,
                    battery=98.0,
                    altitude=35.0 + (index * 2.0),
                    speed=self.config.drone_speed,
                )
            )
        return drones

    def _create_victims(self) -> List[Victim]:
        victims: List[Victim] = []
        for index in range(self.config.victim_count):
            x = self.random.uniform(60, self.config.arena_width - 60)
            y = self.random.uniform(60, self.config.arena_height - 60)
            severity = ["critical", "high", "medium", "low"][index % 4]
            victims.append(
                Victim(
                    victim_id=f"V{index + 1}",
                    x=x,
                    y=y,
                    severity=severity,
                    rescue_priority=self._priority_value(severity),
                )
            )
        return victims

    def _create_hazards(self) -> List[HazardZone]:
        """Disaster hazards modeled after Kerala Landslide (debris, thick smoke, thermal hotspot, wind)."""
        w, h = self.config.arena_width, self.config.arena_height
        return [
            HazardZone(
                hazard_id="H1-DEBRIS",
                hazard_type="landslide_debris",
                x=w * 0.35,
                y=h * 0.40,
                radius=160.0,
                severity=0.85,
                description="Chooralmala Primary Mudflow & Boulder Debris Field",
            ),
            HazardZone(
                hazard_id="H2-SMOKE",
                hazard_type="smoke_plume",
                x=w * 0.65,
                y=h * 0.30,
                radius=130.0,
                severity=0.75,
                description="Dense Smoke Plume & Reduced Visibility Zone",
            ),
            HazardZone(
                hazard_id="H3-WIND",
                hazard_type="wind_shear",
                x=w * 0.70,
                y=h * 0.75,
                radius=180.0,
                severity=0.60,
                wind_vector=(6.5, -4.0),
                description="Western Ghats Ridge Wind Shear (12 m/s Gusts)",
            ),
            HazardZone(
                hazard_id="H4-THERMAL",
                hazard_type="fire_hotspot",
                x=w * 0.25,
                y=h * 0.75,
                radius=110.0,
                severity=0.70,
                description="Thermal Hotspot / Collapsed Structure Hazard",
            ),
        ]

    def _assign_initial_sectors(self) -> None:
        allocator = SectorAllocator(self.sectors, self.drones)
        allocator.assign()

    def _priority_value(self, severity: str) -> int:
        mapping = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        return mapping.get(severity.lower(), 1)

    def _advance_drone(self, drone: Drone) -> None:
        if drone.health not in ("active", "returning"):
            return

        # If physical drone has live external MAVLink telemetry, flight coords are externally bound
        if drone.is_physical and drone.telemetry_source == "mavlink":
            return

        target: Optional[Tuple[float, float]] = None
        if drone.health == "returning":
            target = self.config.rescue_point
        elif drone.sector_id is not None:
            target = self._sector_center(drone.sector_id)

        if target is None:
            return

        dist = hypot(target[0] - drone.x, target[1] - drone.y)
        if dist > 3.0:
            step_x = (target[0] - drone.x) / dist
            step_y = (target[1] - drone.y) / dist

            # Heading calculation (0 = North, 90 = East, 180 = South, 270 = West)
            target_heading = (degrees(atan2(step_x, -step_y)) + 360) % 360
            angle_diff = (target_heading - drone.heading + 180) % 360 - 180
            drone.heading = (drone.heading + angle_diff * 0.35 + 360) % 360
            drone.roll = max(-25.0, min(25.0, angle_diff * 0.8))
            drone.pitch = -4.0  # slight forward pitch while cruising

            # Check environmental hazard effects
            drain_rate = self.config.battery_drain_per_step
            drift_x, drift_y = 0.0, 0.0

            for hazard in self.hazards:
                if hazard.contains(drone.x, drone.y):
                    if hazard.hazard_type == "wind_shear":
                        drift_x += hazard.wind_vector[0] * 0.25
                        drift_y += hazard.wind_vector[1] * 0.25
                        drain_rate *= 1.4
                    elif hazard.hazard_type in ("fire_hotspot", "smoke_plume"):
                        drain_rate *= 1.3

            actual_speed = self.config.drone_speed * 0.25
            drone.x += (step_x * actual_speed) + drift_x
            drone.y += (step_y * actual_speed) + drift_y
            drone.battery = max(0.0, drone.battery - (drain_rate * 0.15))
        else:
            drone.pitch = 0.0
            drone.roll = 0.0

        if drone.battery <= 20.0 and drone.health == "active":
            drone.health = "returning"
            self._reassign_after_failure(drone)

    def _reassign_after_failure(self, drone: Drone) -> None:
        sector = self._get_sector(drone.sector_id)
        if sector is not None:
            sector.status = "available"
            sector.assigned_to = None
            sector.covered = False

        candidate = self._find_replacement(drone)
        if candidate is not None and sector is not None:
            candidate.sector_id = sector.sector_id
            sector.assigned_to = candidate.drone_id
            sector.status = "assigned"
            self.metrics["reassigned_sectors"] += 1

    def _find_replacement(self, drone: Drone) -> Optional[Drone]:
        active = [c for c in self.drones if c.drone_id != drone.drone_id and c.health == "active"]
        if not active:
            return None
        return min(active, key=lambda candidate: candidate.distance_to((drone.x, drone.y)))

    def _sector_center(self, sector_id: str) -> Optional[tuple[float, float]]:
        sector = self._get_sector(sector_id)
        if sector is None:
            return None
        return (sector.x, sector.y)

    def _get_sector(self, sector_id: Optional[str]) -> Optional[Sector]:
        if sector_id is None:
            return None
        for sector in self.sectors:
            if sector.sector_id == sector_id:
                return sector
        return None

    def _handle_victim_detection(self, step_index: int) -> None:
        for drone in self.drones:
            if drone.health != "active":
                continue
            sector = self._get_sector(drone.sector_id)
            if sector is None:
                continue

            # Check if drone is in a smoke hazard (degrades optical vision)
            detection_prob = 0.85
            for hazard in self.hazards:
                if hazard.contains(drone.x, drone.y) and hazard.hazard_type == "smoke_plume":
                    detection_prob *= (1.0 - hazard.severity * 0.5)

            for victim in self.victims:
                if victim.detected:
                    continue
                distance = hypot(drone.x - victim.x, drone.y - victim.y)
                if distance <= self.config.search_radius and self.random.random() < detection_prob:
                    victim.detected = True
                    victim.sector_id = drone.sector_id
                    victim.rescue_time_step = step_index
                    victim.rescue_priority = max(victim.rescue_priority, self._priority_value(victim.severity))
                    drone.detected_victims.append(victim.victim_id)
                    self.metrics["victim_detections"] += 1
                    sector.status = "locked"
                    sector.covered = True

    def _update_sector_progress(self) -> None:
        for drone in self.drones:
            if drone.health != "active" or drone.sector_id is None:
                continue
            sector = self._get_sector(drone.sector_id)
            if sector is None:
                continue
            sector.completion = min(1.0, sector.completion + (self.config.search_rate * 0.2))
            if sector.completion >= self.config.coverage_threshold:
                sector.covered = True
                sector.status = "covered"
                if sector.sector_id not in drone.covered_sectors:
                    drone.covered_sectors.append(sector.sector_id)

    def _simulate_failures(self) -> None:
        for drone in self.drones:
            if drone.is_physical:
                # Do not inject random hardware dropouts into the physical drone
                continue
            if drone.health == "active" and self.random.random() < (self.config.failure_probability * 0.05):
                drone.health = "failed"
                self.metrics["failed_drones"] += 1
                self._reassign_after_failure(drone)

    def step(self) -> SimulationReport:
        """Advance the simulation by one step (called by backend loop)."""
        self.step_count += 1
        for drone in self.drones:
            self._advance_drone(drone)
        self._handle_victim_detection(self.step_count)
        self._update_sector_progress()
        self._simulate_failures()
        return self._compute_report(self.step_count)

    def update_physical_drone(self, telemetry: Dict[str, Any]) -> None:
        """Inject external real telemetry (e.g. from MAVLink / Mission Planner) into Drone 1."""
        if not self.drones:
            return
        drone = self.drones[0]
        if not drone.is_physical:
            return

        if "lat" in telemetry and "lon" in telemetry:
            # Reverse-project GPS to local arena coordinates
            offset_lat = telemetry["lat"] - self.config.base_lat
            offset_lon = telemetry["lon"] - self.config.base_lon
            drone.y = (self.config.arena_height / 2.0) - (offset_lat * 111000.0)
            drone.x = (self.config.arena_width / 2.0) + (offset_lon * 108750.0)

        if "altitude" in telemetry:
            drone.altitude = float(telemetry["altitude"])
        if "heading" in telemetry:
            drone.heading = float(telemetry["heading"])
        if "pitch" in telemetry:
            drone.pitch = float(telemetry["pitch"])
        if "roll" in telemetry:
            drone.roll = float(telemetry["roll"])
        if "battery" in telemetry:
            drone.battery = float(telemetry["battery"])
        if "health" in telemetry:
            drone.health = str(telemetry["health"])

        drone.telemetry_source = "mavlink"

    def _compute_report(self, steps_completed: int) -> SimulationReport:
        covered = sum(1 for sector in self.sectors if sector.covered)
        total = max(len(self.sectors), 1)
        coverage = covered / total
        rescue_recommendations = self.rescue_agent.prioritize(self.victims, self.drones, self.config.rescue_point)
        detected_names = [victim.victim_id for victim in self.victims if victim.detected]
        status_by_drone = {drone.drone_id: drone.health for drone in self.drones}
        status_by_sector = {sector.sector_id: sector.status for sector in self.sectors}
        self.metrics["coverage_ratio"] = coverage
        self.metrics["total_steps"] = steps_completed
        self.metrics["active_hazards"] = len(self.hazards)

        return SimulationReport(
            steps_completed=steps_completed,
            coverage_ratio=coverage,
            detected_victims=detected_names,
            rescue_recommendations=rescue_recommendations,
            drone_status=status_by_drone,
            sector_status=status_by_sector,
            metrics=self.metrics.copy(),
            drones=[drone.to_dict() for drone in self.drones],
            sectors=[sector.to_dict() for sector in self.sectors],
            victims=[victim.to_dict() for victim in self.victims],
            hazards=[hazard.to_dict() for hazard in self.hazards],
            mode=self.mode,
        )

    def run(self) -> SimulationReport:
        self.initialize()
        for _ in range(self.config.max_steps):
            report = self.step()
            if all(sector.covered for sector in self.sectors):
                break
        return self._compute_report(self.step_count)

    def answer_operator_question(self, question: str) -> str:
        return self.knowledge_agent.answer(question)

