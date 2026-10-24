import argparse
import json
import sys
from pathlib import Path

from saras_sim import SimulationConfig, SwarmSimulation


def run_cli_sim() -> None:
    config = SimulationConfig(
        arena_width=1000.0,
        arena_height=1000.0,
        drone_count=4,
        sector_rows=3,
        sector_cols=3,
        victim_count=8,
        max_steps=30,
        failure_probability=0.05,
        coverage_threshold=0.85,
        search_radius=75.0,
        mode="pure_sim",
    )
    simulation = SwarmSimulation(config)
    report = simulation.run()

    output_path = Path(__file__).with_name("simulation_report.json")
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

    print(report.summary())
    print(f"\nJSON report written to: {output_path}")
    print("\nSample operator question:")
    print(simulation.answer_operator_question("What is the safest rescue procedure for a buried victim?"))


def run_server() -> None:
    import uvicorn
    print("\n" + "=" * 65)
    print("  SARAS TACTICAL SWARM COMMAND SERVER")
    print("  Access Console at: http://localhost:8000/dashboard/index.html")
    print("  MAVLink Bridge listening on UDP: 127.0.0.1:14550 (Mission Planner)")
    print("  Video Feed: http://localhost:8000/api/video/feed")
    print("=" * 65 + "\n")
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="SARAS Swarm System Launcher")
    parser.add_argument("--cli", action="store_true", help="Run offline headless simulation and export report")
    parser.add_argument("--server", action="store_true", default=True, help="Launch live FastAPI mission server (default)")
    args = parser.parse_args()

    if args.cli:
        run_cli_sim()
    else:
        run_server()


if __name__ == "__main__":
    main()

