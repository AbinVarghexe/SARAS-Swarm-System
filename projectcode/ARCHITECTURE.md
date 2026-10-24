# SARAS System Architecture

## 1. System objective

SARAS is a multi-layer autonomous search-and-rescue swarm system that mixes:

- real drone autonomy
- simulation-first swarm experimentation
- edge ML inference
- swarm-level task allocation
- agentic rescue decision support
- RAG-based rescue guidance
- dashboard visualization

The goal is to validate the software architecture in simulation before integrating the physical drone as one live swarm member.

---

## 2. High-level architecture

The system is organized into six major layers:

1. Mission layer
   - disaster scenario definition
   - terrain layout
   - search zone geometry
   - victim distribution and severity map

2. Swarm layer
   - drones as autonomous agents
   - flight behavior / route planning / sector coverage
   - health tracking and heartbeat

3. Coordination layer
   - sector allocator
   - fault-tolerance logic
   - reassignment policy
   - swarm scheduling

4. AI layer
   - edge detection model
   - rescue prioritization agent
   - mapping agent
   - knowledge/retrieval agent

5. Integration layer
   - backend API
   - telemetry contract
   - shared message schema
   - dashboard data feeds

6. Operator layer
   - live dashboard
   - mission monitoring
   - rescue recommendations
   - human-in-the-loop decisions

---

## 3. Core subsystem breakdown

### 3.1 Simulation engine

Purpose:
- model the disaster area
- simulate multiple drones
- evaluate coverage, detection, failure, and recovery

Primary responsibilities:
- generate sectors and victims
- run time-stepped simulation loop
- assign tasks to drones
- monitor swarm health and coverage

Key classes:
- `SwarmSimulation`
- `SimulationConfig`
- `DisasterMission`
- `Sector`
- `Drone`
- `Victim`

### 3.2 Coordination and allocation

Purpose:
- assign sectors fairly and efficiently
- handle dynamic reassignment when a drone fails or finishes early

Baseline strategy:
- auction-based sector allocation

Advanced strategy:
- learned policy (multi-agent RL) compared against the auction baseline

Key class:
- `SectorAllocator`

### 3.3 Rescue and decision agents

Purpose:
- turn detections into actionable rescue decisions
- prioritize victims and produce rescue recommendations

Key classes:
- `RescueAgent`
- `KnowledgeAgent`

### 3.4 Metrics and evaluation

Purpose:
- measure the quality of swarm behavior and research contributions

Core metrics:
- coverage ratio
- victim detection latency
- redundant search rate
- recovery time after failure
- mission completion time
- average response distance

Key class:
- `SimulationMetrics`

---

## 4. Runtime data flow

1. Mission is initialized with an arena and set of search sectors.
2. Drones are created and assigned initial sectors.
3. Each step updates drone movement and coverage.
4. Victims are detected based on distance and probability.
5. Detected victims are ranked for rescue priority.
6. Failure cases trigger reassignment logic.
7. The system produces a simulation report, including metrics and recommendations.
8. The dashboard and backend consume the same data model.

---

## 5. Message contract for future integration

To avoid hardware/software bottlenecks, the following telemetry contract must be defined early:

- drone_id
- timestamp
- position (x, y, z)
- yaw / heading
- battery
- health
- current sector
- detection list
- speed
- status mode
- mission status

This contract should be shared by both the hardware and software track so the physical drone can later be integrated without rewriting the swarm logic.

---

## 6. Proposed implementation sequence

### Phase 1: Simulation foundation
- complete configurable mission generation
- validate sector assignment and coverage
- implement detection and failure handling

### Phase 2: Research-grade evaluation
- add metrics for efficiency and resilience
- compare auction baseline vs. learned policy
- generate structured evaluation tables

### Phase 3: AI and decision support
- enhance victim prioritization
- integrate knowledge/RAG layer
- test question answering on rescue procedures

### Phase 4: Backend + dashboard
- expose FastAPI endpoints for live swarm state
- build a minimal frontend dashboard with map and telemetry

### Phase 5: Real-drone integration
- connect the physical drone as one live node
- replace simulated detections with actual onboard inference
- validate same message schema against the simulation path

---

## 7. Recommended project structure

```text
projectcode/
    ARCHITECTURE.md
    run_demo.py
    simulation_report.json
    requirements.txt
    saras_sim/
        __init__.py
        config.py
        models.py
        mission.py
        allocator.py
        agents.py
        metrics.py
        simulator.py
        dashboard_data.py
    backend/
        app.py
        routes/
        schemas/
    dashboard/
        app/
    edge_ml/
        README.md
    swarm_ml/
        README.md
    docs/
        system-design.md
        evaluation-plan.md
```

---

## 8. Success criteria for the defined system

The architecture is considered healthy when:

- one simulator can run many drone agents without code changes
- the same telemetry model works for both simulation and physical drone
- sector allocation is configurable (baseline vs. learned)
- failure handling is automatic and measurable
- rescue recommendation quality is generated from detected victims
- the dashboard reflects the same state used in the simulator

This architecture forms the base for the final system demo and the two research papers described in IDEA.md.
