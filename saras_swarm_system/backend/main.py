"""
SARAS Swarm Mission Control Backend
FastAPI server providing REST APIs, real-time WebSocket streaming,
background simulation loop, and dashboard static hosting.
"""

from __future__ import annotations
import asyncio
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from swarm_core.telemetry_contract import (
    DroneTelemetry,
    DetectionEvent,
    SectorModel,
    SwarmState,
    RescueRecommendation,
    SwarmAlert,
)
from swarm_core.simulation.swarm_sim import SwarmSimulator
from swarm_core.agentic_ai.triage_rag import RescueTriageAgent, RAGKnowledgeAgent
from swarm_core.coordination.allocator import evaluate_allocation_policies, haversine_distance
from backend.video_streamer import SwarmVideoStreamer
from backend.mavlink_bridge import MavlinkBridge

app = FastAPI(
    title="SARAS Mission Control API",
    description="Search And Rescue Autonomous Swarm Backend & Telemetry Engine with MAVLink & Hardware Bridge",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"
MEDIA_DIR = BASE_DIR / "media"
DOCS_DIR = BASE_DIR / "docs"

# State & Service Instances
simulator = SwarmSimulator(num_drones=4, auto_generate_sectors=False)
triage_agent = RescueTriageAgent()
rag_agent = RAGKnowledgeAgent()
video_streamer = SwarmVideoStreamer()

def on_mavlink_telemetry(data: Dict[str, Any]) -> None:
    global current_mode
    if current_mode == "hybrid_real" and "Drone-1" in simulator.drones:
        d1 = simulator.drones["Drone-1"]
        if "lat" in data and "lon" in data and data["lat"] != 0 and data["lon"] != 0:
            d1.lat = float(data["lat"])
            d1.lon = float(data["lon"])
        if "alt" in data:
            d1.alt = float(data["alt"])
        if "heading" in data:
            d1.heading = float(data["heading"])
        if "battery" in data:
            d1.battery = float(data["battery"])
        if "speed" in data:
            d1.speed_mps = float(data["speed"])
    video_streamer.update_telemetry(data)

mavlink_bridge = MavlinkBridge(
    connection_str="udpin:127.0.0.1:14550",
    on_telemetry_callback=on_mavlink_telemetry,
)

# Operating mode: "pure_sim" (all virtual drones) or "hybrid_real" (Drone 1 is physical via MAVLink)
current_mode = "pure_sim"

# Wayanad Landslide Environmental Disaster Hazard Zones
WAYANAD_HAZARDS = [
    {
        "hazard_id": "HAZ-01",
        "hazard_type": "landslide_debris",
        "name": "Chooralmala Mudflow Torrent",
        "lat": 11.5375,
        "lon": 76.1385,
        "radius": 140.0,
        "severity": 0.95,
        "description": "Active mud & debris flow downstream of Iruvaazhinji river. High entrapment risk."
    },
    {
        "hazard_id": "HAZ-02",
        "hazard_type": "smoke_plume",
        "name": "Meppadi Ridge Smoke Plume",
        "lat": 11.5340,
        "lon": 76.1415,
        "radius": 95.0,
        "severity": 0.70,
        "description": "Secondary brush fire & dense smoke layer; optical sensor visibility reduced."
    },
    {
        "hazard_id": "HAZ-03",
        "hazard_type": "fire_hotspot",
        "name": "Collapsed Transformer Fire",
        "lat": 11.5388,
        "lon": 76.1420,
        "radius": 60.0,
        "severity": 0.88,
        "description": "Substation transformer short-circuit fire. High thermal radiation."
    },
    {
        "hazard_id": "HAZ-04",
        "hazard_type": "wind_shear",
        "name": "Vellarimala Valley Wind Shear",
        "lat": 11.5320,
        "lon": 76.1360,
        "radius": 180.0,
        "severity": 0.65,
        "description": "Sudden 14 m/s downdrafts across gorge corridor; attitude stability risk."
    }
]

# Recommendations cache: victim_id -> RescueRecommendation
recommendations_map: Dict[str, RescueRecommendation] = {}

# WebSocket Connections
telemetry_clients: List[WebSocket] = []
alert_clients: List[WebSocket] = []

# Background simulation runner task
sim_task: Optional[asyncio.Task] = None
is_simulation_active = True


# Request Schemas
class QueryRequest(BaseModel):
    query: str


class ModeRequest(BaseModel):
    mode: str  # "pure_sim" | "hybrid_real"


class FaultRequest(BaseModel):
    drone_id: str
    fault_type: str  # "dropout" | "battery" | "restore"
    value: Optional[float] = None


class PolicyRequest(BaseModel):
    policy: str  # "AUCTION" | "GREEDY"


class CustomSectorRequest(BaseModel):
    name: str = "Custom Search Zone"
    bounds: List[List[float]]  # [[lat, lon], ...]
    priority: float = 2.0
    zone_type: str = "SEARCH"  # "SEARCH" | "NO_FLY" | "HAZARD"
    dispatch_mode: str = "SWARM"  # "SWARM" | "SINGLE"
    target_drone_id: Optional[str] = None  # Specific drone ID if single UAV dispatch
    color: Optional[str] = None  # Optional distinct hex color


class FleetSizeRequest(BaseModel):
    count: int = Field(..., ge=1, le=16, description="Number of drones in swarm (1-16)")
    reset_mission: bool = Field(False, description="Whether to reset all drones to staged base positions")


class ResetRequest(BaseModel):
    num_drones: Optional[int] = Field(None, ge=1, le=16, description="Optional new drone count on reset")


class RelocateBaseRequest(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude of new GCS base pad")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude of new GCS base pad")


# Background Simulation Loop
async def run_simulation_worker():
    global simulator, is_simulation_active, recommendations_map
    dt = 0.4  # Step delta

    while True:
        try:
            if is_simulation_active:
                # Step physics and swarm coordination
                current_state: SwarmState = simulator.step(dt=dt)

                # Automatic Triage for newly discovered victims
                for detection in current_state.active_detections:
                    if detection.detection_id not in recommendations_map:
                        rec = triage_agent.triage_detection(detection)
                        recommendations_map[detection.detection_id] = rec
                        # Dispatch triage alert
                        alert = SwarmAlert(
                            alert_id=f"ALT-{int(time.time()*1000)%1000000}",
                            timestamp=time.time(),
                            level="CRITICAL" if rec.triage_category == "CRITICAL" else "WARNING",
                            drone_id=detection.drone_id,
                            message=f"TRIAGE [{rec.triage_category.value}]: {rec.recommended_action[:70]}..."
                        )
                        simulator.health_monitor._dispatch_alert(alert)
                        # Broadcast alert to alert websockets
                        await broadcast_alert(alert.model_dump())

                current_state.recommendations = list(recommendations_map.values())

                # Broadcast to telemetry websockets
                payload = current_state.model_dump()
                payload["drones"] = list(payload.get("active_drones", {}).values())
                payload["victims"] = payload.get("active_detections", [])
                payload["mode"] = current_mode
                payload["is_paused"] = not is_simulation_active
                payload["mavlink_connected"] = mavlink_bridge.is_connected
                payload["hazards"] = WAYANAD_HAZARDS
                await broadcast_telemetry(payload)

            await asyncio.sleep(dt)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[Backend Worker Error]: {e}")
            await asyncio.sleep(1.0)


async def broadcast_telemetry(data: dict):
    disconnected = []
    for client in telemetry_clients:
        try:
            await client.send_json(data)
        except Exception:
            disconnected.append(client)
    for dc in disconnected:
        if dc in telemetry_clients:
            telemetry_clients.remove(dc)


async def broadcast_alert(alert_data: dict):
    disconnected = []
    for client in alert_clients:
        try:
            await client.send_json(alert_data)
        except Exception:
            disconnected.append(client)
    for dc in alert_clients:
        if dc in alert_clients:
            alert_clients.remove(dc)


@app.on_event("startup")
async def startup_event():
    global sim_task
    try:
        await mavlink_bridge.start()
    except Exception as e:
        print(f"[MAVLink Bridge Init Note]: {e}")
    sim_task = asyncio.create_task(run_simulation_worker())


@app.on_event("shutdown")
async def shutdown_event():
    global sim_task
    try:
        await mavlink_bridge.stop()
    except Exception as e:
        print(f"[MAVLink Bridge Stop Note]: {e}")
    if sim_task:
        sim_task.cancel()


# REST Endpoints
@app.get("/api/swarm/status")
@app.get("/api/status")
async def get_swarm_status():
    """Returns the latest consolidated swarm state with backward-compatible aliases."""
    state = simulator.step(dt=0.0)
    state.recommendations = list(recommendations_map.values())
    dump = state.model_dump()
    dump["drones"] = list(dump.get("active_drones", {}).values())
    dump["victims"] = dump.get("active_detections", [])
    dump["mode"] = current_mode
    dump["is_paused"] = not is_simulation_active
    dump["mavlink_connected"] = mavlink_bridge.is_connected
    dump["mavlink_status"] = {
        "connected": mavlink_bridge.is_connected,
        "connection_str": mavlink_bridge.connection_str,
        "packets_received": mavlink_bridge.latest_telemetry.get("packet_count", 0),
    }
    dump["hazards"] = WAYANAD_HAZARDS
    return dump


@app.get("/api/mode")
async def get_system_mode():
    """Returns the current operational mode: pure_sim or hybrid_real."""
    return {"status": "ok", "mode": current_mode}


@app.post("/api/mode")
async def set_system_mode(req: ModeRequest):
    """Switch between 'pure_sim' (hazardous simulation) and 'hybrid_real' (1 real drone + N virtual)."""
    global current_mode
    if req.mode not in ("pure_sim", "hybrid_real"):
        raise HTTPException(status_code=400, detail="Invalid mode. Choose 'pure_sim' or 'hybrid_real'")
    current_mode = req.mode
    return {"status": "ok", "mode": current_mode}


@app.get("/api/hazards")
async def get_hazard_zones():
    """Returns active environmental disaster hazard zones (Wayanad Landslide ground zero)."""
    return WAYANAD_HAZARDS


@app.get("/api/mavlink/status")
async def get_mavlink_status():
    """Returns current MAVLink telemetry bridge status and packet reception statistics."""
    return {
        "connected": mavlink_bridge.is_connected,
        "connection_str": mavlink_bridge.connection_str,
        "packets_received": mavlink_bridge.latest_telemetry.get("packet_count", 0),
        "telemetry": mavlink_bridge.latest_telemetry
    }


@app.post("/api/simulation/pause")
async def pause_simulation():
    """Pauses mission simulator step loop."""
    global is_simulation_active
    is_simulation_active = False
    return {"status": "ok", "is_paused": True}


@app.post("/api/simulation/resume")
async def resume_simulation():
    """Resumes mission simulator step loop."""
    global is_simulation_active
    is_simulation_active = True
    return {"status": "ok", "is_paused": False}


@app.post("/api/command")
async def execute_tactical_command(req: Dict[str, Any]):
    """Unified tactical command endpoint for pause, resume, reassign/rebid, and reset."""
    global is_simulation_active
    cmd = req.get("command", "").lower()
    if cmd == "pause":
        is_simulation_active = False
        return {"status": "ok", "command": "pause", "is_paused": True}
    elif cmd == "resume":
        is_simulation_active = True
        return {"status": "ok", "command": "resume", "is_paused": False}
    elif cmd in ("reassign", "rebid"):
        simulator.rebalance_after_dropout()
        return {"status": "ok", "command": cmd, "message": "Swarm tasks re-bid and balanced."}
    elif cmd == "reset":
        return await reset_simulation()
    return {"status": "ok", "command": cmd}


@app.get("/plan")
@app.get("/system-plan")
async def serve_system_plan():
    """Serves the detailed SARAS System & Architecture Plan document."""
    plan_file = DOCS_DIR / "SARAS_SYSTEM_PLAN.html"
    if plan_file.exists():
        return FileResponse(str(plan_file))
    return JSONResponse({"error": "SARAS_SYSTEM_PLAN.html not found"}, status_code=404)


@app.get("/api/sectors")
async def get_sectors():
    """Returns list of search sectors with coordinates and coverage status."""
    return [s.model_dump() for s in simulator.sectors.values()]


TACTICAL_PALETTE = [
    "#00f0ff",  # 1. Electric Cyan
    "#a855f7",  # 2. Electric Purple
    "#f97316",  # 3. Vivid Amber / Orange
    "#10b981",  # 4. Emerald Green
    "#ec4899",  # 5. Neon Rose
    "#eab308",  # 6. Golden Yellow
    "#3b82f6",  # 7. Royal Blue
    "#ef4444",  # 8. Bright Crimson
    "#14b8a6",  # 9. Deep Teal
    "#84cc16",  # 10. Lime Green
]


from shapely.geometry import Polygon, box, MultiPolygon


def partition_polygon_recursive(geom: Polygon, n: int) -> list:
    """
    Recursively partitions an arbitrary 2D polygon into n balanced sub-polygons.
    Uses continuous binary-search bisection along the major axis so that:
    1. Every sub-polygon is strictly clipped inside the original polygon boundary.
    2. The area is equally balanced (1/n each) across all drones.
    3. Handles non-convex, concave, and irregular geometries without spilling outside.
    """
    if n <= 1 or geom.is_empty:
        return [geom]

    if geom.geom_type == "MultiPolygon":
        geoms = list(geom.geoms)
        if len(geoms) == n:
            return geoms
        geom = max(geoms, key=lambda g: g.area)

    min_x, min_y, max_x, max_y = geom.bounds
    dx = max_x - min_x
    dy = max_y - min_y
    total_area = geom.area

    # Split along the longer dimension to yield compact sweep partitions
    split_horiz = (dy >= dx)
    n_left = n // 2
    n_right = n - n_left
    target_area = total_area * (n_left / n)

    low = min_y if split_horiz else min_x
    high = max_y if split_horiz else max_x

    best_c = (low + high) / 2
    for _ in range(25):
        mid = (low + high) / 2
        cut_box = box(min_x - 0.1, min_y - 0.1, max_x + 0.1, mid) if split_horiz else box(min_x - 0.1, min_y - 0.1, mid, max_y + 0.1)
        p_area = geom.intersection(cut_box).area
        if abs(p_area - target_area) < 1e-12:
            best_c = mid
            break
        elif p_area < target_area:
            low = mid
        else:
            high = mid
        best_c = mid

    box1 = box(min_x - 0.1, min_y - 0.1, max_x + 0.1, best_c) if split_horiz else box(min_x - 0.1, min_y - 0.1, best_c, max_y + 0.1)
    box2 = box(min_x - 0.1, best_c, max_x + 0.1, max_y + 0.1) if split_horiz else box(best_c, min_y - 0.1, max_x + 0.1, max_y + 0.1)

    part1 = geom.intersection(box1)
    part2 = geom.intersection(box2)
    if not part1.is_valid:
        part1 = part1.buffer(0)
    if not part2.is_valid:
        part2 = part2.buffer(0)

    res = []
    res.extend(partition_polygon_recursive(part1, n_left))
    res.extend(partition_polygon_recursive(part2, n_right))
    return res


@app.post("/api/sectors/custom")
async def create_custom_sector(req: CustomSectorRequest):
    """Adds an operator-marked custom region to the swarm mission with distinct color and exact polygon partitioning."""
    if len(req.bounds) < 3:
        raise HTTPException(status_code=400, detail="A region boundary must contain at least 3 coordinates.")

    lats = [float(pt[0]) for pt in req.bounds]
    lons = [float(pt[1]) for pt in req.bounds]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    centroid = [sum(lats) / len(lats), sum(lons) / len(lons)]

    # Compute custom sector sequence count
    sec_count = len({s.split("-")[0] + "-" + s.split("-")[1] for s in simulator.sectors.keys() if s.startswith("CUST-")}) + 1
    sector_id = f"CUST-{sec_count:02d}"

    z_type = req.zone_type.upper()
    assigned_color = req.color or (
        "#ff453a" if z_type == "NO_FLY" else (
            "#ff9f0a" if z_type == "HAZARD" else TACTICAL_PALETTE[(sec_count - 1) % len(TACTICAL_PALETTE)]
        )
    )

    new_sector = SectorModel(
        sector_id=sector_id,
        name=req.name or f"Custom Zone {sec_count}",
        bounds=[[float(pt[0]), float(pt[1])] for pt in req.bounds],
        centroid=centroid,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        status="UNSEARCHED",
        priority=float(req.priority),
        coverage_pct=0.0,
        color=assigned_color
    )

    if z_type == "SEARCH":
        created_sectors = []
        d_mode = req.dispatch_mode.upper() if hasattr(req, "dispatch_mode") and req.dispatch_mode else "SWARM"

        if d_mode == "SWARM" and simulator.num_drones > 1:
            n = simulator.num_drones

            # Form shapely Polygon from exact user-drawn vertices
            poly_coords = [[float(pt[0]), float(pt[1])] for pt in req.bounds]
            if poly_coords[0] != poly_coords[-1]:
                poly_coords.append(poly_coords[0])
            poly = Polygon(poly_coords)
            if not poly.is_valid:
                poly = poly.buffer(0)

            # Decompose the exact custom polygon into n balanced sub-polygons according to the number of drones
            sub_polygons = partition_polygon_recursive(poly, n)

            sub_idx = 1
            for sub_geom in sub_polygons:
                if sub_geom.is_empty or sub_geom.area <= 1e-12:
                    continue

                if sub_geom.geom_type == "MultiPolygon":
                    largest_p = max(sub_geom.geoms, key=lambda g: g.area)
                    raw_coords = list(largest_p.exterior.coords)
                else:
                    raw_coords = list(sub_geom.exterior.coords)

                sub_bounds = [[float(c[0]), float(c[1])] for c in raw_coords]
                s_min_lat, s_min_lon, s_max_lat, s_max_lon = sub_geom.bounds
                sub_centroid = [float(sub_geom.centroid.x), float(sub_geom.centroid.y)]

                sub_id = f"CUST-{sec_count:02d}-{chr(64 + sub_idx)}"
                sub_name = f"{req.name or 'Custom Zone'} (Sec {chr(64 + sub_idx)})"

                sub_sec = SectorModel(
                    sector_id=sub_id,
                    name=sub_name,
                    bounds=sub_bounds,
                    centroid=sub_centroid,
                    min_lat=s_min_lat,
                    max_lat=s_max_lat,
                    min_lon=s_min_lon,
                    max_lon=s_max_lon,
                    status="UNSEARCHED",
                    priority=float(req.priority),
                    coverage_pct=0.0,
                    color=assigned_color
                )
                simulator.sectors[sub_id] = sub_sec
                simulator.seed_victims_in_sector(sub_sec)
                created_sectors.append(sub_sec.model_dump())
                sub_idx += 1
        else:
            if hasattr(req, "target_drone_id") and req.target_drone_id and req.target_drone_id in simulator.drones:
                drone = simulator.drones[req.target_drone_id]
                new_sector.assigned_drone_id = req.target_drone_id
                new_sector.status = "SEARCHING"
                drone.assign_sector(new_sector)
            simulator.sectors[sector_id] = new_sector
            simulator.seed_victims_in_sector(new_sector)
            created_sectors.append(new_sector.model_dump())

        assigned_callsign = req.target_drone_id if (d_mode != "SWARM" and req.target_drone_id) else "SWARM"
        alert = SwarmAlert(
            alert_id=f"ALT-CUST-{int(time.time()*1000)%1000000}",
            timestamp=time.time(),
            level="WARNING",
            drone_id=assigned_callsign,
            message=f"OPERATOR DISPATCH: {assigned_callsign} deployed to '{req.name}' ({len(created_sectors)} sector(s), Priority {req.priority}x, Color {assigned_color})."
        )
        simulator.health_monitor._dispatch_alert(alert)
        await broadcast_alert(alert.model_dump())
        return {
            "status": "ok",
            "sectors": created_sectors,
            "color": assigned_color,
            "message": f"{assigned_callsign} deployed across {len(created_sectors)} sector(s) in '{req.name}'."
        }
    else:
        new_sector.status = z_type
        simulator.sectors[sector_id] = new_sector
        alert = SwarmAlert(
            alert_id=f"ALT-GEO-{int(time.time()*1000)%1000000}",
            timestamp=time.time(),
            level="CRITICAL" if z_type == "NO_FLY" else "WARNING",
            drone_id="SWARM",
            message=f"GEOFENCE ACTIVE: {z_type} zone '{req.name}' locked. Airspace deconfliction enforced."
        )
        simulator.health_monitor._dispatch_alert(alert)
        await broadcast_alert(alert.model_dump())
        return {"status": "ok", "message": f"Geofence '{req.name}' registered with deconfliction.", "sector": new_sector.model_dump(), "color": assigned_color}


@app.delete("/api/sectors/custom/all")
async def clear_all_custom_sectors():
    """Clears all operator-marked custom zones and returns assigned UAVs to base launch pad."""
    removed_ids = [s_id for s_id in list(simulator.sectors.keys()) if s_id.startswith("CUST")]
    for s_id in removed_ids:
        del simulator.sectors[s_id]

    rehomed = []
    for drone in simulator.drones.values():
        if drone.current_sector_id and drone.current_sector_id.startswith("CUST"):
            drone.return_to_home()
            rehomed.append(drone.drone_id)

    alert = SwarmAlert(
        alert_id=f"ALT-CLR-{int(time.time()*1000)%1000000}",
        timestamp=time.time(),
        level="INFO",
        drone_id="SWARM",
        message=f"ALL MARKED REGIONS CLEARED: Removed {len(removed_ids)} sector(s). Assigned UAVs returning to launch pad."
    )
    simulator.health_monitor._dispatch_alert(alert)
    await broadcast_alert(alert.model_dump())
    return {"status": "ok", "removed_count": len(removed_ids), "rehomed_drones": rehomed, "message": "All custom sectors removed."}


@app.delete("/api/sectors/{sector_id}")
async def delete_custom_sector(sector_id: str):
    """
    Deletes a specific custom sector or entire marked region (e.g. CUST-01 deletes all CUST-01-* sub-sectors).
    Safely commands assigned UAVs to return home or reallocates remaining mission tasks.
    """
    to_delete = []
    for s_id in list(simulator.sectors.keys()):
        if s_id == sector_id or s_id.startswith(f"{sector_id}-"):
            to_delete.append(s_id)

    if not to_delete:
        raise HTTPException(status_code=404, detail=f"Sector {sector_id} not found.")

    for s_id in to_delete:
        del simulator.sectors[s_id]

    rehomed_drones = []
    for drone in simulator.drones.values():
        if drone.current_sector_id in to_delete or (drone.current_sector_id and drone.current_sector_id.startswith(f"{sector_id}-")):
            drone.return_to_home()
            rehomed_drones.append(drone.drone_id)

    # Idle drones will automatically pick up remaining unsearched sectors on the next simulation tick
    unsearched = [s for s in simulator.sectors.values() if (hasattr(s.status, "value") and s.status.value == "UNSEARCHED") or s.status == "UNSEARCHED"]

    alert = SwarmAlert(
        alert_id=f"ALT-DEL-{int(time.time()*1000)%1000000}",
        timestamp=time.time(),
        level="INFO",
        drone_id="SWARM",
        message=f"REGION REMOVED: '{sector_id}' ({len(to_delete)} sector(s)) deleted. UAVs updated."
    )
    simulator.health_monitor._dispatch_alert(alert)
    await broadcast_alert(alert.model_dump())

    return {
        "status": "ok",
        "deleted_sectors": to_delete,
        "rehomed_drones": rehomed_drones,
        "message": f"Successfully deleted {len(to_delete)} sector(s) for region {sector_id}."
    }



@app.get("/api/victims")
async def get_victims():
    """Returns detected disaster victims."""
    return [d.model_dump() for d in simulator.detections]


@app.get("/api/victims/sorted")
async def get_sorted_victims():
    """
    Returns all victims (detected and active ground truth) sorted strictly by triage severity.
    Includes GPS coordinates, distance to base/GCS, thermal signature, triage recommendation,
    and aerial inspection snapshot URL.
    """
    results = []
    base_lat = simulator.min_lat + (simulator.max_lat - simulator.min_lat) / 2.0
    base_lon = simulator.min_lon + (simulator.max_lon - simulator.min_lon) / 2.0
    if simulator.drones:
        d1 = next(iter(simulator.drones.values()))
        base_lat, base_lon = d1.home_lat, d1.home_lon

    all_vic_map = {v["id"]: v for v in simulator.ground_truth_victims}
    processed_ids = set()

    # Process all detections
    for det in simulator.detections:
        processed_ids.add(det.detection_id)
        rec = recommendations_map.get(det.detection_id)
        if not rec:
            rec = triage_agent.triage_detection(det)
            recommendations_map[det.detection_id] = rec

        dist_m = haversine_distance(base_lat, base_lon, det.lat, det.lon)
        cat_val = rec.triage_category.value if (rec and hasattr(rec.triage_category, "value")) else str(rec.triage_category if rec else "CRITICAL")
        results.append({
            "victim_id": det.detection_id,
            "drone_id": det.drone_id,
            "lat": det.lat,
            "lon": det.lon,
            "distance_m": round(dist_m, 1),
            "confidence": det.confidence,
            "thermal_signature": det.thermal_signature or 35.2,
            "environment_tags": det.environment_tags,
            "status": det.status.value if hasattr(det.status, "value") else str(det.status),
            "urgency_score": rec.urgency_score if rec else 90.0,
            "triage_category": cat_val,
            "recommended_action": rec.recommended_action if rec else "Immediate medical drop & evac",
            "sop_references": rec.sop_references if rec else ["SOP-MED-01"],
            "notes": det.notes or (rec.notes if rec else ""),
            "snapshot_url": f"/api/victims/{det.detection_id}/snapshot",
            "detected_at": det.timestamp
        })

    # Include any remaining casualties so operator can triage full disaster zone
    for vic_id, vic in all_vic_map.items():
        if vic_id not in processed_ids:
            dummy_det = DetectionEvent(
                detection_id=vic_id,
                drone_id="UAV-01",
                lat=vic["lat"],
                lon=vic["lon"],
                confidence=vic.get("confidence", 0.94),
                thermal_signature=vic.get("thermal_signature", 35.2),
                environment_tags=vic.get("environment_tags", []),
                notes=vic.get("notes", "")
            )
            rec = recommendations_map.get(vic_id)
            if not rec:
                rec = triage_agent.triage_detection(dummy_det)
                recommendations_map[vic_id] = rec

            dist_m = haversine_distance(base_lat, base_lon, vic["lat"], vic["lon"])
            cat_val = rec.triage_category.value if (rec and hasattr(rec.triage_category, "value")) else str(rec.triage_category)
            results.append({
                "victim_id": vic_id,
                "drone_id": "UAV-01",
                "lat": vic["lat"],
                "lon": vic["lon"],
                "distance_m": round(dist_m, 1),
                "confidence": vic.get("confidence", 0.94),
                "thermal_signature": vic.get("thermal_signature", 35.2),
                "environment_tags": vic.get("environment_tags", []),
                "status": "TRIAGED",
                "urgency_score": rec.urgency_score,
                "triage_category": cat_val,
                "recommended_action": rec.recommended_action,
                "sop_references": rec.sop_references,
                "notes": vic.get("notes", ""),
                "snapshot_url": f"/api/victims/{vic_id}/snapshot",
                "detected_at": time.time()
            })

    # Sort strictly according to severity / urgency score descending
    results.sort(key=lambda x: x["urgency_score"], reverse=True)
    return results


@app.get("/api/victims/{victim_id}/snapshot")
async def get_victim_snapshot(victim_id: str):
    """Returns high-resolution aerial optical & thermal inspection snapshot JPEG for a specific victim."""
    target_data = None
    for d in simulator.detections:
        if d.detection_id == victim_id:
            rec = recommendations_map.get(victim_id)
            cat = rec.triage_category.value if (rec and hasattr(rec.triage_category, "value")) else "CRITICAL"
            target_data = {
                "victim_id": d.detection_id,
                "lat": d.lat,
                "lon": d.lon,
                "drone_id": d.drone_id,
                "triage_category": cat,
                "thermal_signature": d.thermal_signature,
                "confidence": d.confidence,
                "tags": d.environment_tags,
                "notes": d.notes
            }
            break

    if not target_data:
        for v in simulator.ground_truth_victims:
            if v["id"] == victim_id:
                rec = recommendations_map.get(victim_id)
                cat = rec.triage_category.value if (rec and hasattr(rec.triage_category, "value")) else ("CRITICAL" if v.get("thermal_signature", 37) < 35 else "URGENT")
                target_data = {
                    "victim_id": v["id"],
                    "lat": v["lat"],
                    "lon": v["lon"],
                    "drone_id": "UAV-01",
                    "triage_category": cat,
                    "thermal_signature": v.get("thermal_signature"),
                    "confidence": v.get("confidence", 0.92),
                    "tags": v.get("environment_tags", []),
                    "notes": v.get("notes", "")
                }
                break

    if not target_data:
        raise HTTPException(status_code=404, detail=f"Victim {victim_id} not found.")

    jpeg_bytes = video_streamer.generate_victim_snapshot(
        victim_id=target_data["victim_id"],
        lat=target_data["lat"],
        lon=target_data["lon"],
        drone_id=target_data["drone_id"],
        triage_category=target_data["triage_category"],
        thermal_signature=target_data["thermal_signature"],
        confidence=target_data["confidence"],
        tags=target_data["tags"],
        notes=target_data["notes"],
        force_fresh=False
    )
    return Response(content=jpeg_bytes, media_type="image/jpeg")


@app.post("/api/victims/{victim_id}/capture")
async def capture_fresh_victim_snapshot(victim_id: str):
    """Forces fresh real-time aerial snapshot capture for victim."""
    target_data = None
    for d in simulator.detections:
        if d.detection_id == victim_id:
            rec = recommendations_map.get(victim_id)
            cat = rec.triage_category.value if (rec and hasattr(rec.triage_category, "value")) else "CRITICAL"
            target_data = {
                "victim_id": d.detection_id,
                "lat": d.lat,
                "lon": d.lon,
                "drone_id": d.drone_id,
                "triage_category": cat,
                "thermal_signature": d.thermal_signature,
                "confidence": d.confidence,
                "tags": d.environment_tags,
                "notes": d.notes
            }
            break

    if not target_data:
        for v in simulator.ground_truth_victims:
            if v["id"] == victim_id:
                rec = recommendations_map.get(victim_id)
                cat = rec.triage_category.value if (rec and hasattr(rec.triage_category, "value")) else "URGENT"
                target_data = {
                    "victim_id": v["id"],
                    "lat": v["lat"],
                    "lon": v["lon"],
                    "drone_id": "UAV-01",
                    "triage_category": cat,
                    "thermal_signature": v.get("thermal_signature"),
                    "confidence": v.get("confidence", 0.92),
                    "tags": v.get("environment_tags", []),
                    "notes": v.get("notes", "")
                }
                break

    if not target_data:
        raise HTTPException(status_code=404, detail=f"Victim {victim_id} not found.")

    jpeg_bytes = video_streamer.generate_victim_snapshot(
        victim_id=target_data["victim_id"],
        lat=target_data["lat"],
        lon=target_data["lon"],
        drone_id=target_data["drone_id"],
        triage_category=target_data["triage_category"],
        thermal_signature=target_data["thermal_signature"],
        confidence=target_data["confidence"],
        tags=target_data["tags"],
        notes=target_data["notes"],
        force_fresh=True
    )
    return Response(content=jpeg_bytes, media_type="image/jpeg")


@app.get("/api/reports/triage-pdf")
@app.get("/api/reports/triage/pdf")
async def export_triage_pdf_report(fresh: bool = False):
    """
    Generates and returns the official, publication-grade SARAS Casualty Triage PDF report
    containing sorted victims, exact GPS coordinates, aerial reconnaissance optical & thermal snapshots,
    urgency scores, and SOP action protocols.
    """
    reports_dir = BASE_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = reports_dir / "SARAS_Casualty_Triage_Report.pdf"

    # Fetch current sorted casualties
    sorted_victims = await get_sorted_victims()
    fleet_info = [d.to_telemetry().model_dump() for d in simulator.drones.values()]

    try:
        from backend.report_generator import generate_triage_pdf_report
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: generate_triage_pdf_report(
                victims=sorted_victims,
                gcs_lat=simulator.base_lat,
                gcs_lon=simulator.base_lon,
                fleet_info=fleet_info,
                video_streamer=video_streamer,
                output_path=pdf_path
            )
        )
    except Exception as e:
        print(f"[Main API] PDF generation error: {e}")
        if not pdf_path.exists():
            raise HTTPException(status_code=500, detail=f"Failed to generate report PDF: {e}")

    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename="SARAS_Casualty_Triage_Report.pdf",
        headers={"Content-Disposition": "inline; filename=SARAS_Casualty_Triage_Report.pdf"}
    )


