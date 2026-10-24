# SARAS Research Paper Library

This folder contains curated research papers and references for the SARAS (Search And Rescue Autonomous Swarm) Final Year Project, organized into software and hardware sections.

---

## Structure

```
research_papers/
├── README.md
├── software/
│   ├── CV/                          # Computer Vision (Image Processing, Feature Extraction)
│   ├── object_detection/            # Person/Vehicle/Debris Detection (YOLO variants, etc.)
│   ├── object_tracking/             # Multi-Target / Multi-Drone Tracking
│   ├── swarm-robotics/              # Multi-Robot / Drone Swarm Coordination
│   ├── cooperative-perception/      # Shared Perception & Information Fusion in Swarms
│   ├── multi-agent-rl/              # Multi-Agent Reinforcement Learning for Task Allocation
│   ├── task-allocation-optimization/ # Auction, Market-based, Optimization approaches
│   ├── mission-planning/            # Path Planning, Waypoint Generation, Search Strategies
│   └── realtime-ai-systems/         # Real-time System Design, Edge-Swarm Interface
└── hardware/
    ├── autonomous-uavs/             # UAV Autonomy, Platform Design
    ├── flight-control/              # PX4/Pixhawk, Autopilot Systems
    ├── companion-computers/         # Raspberry Pi, Jetson, etc.
    ├── embedded-ai/                 # Edge ML Deployment, Model Optimization
    ├── edge-inference/              # TensorRT, ONNX, TFLite, Quantization
    ├── communication-and-telemetry/ # MAVLink, WiFi, Network Protocols
    └── simulation-hardware-integration/ # SITL/HITL, Gazebo, Virtual-to-Real Transfer
```

## How to Use

Each subfolder contains two things:
1. A `%LIST.md` listing all papers in that category (sorted, with links, years, and relevance notes)
2. Individual paper files (PDF, or markdown summaries if PDF is unavailable)

- Focus on **IEEE format**, **recent works (2020+ preferred)**
- Prioritize **open-access** papers or those available through institutional access
- Flag **foundational/seminal works** for must-read before implementation

---

## Categories Summary

### Software Tracks
| Category | Focus Area |
|----------|-----------|
| CV | Image preprocessing, feature extraction, visual understanding |
| object_detection | YOLO, SSD, DETR for person/vehicle/debris on aerial/drone imagery |
| object_tracking | SOT / MOT for continuous victim tracking across frames / drones |
| swarm-robotics | Decentralized coordination, consensus, formation control for drone swarms |
| cooperative-perception | Shared maps, sensor fusion, distributed SLAM in multi-agent systems |
| multi-agent-rl | MARL algorithms (QMIX, MAPPO, MADDPG) applied to task allocation |
| task-allocation-optimization | Auction-based, Hungarian, consensus-based allocation strategies |
| mission-planning | Coverage planning, search patterns, path optimization |
| realtime-ai-systems | Pipeline design, system latency, real-time guarantees |

### Hardware Tracks
| Category | Focus Area |
|----------|-----------|
| autonomous-uavs | Drone autonomy stack, complete UAV platforms for SAR |
| flight-control | PX4 autopilot, flight modes, control architecture |
| companion-computers | Raspberry Pi, Jetson Nano/Orin as companion computers |
| embedded-ai | Model conversion, deployment pipelines for embedded devices |
| edge-inference | Quantization, pruning, TensorRT/TFLite/ONNX optimization |
| communication-and-telemetry | MAVLink, DDS, telemetry protocols for real-time data |
| simulation-hardware-integration | SITL, simulation-to-reality transfer, VTOL/Swarm SITL |

---

_Last updated: 2026-07-03_
