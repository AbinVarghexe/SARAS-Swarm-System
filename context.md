# SARAS: Search And Rescue Autonomous Swarm
## Technical Project Context & Architecture Reference for AI Coding Agents

> **Document Type:** Project Context & Codebase Specification  
> **Target Audience:** Autonomous Coding Agents & AI Pair Programmers  
> **Project Title:** SARAS (Search And Rescue Autonomous Swarm)  
> **Academic Context:** B.Tech Final Year Project, Department of Computer Science & Engineering, Amal Jyothi College of Engineering (Affiliated with APJ Abdul Kalam Technological University - KTU)  
> **Repository Root:** `d:\DEV\Final Year Project`

---

## 1. Executive Summary

**SARAS** is an integrated, autonomous multi-UAV (Unmanned Aerial Vehicle) robotic swarm system engineered for rapid disaster response operations (e.g., landslides, flash floods, collapsed structures, earthquake debris, and wilderness search operations). The primary operational objective is to compress the victim localization timeline within the critical **"72-Hour Golden Window"**.

The core engineering innovation lies in its **Dual-Track Machine Learning Architecture**:
1. **Edge ML Subsystem (Hardware Lead):** Real-time onboard neural inference running on an ARM64 companion computer (Raspberry Pi 4/5) interfaced with a Pixhawk PX4 flight controller on a physical 450mm quadrotor frame. It deploys an ONNX-quantized YOLOv8 nano model for low-latency aerial human detection.
2. **Swarm Intelligence Subsystem (Software Lead):** Decentralized multi-agent coordination, market-based auction task allocation, heartbeat-driven fault tolerance with dynamic orphan sector reassignment, an agentic START casualty triage calculator, a zero-dependency TF-IDF RAG emergency standard operating procedure (SOP) retriever, a real-time FastAPI async streaming backend, and a Leaflet-based dark tactical Mission Control dashboard.

**Zero-Friction Scale Guarantee:** The entire communication schema and telemetry contract are built so that the identical coordination protocols operate whether connected to **1 physical quadrotor** or **$N$ simulated UAVs**.

---

## 2. Team Division & Functional Tracks

| Dimension | Track 1: Hardware & Edge ML Lead | Track 2: Software, Swarm & Mission Control Lead |
| :--- | :--- | :--- |
| **Primary Domain** | Quadrotor avionics, companion computer, edge perception | Swarm coordination, simulation, backend, dashboard, agentic AI |
| **Compute Node** | Pixhawk 4/6C + Raspberry Pi 4/5 (ARM64) | Ground Control Station / Server (FastAPI + Async WebSockets) |
| **Inference/ML** | YOLOv8n (ONNX Runtime, INT8/FP32 quantized, 10.7 FPS) | Market Auction Cost Engine, TF-IDF SOP RAG, START Triage (Operational); CTDE-MAPPO & MAML (Future Scope) |
| **Protocols** | MAVLink2 (UART TELEM2 @ 57600/921600 baud), CSI Camera | WebSockets (10 Hz broadcast), REST APIs, Pydantic v2 telemetry |
| **Simulation Role** | Companion node hardware-in-the-loop (HIL) feed injection | Multi-UAV kinematic simulator, boustrophedon lawnmower search sweeps |

---

## 3. Directory Layout & Key File Map

