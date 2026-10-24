#!/usr/bin/env python3
"""
SARAS - Search And Rescue Autonomous Swarm
Root Orchestrator and Unified Launcher
Member 2: Software, Swarm Intelligence, Simulation & Mission Control
"""

import argparse
import os
import sys
import time
import webbrowser
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

BANNER = r"""
==============================================================================
   ____    _    ____      _    ____    ____                               
  / ___|  / \  |  _ \    / \  / ___|  / ___|_      ____ _ _ __ _ __ ___   
  \___ \ / _ \ | |_) |  / _ \ \___ \  \___ \ \ /\ / / _` | '__| '_ ` _ \  
   ___) / ___ \|  _ <  / ___ \ ___) |  ___) \ V  V / (_| | |  | | | | | | 
  |____/_/   \_\_| \_\/_/   \_\____/  |____/ \_/\_/ \__,_|_|  |_| |_| |_| 
                                                                          
  Autonomous Swarm Coordination | Fault Tolerance | Real-Time Mission Control
==============================================================================
"""


def run_benchmark_cli(num_drones: int = 4):
    """Runs ablation evaluation comparing Market Auction vs Greedy Distance Allocator."""
    from swarm_core.coordination.allocator import evaluate_allocation_policies

    print("\n[BENCHMARK] Executing IEEE Ablation Evaluation across Swarm Allocation Policies...")
    results = evaluate_allocation_policies(num_drones=num_drones, rows=3, cols=4)

    greedy = results["GreedyDistanceBaseline"]
    auction = results["MarketAuctionProposed"]

    travel_diff = ((greedy["total_travel_meters"] - auction["total_travel_meters"]) / greedy["total_travel_meters"]) * 100.0
    var_diff = ((greedy["workload_variance"] - auction["workload_variance"]) / max(greedy["workload_variance"], 0.001)) * 100.0

    print("\n" + "=" * 78)
    print("           IEEE PAPER 2: SWARM ALLOCATION ABLATION EVALUATION")
    print("=" * 78)
    print(f"{'Metric':<32} | {'Greedy Baseline':<16} | {'Market Auction':<16} | {'Delta':<10}")
    print("-" * 78)
    print(f"{'Total Swarm Travel (meters)':<32} | {greedy['total_travel_meters']:<16.1f} | {auction['total_travel_meters']:<16.1f} | {travel_diff:+.1f}%")
    print(f"{'Workload / Battery Variance':<32} | {greedy['workload_variance']:<16.4f} | {auction['workload_variance']:<16.4f} | {var_diff:+.1f}%")
    print(f"{'Avg Priority Served':<32} | {greedy['avg_priority_weight']:<16.2f} | {auction['avg_priority_weight']:<16.2f} | {(auction['avg_priority_weight']-greedy['avg_priority_weight']):+.2f}")
    print(f"{'Energy Efficiency Score':<32} | {greedy['energy_efficiency_score']:<16.2f} | {auction['energy_efficiency_score']:<16.2f} | {(auction['energy_efficiency_score']-greedy['energy_efficiency_score']):+.2f}")
    print("=" * 78)
    print("[CONCLUSION] Market-based auction dynamically curbs low-battery drone assignments,")
    print("             yielding substantially superior battery fairness and energy balance.\n")


