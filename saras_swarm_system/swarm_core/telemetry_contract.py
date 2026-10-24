"""
SARAS Swarm Telemetry Contract
Standard Pydantic v2 schemas for DroneTelemetry, DetectionEvent, SectorModel,
SwarmState, RescueRecommendation, and SwarmAlert.
"""

from __future__ import annotations
import time
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DroneStatus(str, Enum):
    IDLE = "IDLE"
    SEARCHING = "SEARCHING"
    RETURNING = "RETURNING"
    ASSISTING = "ASSISTING"
    FAULT = "FAULT"
    LOST = "LOST"


class SectorStatus(str, Enum):
    UNSEARCHED = "UNSEARCHED"
    SEARCHING = "SEARCHING"
    COVERED = "COVERED"


class TriageCategory(str, Enum):
    CRITICAL = "CRITICAL"   # Immediate life threat: rapid evac / medical drop
    URGENT = "URGENT"       # Severe injuries: rescue within 1-2 hours
    STABLE = "STABLE"       # Minor / ambulatory: shelter in place or ground team


class DetectionStatus(str, Enum):
    PENDING = "PENDING"
    TRIAGED = "TRIAGED"
    RESCUED = "RESCUED"


class GeoPoint(BaseModel):
    lat: float = Field(..., description="Latitude in decimal degrees")
    lon: float = Field(..., description="Longitude in decimal degrees")
    alt: float = Field(0.0, description="Altitude in meters AGL")


class DroneTelemetry(BaseModel):
    drone_id: str = Field(..., description="Unique drone identifier (e.g. Drone-1)")
    timestamp: float = Field(default_factory=time.time, description="Unix epoch timestamp")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    alt: float = Field(15.0, description="Altitude AGL in meters")
    battery: float = Field(..., ge=0.0, le=100.0, description="Battery percentage (0.0 to 100.0)")
    speed: float = Field(0.0, ge=0.0, description="Ground speed in m/s")
    heading: float = Field(0.0, ge=0.0, le=360.0, description="Heading in degrees (0 = North)")
    status: DroneStatus = Field(default=DroneStatus.IDLE, description="Operational state")
    current_sector_id: Optional[str] = Field(None, description="Currently assigned sector ID")
    target_waypoint: Optional[List[float]] = Field(None, description="[lat, lon] current target")
    mission_time: float = Field(0.0, description="Elapsed mission time in seconds")
    victims_detected: int = Field(0, description="Count of victims detected by this drone")

    @field_validator("heading")
    @classmethod
    def normalize_heading(cls, v: float) -> float:
        return v % 360.0


class DetectionEvent(BaseModel):
    detection_id: str = Field(..., description="Unique ID for detection event")
    drone_id: str = Field(..., description="Reporting drone ID")
    timestamp: float = Field(default_factory=time.time, description="Timestamp of detection")
    lat: float = Field(..., description="Latitude of victim")
    lon: float = Field(..., description="Longitude of victim")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    label: str = Field("victim", description="Class label (e.g. victim, person)")
    bbox: Optional[List[float]] = Field(None, description="[x_min, y_min, x_max, y_max] normalized")
    thermal_signature: Optional[float] = Field(None, description="Estimated body temp in Celsius")
    environment_tags: List[str] = Field(default_factory=list, description="Tags: flood, fire, debris, smoke")
    status: DetectionStatus = Field(default=DetectionStatus.PENDING, description="Rescue progress status")
    notes: Optional[str] = Field(None, description="Contextual triage notes")


class SectorModel(BaseModel):
    sector_id: str = Field(..., description="Unique sector identifier (e.g. SEC-01)")
    name: str = Field(..., description="Human-readable sector name")
    bounds: List[List[float]] = Field(..., description="Polygon coordinates [[lat, lon], ...]")
    centroid: List[float] = Field(..., description="[lat, lon] center point")
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    status: SectorStatus = Field(default=SectorStatus.UNSEARCHED, description="Sector search status")
    assigned_drone_id: Optional[str] = Field(None, description="Assigned drone ID or None")
    priority: float = Field(1.0, description="Priority weight (higher = urgent)")
    coverage_pct: float = Field(0.0, ge=0.0, le=100.0, description="Percentage of sector searched")
    last_searched_at: Optional[float] = Field(None, description="Timestamp of last search progress")
    color: Optional[str] = Field(None, description="Hex color code for map visualization (e.g. #00f0ff)")


class RescueRecommendation(BaseModel):
    rec_id: str = Field(..., description="Recommendation unique ID")
    victim_id: str = Field(..., description="Reference to DetectionEvent.detection_id")
    urgency_score: float = Field(..., ge=0.0, le=100.0, description="Calculated urgency score 0-100")
    triage_category: TriageCategory = Field(..., description="START triage class")
    recommended_action: str = Field(..., description="Prescribed tactical rescue action")
    assigned_asset: Optional[str] = Field(None, description="Suggested rescue asset (e.g. Boat-1, Heli-Alpha, Ground-Team-3)")
    sop_references: List[str] = Field(default_factory=list, description="Referenced emergency SOP sections")
    notes: str = Field("", description="Triage rationale and instructions")
    timestamp: float = Field(default_factory=time.time)


class SwarmAlert(BaseModel):
    alert_id: str = Field(..., description="Alert ID")
    timestamp: float = Field(default_factory=time.time)
    level: str = Field("INFO", description="INFO | WARNING | CRITICAL")
    drone_id: Optional[str] = Field(None, description="Associated drone or None")
    message: str = Field(..., description="Alert description text")


class SwarmState(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    active_drones: Dict[str, DroneTelemetry] = Field(default_factory=dict)
    sectors: Dict[str, SectorModel] = Field(default_factory=dict)
    total_coverage_pct: float = Field(0.0, ge=0.0, le=100.0)
    active_detections: List[DetectionEvent] = Field(default_factory=list)
    recommendations: List[RescueRecommendation] = Field(default_factory=list)
    alerts: List[SwarmAlert] = Field(default_factory=list)
    system_health: str = Field("HEALTHY", description="HEALTHY | DEGRADED | CRITICAL")
    allocation_policy: str = Field("AUCTION", description="AUCTION | GREEDY | RL")