```
D:\DEV\Final Year Project\
│
├── context.md                          # THIS FILE: Ground-truth reference for coding agents
├── IDEA.md                             # Original platform vision, constraints, and project goals
├── content.md                          # 73KB+ KTU-compliant complete thesis manuscript text
│
├── saras_swarm_system/                 # PRIMARY UNIFIED PRODUCTION & SIMULATION CODEBASE
│   ├── run_saras.py                    # Unified launcher CLI (tests, benchmarks, simulation)
│   ├── requirements.txt                # Python dependencies (fastapi, uvicorn, pydantic, etc.)
│   ├── ARCHITECTURE.md                 # Mathematical formulations & IEEE paper specs
│   ├── README.md                       # Quickstart & architectural guide
│   │
│   ├── swarm_core/                     # CORE SWARM ALGORITHMS & TELEMETRY
│   │   ├── telemetry_contract.py       # Pydantic v2 schemas: telemetry, detections, sectors, alerts
│   │   ├── coordination/
│   │   │   └── allocator.py            # Market Auction Allocator & Greedy Baseline for ablation
│   │   ├── fault_tolerance/
│   │   │   └── monitor.py              # 10 Hz Watchdog, heartbeat timeouts & orphan sector reassignment
│   │   ├── simulation/
│   │   │   └── swarm_sim.py            # Multi-UAV kinematic engine with boustrophedon sweeps
│   │   └── agentic_ai/
│   │       └── triage_rag.py           # START Triage Urgency Scorer & TF-IDF Emergency SOP RAG
│   │
│   ├── backend/                        # REAL-TIME ASYNC SERVER
│   │   ├── main.py                     # FastAPI REST API, WebSocket streams, background loop
│   │   ├── video_streamer.py           # Synthetic & live aerial camera MJPEG streaming
│   │   └── report_generator.py         # Automated post-mission PDF/JSON audit generator
│   │
│   ├── dashboard/                      # TACTICAL MISSION CONTROL (FRONTEND)
│   │   ├── index.html                  # Main Mission Control tactical dashboard
│   │   ├── triage.html                 # Specialized casualty medical triage board
│   │   ├── style.css                   # Dark tactical command center styling
│   │   └── app.js                      # Leaflet map renderer, WebSocket client & UI controls
│   │
│   └── edge_hardware/                  # PHYSICAL COMPANION COMPUTER SUBSYSTEM
│       ├── run_edge_node.py            # Entry point for Raspberry Pi onboard node
│       ├── config/edge_config.py       # Serial ports, camera resolution, backend URLs
│       ├── inference/detector.py       # ONNX Runtime YOLOv8n detector with bounding box parsing
│       ├── camera/capture.py           # OpenCV / CSI libcamera video capture abstraction
│       ├── telemetry/telemetry_sender.py # MAVLink-to-FastAPI telemetry bridge
│       └── benchmark/                  # Latency, FPS, and thermal benchmarking suite
│
├── projectcode/                        # PROTOTYPE ARCHIVE (Earlier iteration of simulation & backend)
│   ├── run_demo.py                     # Initial simulator runner
│   ├── saras_sim/                      # Legacy simulation modules
│   └── backend/                        # Legacy Flask/FastAPI backend
│
├── hardware/                           # PHYSICAL HARDWARE ASSETS & WIRING
│   ├── 01_bom/                         # Bill of Materials (Frame, Motors, ESCs, Pixhawk, Pi)
│   ├── 03_flight_stack/                # PX4 / ArduPilot parameter dumps
│   ├── 04_companion/                   # Raspberry Pi 4/5 Debian Bookworm setup notes
│   ├── 06_telemetry/                   # Wiring pinouts (Pixhawk TELEM2 UART to Pi GPIO 14/15)
│   └── 10_checklists/                  # Pre-flight hardware safety checklists
│
└── ProjectReport/                      # ACADEMIC KTU REPORT & LATEX COMPILATION
    ├── bin/tectonic.exe                # Zero-dependency, standalone LaTeX compiler
    ├── Report_Template_Placeholder/    # LaTeX source files (.tex)
    │   ├── main.tex                    # Master LaTeX entrypoint
    │   ├── intro.tex, litsurvey.tex    # Chapters 1 & 2
    │   ├── implementation.tex          # Chapter 3 (System Architecture & Math)
    │   ├── results.tex, conclusion.tex # Chapters 4 & 5 (Ablation tables, graphs)
    │   ├── compile_report.py           # Python script wrapping tectonic.exe
    │   ├── main.pdf                    # Compiled final project report PDF
    │   └── assets/                     # High-res diagrams (trajectories, coalitions, architecture)
    └── Report Format Project/          # Institutional reference format
```

