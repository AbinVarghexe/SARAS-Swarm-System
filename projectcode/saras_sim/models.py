from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, hypot, radians
from typing import Any, Dict, List, Optional, Tuple

# Wayanad Chooralmala, Kerala Landslide Disaster Anchor
KERALA_BASE_LAT = 11.5360
KERALA_BASE_LON = 76.1390
METERS_PER_DEG_LAT = 111000.0
METERS_PER_DEG_LON = 111000.0 * cos(radians(KERALA_BASE_LAT))


def local_to_gps(x: float, y: float, arena_w: float = 1000.0, arena_h: float = 1000.0) -> Tuple[float, float]:
    """Convert local arena coordinates (meters) to Kerala GPS lat/lon."""
    offset_x = x - (arena_w / 2.0)
    offset_y = (arena_h / 2.0) - y  # y increases downward in 2D arena, north is up
    lat = KERALA_BASE_LAT + (offset_y / METERS_PER_DEG_LAT)
    lon = KERALA_BASE_LON + (offset_x / METERS_PER_DEG_LON)
    return round(lat, 6), round(lon, 6)


@dataclass
class HazardZone:
    """Represents an environmental disaster hazard (fire, smoke, debris, wind)."""
    hazard_id: str
    hazard_type: str  # "landslide_debris", "smoke_plume", "fire_hotspot", "wind_shear"
    x: float
    y: float
    radius: float
    severity: float  # 0.0 to 1.0
    wind_vector: Tuple[float, float] = (0.0, 0.0)
    description: str = ""

    @property
    def center(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def contains(self, px: float, py: float) -> bool:
        return hypot(px - self.x, py - self.y) <= self.radius

    def to_dict(self) -> Dict[str, Any]:
        lat, lon = local_to_gps(self.x, self.y)
        return {
            "hazard_id": self.hazard_id,
            "hazard_type": self.hazard_type,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "radius": round(self.radius, 2),
            "severity": round(self.severity, 2),
            "wind_vector": list(self.wind_vector),
            "description": self.description,
            "lat": lat,
            "lon": lon,
        }


@dataclass
class Sector:
    sector_id: str
    x: float
    y: float
    width: float
    height: float
    assigned_to: Optional[str] = None
    covered: bool = False
    completion: float = 0.0
    status: str = "available"

    @property
    def center(self) -> tuple[float, float]:
        return (self.x, self.y)

    def to_dict(self) -> Dict[str, Any]:
        lat, lon = local_to_gps(self.x, self.y)
        return {
            "sector_id": self.sector_id,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "width": round(self.width, 2),
            "height": round(self.height, 2),
            "completion": round(self.completion, 3),
            "status": self.status,
            "assigned_to": self.assigned_to,
            "lat": lat,
            "lon": lon,
        }


@dataclass
class Drone:
    drone_id: str
    x: float
    y: float
    battery: float
    health: str = "active"  # "active", "returning", "failed", "emergency"
    sector_id: Optional[str] = None
    detected_victims: List[str] = field(default_factory=list)
    covered_sectors: List[str] = field(default_factory=list)
    last_known_sector: Optional[str] = None

    # Telemetry and Physical Node Attributes
    is_physical: bool = False  # True for physical Drone-01 in Hybrid mode
    heading: float = 0.0  # degrees 0-360
    pitch: float = 0.0  # degrees
    roll: float = 0.0  # degrees
    altitude: float = 35.0  # meters AGL
    speed: float = 12.0  # m/s
    telemetry_source: str = "sim"  # "mavlink", "sim", "emulated"
    video_feed_active: bool = False

    @property
    def position(self) -> tuple[float, float]:
        return (self.x, self.y)

    def distance_to(self, point: tuple[float, float]) -> float:
        return hypot(self.x - point[0], self.y - point[1])

    def to_dict(self) -> Dict[str, Any]:
        lat, lon = local_to_gps(self.x, self.y)
        return {
            "drone_id": self.drone_id,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "battery": round(self.battery, 1),
            "health": self.health,
            "sector_id": self.sector_id,
            "detected_victims": self.detected_victims,
            "is_physical": self.is_physical,
            "heading": round(self.heading, 1),
            "pitch": round(self.pitch, 1),
            "roll": round(self.roll, 1),
            "altitude": round(self.altitude, 1),
            "speed": round(self.speed, 1),
            "telemetry_source": self.telemetry_source,
            "video_feed_active": self.video_feed_active,
            "lat": lat,
            "lon": lon,
        }


@dataclass
class Victim:
    victim_id: str
    x: float
    y: float
    severity: str  # "critical", "high", "medium", "low"
    sector_id: Optional[str] = None
    detected: bool = False
    rescued: bool = False
    rescue_priority: int = 0
    rescue_time_step: Optional[int] = None

    @property
    def position(self) -> tuple[float, float]:
        return (self.x, self.y)

    def to_dict(self) -> Dict[str, Any]:
        lat, lon = local_to_gps(self.x, self.y)
        return {
            "victim_id": self.victim_id,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "severity": self.severity,
            "detected": self.detected,
            "sector_id": self.sector_id,
            "rescue_time_step": self.rescue_time_step,
            "rescue_priority": self.rescue_priority,
            "lat": lat,
            "lon": lon,
        }


@dataclass
class RescueRecommendation:
    victim_id: str
    priority: int
    estimated_distance: float
    nearest_rescue_point: tuple[float, float]
    suggested_order: int
    drone_id: str
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        lat, lon = local_to_gps(self.nearest_rescue_point[0], self.nearest_rescue_point[1])
        return {
            "victim_id": self.victim_id,
            "priority": self.priority,
            "estimated_distance": round(self.estimated_distance, 2),
            "nearest_rescue_point": list(self.nearest_rescue_point),
            "rescue_point_gps": [lat, lon],
            "suggested_order": self.suggested_order,
            "drone_id": self.drone_id,
            "rationale": self.rationale,
        }


@dataclass
class SimulationReport:
    steps_completed: int
    coverage_ratio: float
    detected_victims: List[str]
    rescue_recommendations: List[RescueRecommendation]
    drone_status: Dict[str, str]
    sector_status: Dict[str, str]
    metrics: Dict[str, Any]
    drones: List[Dict[str, Any]] = field(default_factory=list)
    sectors: List[Dict[str, Any]] = field(default_factory=list)
    victims: List[Dict[str, Any]] = field(default_factory=list)
    hazards: List[Dict[str, Any]] = field(default_factory=list)
    mode: str = "pure_sim"
    kerala_anchor: Dict[str, float] = field(default_factory=lambda: {
        "lat": KERALA_BASE_LAT,
        "lon": KERALA_BASE_LON,
        "region": "Wayanad Chooralmala / Meppadi, Kerala"
    })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps_completed": self.steps_completed,
            "coverage_ratio": round(self.coverage_ratio, 3),
            "detected_victims": self.detected_victims,
            "rescue_recommendations": [item.to_dict() for item in self.rescue_recommendations],
            "drone_status": self.drone_status,
            "sector_status": self.sector_status,
            "metrics": self.metrics,
            "drones": self.drones,
            "sectors": self.sectors,
            "victims": self.victims,
            "hazards": self.hazards,
            "mode": self.mode,
            "kerala_anchor": self.kerala_anchor,
        }

    def summary(self) -> str:
        lines = [
            f"SARAS simulation summary [{self.mode.upper()} - {self.kerala_anchor.get('region', 'Kerala')}]",
            f"Steps completed: {self.steps_completed}",
            f"Coverage ratio: {self.coverage_ratio:.2%}",
            f"Active fleet: {len(self.drones)} drones",
            f"Detected victims: {len(self.detected_victims)}",
            f"Active hazards: {len(self.hazards)}",
            f"Rescue recommendations: {len(self.rescue_recommendations)}",
        ]
        for recommendation in self.rescue_recommendations:
            lines.append(
                f"- Victim {recommendation.victim_id}: priority {recommendation.priority}, "
                f"order {recommendation.suggested_order}, drone {recommendation.drone_id}"
            )
        return "\n".join(lines)

