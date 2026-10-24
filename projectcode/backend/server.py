"""SARAS Swarm Mission Command Server.

FastAPI backend with real-time WebSocket telemetry push,
MAVLink/Mission Planner bridge, live YOLO video stream with HUD,
and dynamic multi-drone fleet management.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure projectcode root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.mavlink_bridge import MavlinkBridge
from backend.video_streamer import VideoStreamer
from saras_sim.config import SimulationConfig
from saras_sim.simulator import SwarmSimulation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("saras.server")

app = FastAPI(
    title="SARAS Swarm Command System",
    description="Autonomous Multi-Drone Search & Rescue API with MAVLink, Live Video HUD & Swarm Allocation",
    version="2.0.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global system state
config = SimulationConfig(mode="pure_sim", drone_count=4)
simulation = SwarmSimulation(config)
simulation.initialize()

video_streamer = VideoStreamer()
active_websockets: List[WebSocket] = []
is_paused = False


def on_mavlink_telemetry(data: Dict[str, Any]) -> None:
    """Callback when MAVLink message arrives from Mission Planner / Pixhawk."""
    if simulation.mode == "hybrid_real":
        simulation.update_physical_drone(data)
        video_streamer.update_telemetry(data)


mavlink_bridge = MavlinkBridge(
    connection_str="udpin:127.0.0.1:14550",
    on_telemetry_callback=on_mavlink_telemetry,
)


# Request Models
class ModeRequest(BaseModel):
    mode: str  # "pure_sim" or "hybrid_real"


class DroneCountRequest(BaseModel):
    count: int  # 1 to 10


class CommandRequest(BaseModel):
    command: str  # "pause", "resume", "reset", "reassign", "rtl"
    drone_id: Optional[str] = None


class AgentQueryRequest(BaseModel):
    query: str


class HazardInjectRequest(BaseModel):
    hazard_type: str
    x: float
    y: float
    radius: float
    severity: float
    description: str


# Background Simulation & Broadcast Task
async def simulation_loop() -> None:
    """Runs at ~8-10 Hz, stepping simulation and broadcasting state via WebSockets."""
    report_file_path = PROJECT_ROOT / "simulation_report.json"
    while True:
        try:
            if not is_paused:
                report = simulation.step()
            else:
                report = simulation._compute_report(simulation.step_count)

            report_dict = report.to_dict()
            report_dict["mavlink_connected"] = mavlink_bridge.is_connected
            report_dict["is_paused"] = is_paused

            # Sync physical drone telemetry to video streamer HUD
            if simulation.mode == "hybrid_real" and report_dict["drones"]:
                p_drone = report_dict["drones"][0]
                video_streamer.update_telemetry({
                    "lat": p_drone.get("lat", 11.5360),
                    "lon": p_drone.get("lon", 76.1390),
                    "altitude": p_drone.get("altitude", 35.0),
                    "heading": p_drone.get("heading", 0.0),
                    "pitch": p_drone.get("pitch", 0.0),
                    "roll": p_drone.get("roll", 0.0),
                    "battery": p_drone.get("battery", 90.0),
                    "speed": p_drone.get("speed", 12.0),
                    "telemetry_source": p_drone.get("telemetry_source", "emulated"),
                    "mode": simulation.mode,
                })

            # Save report to disk for backward compatibility
            try:
                with open(report_file_path, "w", encoding="utf-8") as f:
                    json.dump(report_dict, f, indent=2)
            except Exception:
                pass

            # Push to connected WebSocket clients
            if active_websockets:
                payload = json.dumps(report_dict)
                disconnected = []
                for ws in active_websockets:
                    try:
                        await ws.send_text(payload)
                    except Exception:
                        disconnected.append(ws)
                for ws in disconnected:
                    if ws in active_websockets:
                        active_websockets.remove(ws)

            await asyncio.sleep(0.12)  # ~8.3 Hz refresh
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in simulation loop: {e}")
            await asyncio.sleep(0.5)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Starting SARAS Swarm Mission Server...")
    await mavlink_bridge.start()
    asyncio.create_task(simulation_loop())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await mavlink_bridge.stop()


# REST Endpoints
@app.get("/")
def root_redirect():
    return RedirectResponse(url="/dashboard/index.html")


@app.get("/api/status")
def get_status():
    report = simulation._compute_report(simulation.step_count)
    data = report.to_dict()
    data["mavlink_status"] = {
        "connected": mavlink_bridge.is_connected,
        "connection_str": mavlink_bridge.connection_str,
        "packets_received": mavlink_bridge.latest_telemetry.get("packet_count", 0),
    }
    data["is_paused"] = is_paused
    return data


@app.post("/api/mode")
def set_system_mode(req: ModeRequest):
    if req.mode not in ("pure_sim", "hybrid_real"):
        raise HTTPException(status_code=400, detail="Invalid mode. Choose 'pure_sim' or 'hybrid_real'")
    simulation.set_mode(req.mode)
    logger.info(f"System mode switched to: {req.mode}")
    return {"status": "ok", "mode": simulation.mode}


@app.post("/api/drones/count")
def set_swarm_count(req: DroneCountRequest):
    if req.count < 1 or req.count > 12:
        raise HTTPException(status_code=400, detail="Drone count must be between 1 and 12")
    simulation.set_drone_count(req.count)
    logger.info(f"Swarm size updated to: {req.count} drones")
    return {"status": "ok", "drone_count": len(simulation.drones)}


@app.post("/api/command")
def send_command(req: CommandRequest):
    global is_paused
    cmd = req.command.lower()
    if cmd == "pause":
        is_paused = True
    elif cmd == "resume":
        is_paused = False
    elif cmd == "reset":
        simulation.initialize()
        is_paused = False
    elif cmd == "reassign":
        simulation.reallocate_sectors()
    elif cmd == "rtl":
        if req.drone_id:
            for d in simulation.drones:
                if d.drone_id == req.drone_id:
                    d.health = "returning"
        else:
            for d in simulation.drones:
                d.health = "returning"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown command: {cmd}")
    return {"status": "ok", "command": cmd, "is_paused": is_paused}


@app.post("/api/agent/query")
def ask_agent(req: AgentQueryRequest):
    answer = simulation.answer_operator_question(req.query)
    return {"status": "ok", "query": req.query, "answer": answer}


@app.get("/api/video/feed")
def video_feed():
    """MJPEG live camera stream for physical Drone-01."""
    return StreamingResponse(
        video_streamer.generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    logger.info(f"WebSocket client connected. Total active: {len(active_websockets)}")
    try:
        while True:
            # Keep connection open and accept operator ping/commands
            data = await websocket.receive_text()
            try:
                cmd_data = json.loads(data)
                if "command" in cmd_data:
                    send_command(CommandRequest(**cmd_data))
            except Exception:
                pass
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total active: {len(active_websockets)}")


# Mount dashboard directory as static files
dashboard_dir = PROJECT_ROOT / "dashboard"
if dashboard_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_dir), html=True), name="dashboard")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=False)