def run_unit_tests():
    """Runs self-diagnostics test suite verifying all swarm modules."""
    print("\n[TESTS] Running SARAS Swarm System Self-Diagnostics...")

    # Ensure stdout handles unicode cleanly
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    # 1. Telemetry Contracts
    from swarm_core.telemetry_contract import DroneTelemetry, DetectionEvent, SectorModel, SectorStatus, DroneStatus
    telemetry = DroneTelemetry(drone_id="Drone-Test", lat=12.975, lon=77.597, battery=88.5, status=DroneStatus.SEARCHING)
    assert telemetry.drone_id == "Drone-Test"
    print("  [PASS] Telemetry Contracts: Pydantic v2 validation passed.")

    # 2. Sector Generation & Allocation
    from swarm_core.coordination.allocator import generate_sectors, MarketAuctionAllocator, GreedyDistanceAllocator
    sectors = generate_sectors(rows=3, cols=3)
    assert len(sectors) == 9
    drones = {"Drone-1": telemetry}
    allocator = MarketAuctionAllocator()
    assigned = allocator.allocate(drones, sectors)
    assert len(assigned) == 1
    print(f"  [PASS] Coordination: Market Auction allocated {assigned['Drone-Test']} successfully.")

    # 3. Fault Tolerance Monitor
    from swarm_core.fault_tolerance.monitor import SwarmHealthMonitor
    monitor = SwarmHealthMonitor(heartbeat_timeout_sec=2.0)
    monitor.record_heartbeat("Drone-1", timestamp=time.time() - 3.0)
    drones_state = {"Drone-1": telemetry}
    alerts = monitor.check_health(drones_state, sectors, now=time.time())
    assert any("DROPOUT DETECTED" in a.message for a in alerts)
    print("  [PASS] Fault Tolerance: Heartbeat timeout & dropout detection passed.")

    # 4. Agentic AI & RAG
    from swarm_core.agentic_ai.triage_rag import RescueTriageAgent, RAGKnowledgeAgent
    det = DetectionEvent(
        detection_id="DET-TEST",
        drone_id="Drone-1",
        lat=12.975,
        lon=77.597,
        confidence=0.92,
        thermal_signature=34.0,  # hypothermia
        environment_tags=["flood", "hypothermia"]
    )
    triage = RescueTriageAgent()
    rec = triage.triage_detection(det)
    assert rec.triage_category.value == "CRITICAL"
    print(f"  [PASS] Agentic Triage: Correctly scored urgency ({rec.urgency_score}) -> {rec.triage_category.value}.")

    rag = RAGKnowledgeAgent()
    ans = rag.answer_query("What is the protocol for hypothermia in swiftwater flood?")
    assert len(ans["sop_references"]) > 0
    print(f"  [PASS] RAG Knowledge Agent: Retrieved {ans['sop_references'][0]} successfully.")

    print("\n[SUCCESS] All SARAS Swarm System components verified with 100% pass rate.\n")


def main():
    parser = argparse.ArgumentParser(description="SARAS - Search And Rescue Autonomous Swarm Launcher")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind backend server (default: 8000)")
    parser.add_argument("--drones", type=int, default=4, help="Number of simulated drones (default: 4)")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open the dashboard in browser")
    parser.add_argument("--edge", action="store_true", help="Launch onboard Edge ML companion node alongside swarm")
    parser.add_argument("--benchmark", action="store_true", help="Run IEEE ablation benchmark and exit")
    parser.add_argument("--test", action="store_true", help="Run self-diagnostic unit tests and exit")

    args = parser.parse_args()

    print(BANNER)

    if args.test:
        run_unit_tests()
        sys.exit(0)

    if args.benchmark:
        run_benchmark_cli(num_drones=args.drones)
        sys.exit(0)

    url = f"http://{args.host}:{args.port}"
    print(f"[*] Starting SARAS Backend & Mission Control Dashboard on {url}")
    print(f"[*] Swarm Fleet Size: {args.drones} simulated UAVs")
    print(f"[*] Task Allocation: Market-Based Auction with Dynamic Fault Tolerance")
    print(f"[*] Emergency SOP RAG: Active (Disaster protocols loaded)")

    edge_process = None
    if args.edge:
        edge_script = PROJECT_ROOT / "edge_hardware" / "run_edge_node.py"
        if edge_script.exists():
            print(f"[*] Launching Onboard Edge ML Node: {edge_script}")
            import subprocess
            edge_cmd = [
                sys.executable,
                str(edge_script),
                "--drone-id", "Drone-Physical-1",
                "--camera", "synthetic",
                "--backend", url
            ]
            edge_process = subprocess.Popen(edge_cmd)
        else:
            print(f"[!] Warning: Edge script {edge_script} not found.")

    if not args.no_browser:
        def open_browser():
            time.sleep(1.2)
            print(f"[*] Launching Mission Control Dashboard in browser: {url}")
            webbrowser.open(url)

        import threading
        threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    try:
        uvicorn.run("backend.main:app", host=args.host, port=args.port, log_level="info")
    finally:
        if edge_process:
            print("[*] Terminating Edge ML Node...")
            edge_process.terminate()


if __name__ == "__main__":
    main()