@app.get("/api/recommendations")
async def get_recommendations():
    """Returns AI Triage recommendations for all detected victims."""
    return [r.model_dump() for r in recommendations_map.values()]


@app.post("/api/query")
async def query_rag(req: QueryRequest):
    """Answers operator search and rescue inquiries using TF-IDF RAG over disaster SOPs."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    response = rag_agent.answer_query(req.query)
    return response


@app.get("/api/video/feed")
@app.get("/api/video/feed/{drone_id}")
async def get_drone_video_feed(drone_id: str = "Drone-1"):
    """MJPEG live camera stream with tactical HUD and YOLO target locks for specified UAV."""
    def get_drone_telemetry(d_id: str) -> Dict[str, Any]:
        if d_id in simulator.drones:
            return simulator.drones[d_id].to_telemetry().model_dump()
        elif simulator.drones:
            return next(iter(simulator.drones.values())).to_telemetry().model_dump()
        return {}

    return StreamingResponse(
        video_streamer.generate_mjpeg_stream(drone_id=drone_id, telemetry_getter=get_drone_telemetry),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/api/swarm/policy")
async def set_policy(req: PolicyRequest):
    """Sets swarm task allocation policy: AUCTION or GREEDY."""
    policy = req.policy.upper()
    if policy not in ("AUCTION", "GREEDY"):
        raise HTTPException(status_code=400, detail="Policy must be AUCTION or GREEDY.")
    simulator.set_allocator(policy)
    return {"status": "ok", "policy": policy}


@app.post("/api/swarm/fault")
async def inject_fault(req: FaultRequest):
    """Simulates drone communication failure, low battery, or recovery."""
    drone_id = req.drone_id
    f_type = req.fault_type.lower()

    if drone_id not in simulator.drones:
        raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found.")

    if f_type == "dropout":
        simulator.inject_dropout(drone_id)
        msg = f"Simulated comms dropout for {drone_id}."
    elif f_type == "battery":
        val = req.value if req.value is not None else 12.0
        simulator.inject_battery_drain(drone_id, val)
        msg = f"Simulated battery drain on {drone_id} to {val}%."
    elif f_type == "restore":
        simulator.restore_drone(drone_id)
        msg = f"Restored {drone_id} to nominal state."
    else:
        raise HTTPException(status_code=400, detail=f"Unknown fault type: {f_type}")

    return {"status": "ok", "message": msg}


@app.post("/api/swarm/fleet-size")
@app.post("/api/swarm/scale")
async def set_fleet_size(req: FleetSizeRequest):
    """Dynamically sets or scales the number of drones in the swarm (1 to 16)."""
    res = simulator.set_drone_count(req.count, reset_mission=req.reset_mission)
    alert = SwarmAlert(
        alert_id=f"ALT-SCALE-{int(time.time()*1000)%1000000}",
        timestamp=time.time(),
        level="INFO",
        drone_id="SWARM",
        message=f"FLEET RECONFIGURED: Swarm operator set fleet size to {simulator.num_drones} UAVs ({res['action']})."
    )
    simulator.health_monitor._dispatch_alert(alert)
    return {
        "status": "ok",
        "drone_count": simulator.num_drones,
        "drones": [d.to_telemetry().model_dump() for d in simulator.drones.values()],
        "message": f"Swarm fleet configured to {simulator.num_drones} UAVs."
    }


@app.post("/api/swarm/relocate")
async def relocate_swarm_base(req: RelocateBaseRequest):
    """Relocates swarm staging base launch pad to specified GPS coordinates (e.g. user live GPS)."""
    simulator.relocate_base(req.lat, req.lon)
    alert = SwarmAlert(
        alert_id=f"ALT-LOC-{int(time.time()*1000)%1000000}",
        timestamp=time.time(),
        level="INFO",
        drone_id="GCS",
        message=f"GCS BASE RELOCATED: Swarm launch pad positioned to GPS [{req.lat:.5f}, {req.lon:.5f}]."
    )
    simulator.health_monitor._dispatch_alert(alert)
    return {
        "status": "ok",
        "base_lat": req.lat,
        "base_lon": req.lon,
        "drones": [d.to_telemetry().model_dump() for d in simulator.drones.values()],
        "message": f"Swarm launch pad relocated to [{req.lat:.5f}, {req.lon:.5f}]."
    }


@app.post("/api/swarm/reset")
async def reset_simulation(req: Optional[ResetRequest] = None):
    """Resets simulator to fresh initial state."""
    global simulator, recommendations_map
    current_policy = simulator.allocator_type
    drone_count = req.num_drones if (req and req.num_drones) else simulator.num_drones
    drone_count = max(1, min(16, drone_count))
    simulator = SwarmSimulator(num_drones=drone_count, allocator_type=current_policy, auto_generate_sectors=False)
    recommendations_map.clear()
    return {
        "status": "ok",
        "drone_count": simulator.num_drones,
        "message": f"Swarm simulation reset to initial parameters with {simulator.num_drones} UAVs."
    }


@app.get("/api/benchmark")
async def run_benchmark():
    """Executes ablation evaluation comparing Market Auction vs Greedy Allocation."""
    fleet_count = max(2, simulator.num_drones)
    results = evaluate_allocation_policies(num_drones=fleet_count, rows=3, cols=4)
    return {
        "title": "SARAS Swarm Task Allocation Benchmark (IEEE Ablation Study)",
        "metrics": results
    }


# WebSocket Endpoints
@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    await websocket.accept()
    telemetry_clients.append(websocket)
    try:
        while True:
            # Keep-alive receive
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in telemetry_clients:
            telemetry_clients.remove(websocket)


@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    await websocket.accept()
    alert_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in alert_clients:
            alert_clients.remove(websocket)


# Static Dashboard Hosting & Route Aliases
if DASHBOARD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")
    app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard_static")

    @app.get("/")
    @app.get("/index.html")
    async def serve_dashboard():
        index_file = DASHBOARD_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse({"error": "Dashboard index.html not found"}, status_code=404)

    @app.get("/triage")
    @app.get("/triage.html")
    @app.get("/casualty-dashboard")
    async def serve_triage_dashboard():
        triage_file = DASHBOARD_DIR / "triage.html"
        if triage_file.exists():
            return FileResponse(str(triage_file))
        return JSONResponse({"error": "triage.html not found"}, status_code=404)
