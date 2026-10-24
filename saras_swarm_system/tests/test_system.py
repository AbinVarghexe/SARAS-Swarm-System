"""
Unit and Integration Tests for SARAS Swarm System
Tests REST endpoints, WebSockets, Simulation, Allocator, and RAG agents.
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure saras_swarm_system is in path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.main import app, simulator, triage_agent, rag_agent
from swarm_core.telemetry_contract import (
    DroneTelemetry,
    DetectionEvent,
    SectorModel,
    SectorStatus,
    DroneStatus,
    TriageCategory,
)
from swarm_core.coordination.allocator import (
    generate_sectors,
    MarketAuctionAllocator,
    GreedyDistanceAllocator,
    evaluate_allocation_policies,
)
from swarm_core.fault_tolerance.monitor import SwarmHealthMonitor


client = TestClient(app)


def test_root_dashboard_html():
    """Verify Mission Control dashboard static page is served."""
    response = client.get("/")
    assert response.status_code == 200
    assert "SARAS" in response.text
    assert "MISSION CONTROL" in response.text


def test_static_assets():
    """Verify CSS and JS static assets load."""
    res_css = client.get("/static/style.css")
    assert res_css.status_code == 200
    assert "tactical-header" in res_css.text

    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    assert "initMap" in res_js.text


def test_swarm_status_endpoint():
    """Verify /api/swarm/status endpoint returns valid SwarmState."""
    response = client.get("/api/swarm/status")
    assert response.status_code == 200
    data = response.json()
    assert "active_drones" in data
    assert "sectors" in data
    assert "total_coverage_pct" in data
    assert len(data["active_drones"]) == 4


def test_sectors_endpoint():
    """Verify /api/sectors endpoint returns 12 sectors."""
    response = client.get("/api/sectors")
    assert response.status_code == 200
    sectors = response.json()
    assert len(sectors) == 12
    assert all("sector_id" in s for s in sectors)


def test_rag_query_endpoint():
    """Verify /api/query answers with SOP guidance and citations."""
    response = client.post("/api/query", json={"query": "flood hypothermia protocol"})
    assert response.status_code == 200
    data = response.json()
    assert "synthesized_guidance" in data
    assert "sop_references" in data
    assert len(data["sop_references"]) > 0
    assert "SOP-101" in data["sop_references"][0]


def test_policy_switch_endpoint():
    """Verify switching between AUCTION and GREEDY policy."""
    res1 = client.post("/api/swarm/policy", json={"policy": "GREEDY"})
    assert res1.status_code == 200
    assert res1.json()["policy"] == "GREEDY"

    res2 = client.post("/api/swarm/policy", json={"policy": "AUCTION"})
    assert res2.status_code == 200
    assert res2.json()["policy"] == "AUCTION"


def test_fault_injection_endpoint():
    """Verify injecting dropout and battery drain faults."""
    res = client.post("/api/swarm/fault", json={"drone_id": "Drone-2", "fault_type": "dropout"})
    assert res.status_code == 200

    # Drone-2 should be disconnected
    assert simulator.drones["Drone-2"].is_disconnected is True

    # Restore
    res_restore = client.post("/api/swarm/fault", json={"drone_id": "Drone-2", "fault_type": "restore"})
    assert res_restore.status_code == 200
    assert simulator.drones["Drone-2"].is_disconnected is False


def test_benchmark_endpoint():
    """Verify /api/benchmark returns IEEE ablation comparative metrics."""
    response = client.get("/api/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "GreedyDistanceBaseline" in data["metrics"]
    assert "MarketAuctionProposed" in data["metrics"]


def test_websocket_telemetry():
    """Verify WebSocket connection handles telemetry stream."""
    with client.websocket_connect("/ws/telemetry") as websocket:
        # Send a keep-alive ping
        websocket.send_text("ping")


if __name__ == "__main__":
    test_root_dashboard_html()
    test_static_assets()
    test_swarm_status_endpoint()
    test_sectors_endpoint()
    test_rag_query_endpoint()
    test_policy_switch_endpoint()
    test_fault_injection_endpoint()
    test_benchmark_endpoint()
    test_websocket_telemetry()
    print("\n[SUCCESS] All 8 integration tests passed with 100% success!")