---

## 4. Technical Specifications of Core Modules

### 4.1 Telemetry Contract (`swarm_core/telemetry_contract.py`)
All communications between UAVs, the simulation loop, the backend, and the dashboard rely on strictly validated **Pydantic v2** models:
* `DroneTelemetry`: `drone_id`, `lat`, `lon`, `alt`, `heading`, `battery` ($0-100\%$), `speed`, `status` (`IDLE`, `NAVIGATING`, `SEARCHING`, `RETURNING`, `FAILED`, `CHARGING`), `current_sector_id`, `waypoints_completed`.
* `DetectionEvent`: `detection_id`, `drone_id`, `lat`, `lon`, `confidence`, `thermal_signature`, `environment_tags` (`flood`, `fire`, `pinned`, `hypothermia`), `image_snapshot`.
* `SectorModel`: `sector_id`, `polygon_coords`, `center_lat`, `center_lon`, `status` (`UNASSIGNED`, `ASSIGNED`, `SEARCHING`, `COVERED`), `assigned_drone_id`, `priority_weight` ($1.0-3.0$), `search_progress`.
* `RescueRecommendation`: `recommendation_id`, `detection_id`, `triage_category` (`CRITICAL`, `URGENT`, `STABLE`, `EXPECTANT`), `urgency_score` ($0-100$), `required_kit`, `dispatch_priority`.
* `SwarmAlert`: `alert_id`, `timestamp`, `level` (`INFO`, `WARNING`, `CRITICAL`), `drone_id`, `message`.

### 4.2 Market-Based Auction Allocator (`swarm_core/coordination/allocator.py`)
* Decomposes the operational bounding box into an $M \times N$ sector grid.
* When a sector becomes available, bids are evaluated via a composite cost objective:
  $$\text{Bid}(i, s) = w_d \cdot D_{\text{haversine}}(u_i, c_s) + w_b \cdot \left(\frac{100 - B_i}{100}\right)^2 + w_u \cdot (3.0 - P_s)$$
  Where $D_{\text{haversine}}$ is the Euclidean/Haversine distance, $B_i$ is battery percentage (with quadratic penalization as battery drops), and $P_s$ is sector priority.
* Prevents starvation and heavily suppresses assigning low-battery drones to distant sectors.
* Includes `GreedyDistanceAllocator` for comparative ablation benchmarking.

### 4.3 Swarm Fault Tolerance & Watchdog (`swarm_core/fault_tolerance/monitor.py`)
* Maintains a rolling heartbeat table updated at 10 Hz.
* If $(t_{\text{current}} - t_{\text{last\_heartbeat}}) > 5.0\text{s}$, or battery drops below failsafe threshold ($\le 20\%$), the node is marked `FAILED`.
* The orphan sector assigned to that drone is immediately revoked, tagged `UNASSIGNED`, and re-injected into the Market Auction.
* Achieves dynamic recovery and sector reassignment in **sub-1.2 seconds**.

### 4.4 Simulation Engine (`swarm_core/simulation/swarm_sim.py`)
* Supports $N$ simultaneous drones running at configurable update rates (default: 10 Hz).
* Implements boustrophedon sweep trajectory generation with coordinate waypoint following.
* Simulates battery draw proportional to flight velocity and hover state.
* Seeding engine spawns victims with realistic environmental hazards.
* Dynamic fault injection methods: `inject_dropout(drone_id)`, `drain_battery(drone_id, level)`, `restore_drone(drone_id)`.

### 4.5 Agentic AI & RAG Subsystem (`swarm_core/agentic_ai/triage_rag.py`)
* **Rescue Triage Agent:** Applies Simple Triage and Rapid Treatment (START) rules, factoring in physiological indicators (body temperature), trap state, and environmental hazard proximity to compute urgency scores ($0-100$).
* **RAG Knowledge Agent:** Standalone, zero-dependency TF-IDF retrieval system over structured SOP knowledge bases (`Disaster Management Guidelines`, `Swiftwater Extraction Protocols`, `Crush Syndrome Triage`, `Hazardous Material Exposure`).

