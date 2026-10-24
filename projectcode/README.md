# SARAS Simulation

This project implements a modular swarm simulation for the SARAS (Search And Rescue Autonomous Swarm) concept described in `IDEA.md`.

## Objective

The simulator captures the software-track core of the system:

- multi-drone coverage of a disaster zone
- sector allocation using an auction-style market strategy
- fault tolerance with dynamic reassignment
- victim detection and rescue prioritization
- a minimal agentic AI + RAG layer for support questions
- a dashboard-style summary report for the swarm state

## Why this exists

The project is intentionally designed as a research-oriented simulation baseline before hardware integration. The software logic is structured so that it can later scale to a real ROS2/PX4 swarm and a FastAPI dashboard without major refactoring.

## Project structure

- `saras_sim/config.py` – configurable simulation parameters
- `saras_sim/models.py` – data model for drones, sectors, victims, and reports
- `saras_sim/allocator.py` – auction-style sector assignment logic
- `saras_sim/agents.py` – rescue prioritization and RAG knowledge agent
- `saras_sim/simulator.py` – swarm simulation loop and metrics
- `run_demo.py` – example entry point for running the scenario
- `dashboard/` – responsive operator dashboard for live swarm status

## Quick start

```bash
cd projectcode
python run_demo.py
```

The command prints a scenario summary and writes a JSON report to `simulation_report.json`.

## Dashboard

Run the simulator first, then serve the project directory:

```bash
python run_demo.py
python -m http.server 8000
```

Open `http://localhost:8000/dashboard/` in a browser. The dashboard uses Leaflet with OpenStreetMap tiles and visualizes the tactical map, fleet health, sector progress, victim queue, and rescue-agent recommendation.

The map polls `simulation_report.json` every three seconds. To see fresh telemetry on the map, rerun `python run_demo.py` while the dashboard is open, then watch the map, markers, popups, and telemetry timestamp update automatically.

## Architecture summary

1. Sector grid generation over a disaster area
2. Auction-based assignment of sectors to active drones
3. Search simulation, victim detection, and battery degradation
4. Failure handling with reassignment of incomplete sectors
5. Rescue recommendation generation
6. Retrieval-based SOP answers for operator queries

## Extensibility

This baseline is intentionally simple but modular. The next phases can extend it with:

- learned allocation policy instead of the auction baseline
- ROS2/PX4 message compatibility
- FastAPI backend endpoints
- Next.js dashboard components
- integration with real YOLO detections