### 4.6 Backend & Video Streaming (`backend/main.py`, `backend/video_streamer.py`)
* FastAPI application hosting REST endpoints (`/api/swarm/state`, `/api/drone/{id}/fault`, `/api/rag/query`, `/api/benchmark`, `/api/report/generate`).
* WebSocket routes:
  * `/ws/telemetry`: 10 Hz streaming of the unified `SwarmState`.
  * `/ws/alerts`: Asynchronous event channel for failures, victim detections, and sector completions.
* MJPEG synthetic/camera feed streamer with YOLO bounding box overlays.

### 4.7 Tactical Mission Control (`dashboard/`)
* Built with clean vanilla JavaScript + Leaflet.js, styled with an aviation dark-mode theme.
* Features:
  * Real-time drone position markers with orientation arrows and battery rings.
  * Interactive sector polygon overlays updating color dynamically (`Unassigned` = gray, `Searching` = cyan, `Covered` = green).
  * Pulsing victim detection markers with casualty triage modals.
  * Fault injection panel allowing manual dropout/battery drain testing during live demonstrations.
  * SOP interactive search bar querying the RAG knowledge agent.

---

## 5. Standard Operating Procedures (How to Run Everything)

### 5.1 Verification & Self-Diagnostics
To verify that all Pydantic contracts, allocators, fault handlers, and RAG agents pass unit tests:
```bash
python saras_swarm_system/run_saras.py --test
```
*(Expected: 100% pass rate across contracts, allocator, fault monitor, triage agent, and RAG agent).*

### 5.2 Running the Full Interactive Simulation & Mission Control
To start the backend and automatically open the tactical dashboard in the browser:
```bash
python saras_swarm_system/run_saras.py
```
* **Default URL:** `http://127.0.0.1:8000`
* **Custom Fleet Size (e.g., 6 drones):**
  ```bash
  python saras_swarm_system/run_saras.py --drones 6
  ```

### 5.3 Running the IEEE Ablation Benchmark
To generate the quantitative comparison between Market Auction and Greedy Distance Allocation:
```bash
python saras_swarm_system/run_saras.py --benchmark
```

### 5.4 Running the Edge Hardware Subsystem (Simulated or Real)
To run the companion computer detection pipeline:
```bash
python saras_swarm_system/edge_hardware/run_edge_node.py --drone-id Drone-Physical-1 --camera synthetic
```

### 5.5 Compiling the KTU Project Report
The LaTeX report compiles with zero external dependencies using the bundled Tectonic binary:
```bash
cd "ProjectReport\Report_Template_Placeholder"
python compile_report.py
```
*(Produces updated `main.pdf` in the same directory).*

---

## 6. Guidance for Coding Agents Working on This Repository

1. **Active Codebase Location:** Always write new features, fixes, or extensions inside `saras_swarm_system/`. Treat `projectcode/` as an archived reference.
2. **Contract Preservation:** Any change to drone status, coordinates, or alerts must comply with `swarm_core/telemetry_contract.py`. If modifying models, update both the backend and `dashboard/app.js` to prevent frontend serialization breakage.
3. **Hardware-Software Compatibility:** Ensure any new flight command or telemetry field can be translated to/from standard MAVLink messages (e.g., `GLOBAL_POSITION_INT`, `SYS_STATUS`, `HEARTBEAT`).
4. **Zero-Crash Requirement:** The simulation loop in `backend/main.py` runs inside an asynchronous background task. Ensure all exceptions are cleanly caught and logged without killing the FastAPI server.
5. **No Heavy Weight Dependencies for RAG:** The RAG assistant in `triage_rag.py` is intentionally designed with pure Python + scikit-learn/math to run instantly on lightweight edge hardware (Raspberry Pi) and local workstations without requiring external vector databases or OpenAI API keys. Maintain this lightweight portability.
