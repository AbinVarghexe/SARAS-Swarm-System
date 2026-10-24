# SARAS Research Paper Collection

This directory contains curated research paper lists organized by software and hardware tracks for the SARAS (Search And Rescue Autonomous Swarm) Final Year Project.

**Updated: 2026-07-03** — Architecture changed from onboard edge ML to live video streaming + backend processing.

---

## Quick Stats
- **Software Tracks**: 9 categories
- **Hardware Tracks**: 7 categories
- **Total Papers Curated**: 85+
- **Preferred Publication Years**: 2020-2024
- **Preferred Venues**: IEEE, ICRA, IROS, NeurIPS, ICML, arXiv

---

## Architecture Update (IMPORTANT)

In the updated SARAS architecture, **all video processing happens on the ground/backend system**, not on the drone.

### New Data Flow
```
Drone (RPi Camera) 
  -> Hardware Encode (H.264/H.265) on RPi
  -> Live Video Stream (RTSP/WebRTC/UDP) over WiFi
  -> Backend/Ground Station
  -> Decode + Object Detection (YOLO on GPU/CPU)
  -> Tracking + Coordination + Dashboard
```

### What Changed
- ✋ Old: Onboard YOLO inference on Raspberry Pi (TensorRT / ONNX / TFLite)
- ✅ New: RPi streams raw video; all ML runs on the backend/ground station
- ✋ Old: "Edge ML" hardware track focused on model optimization for RPi
- ✅ New: Companion computer is a "smart video encoder + telemetry relay"
- ✋ Old: Focus on inference speed (FPS) on embedded hardware
- ✅ New: Focus on **streaming latency** (camera → backend) and **end-to-end system latency**

---

## How to Download Papers

Each `%LIST.md` file contains paper titles, focus, and relevance notes. To download:

1. **Google Scholar**: Search for the paper title directly
2. **arXiv**: Many ML/robotics preprints are available here
3. **IEEE Xplore**: Institutional access required for many robotics papers
4. **Unpaywall Browser Plugin**: Automatically finds free PDFs

### Recommended Process
1. Read the `%LIST.md` for a category
2. Identify the most relevant papers (marked with higher relevance)
3. Search Google Scholar for each title
4. Download PDFs to the respective folder
5. Rename PDFs as `Author-Year-ShortTitle.pdf` for easy reference

---

## Software Tracks Summary

| Track | Focus | Key Papers |
|-------|-------|-----------|
| CV | Aerial image understanding | 6 papers (2021-2023) |
| Object Detection | YOLO variants, aerial person detection — now runs on backend | 9 papers (2021-2024) |
| Object Tracking | MOT, multi-drone tracking — now streams from all drones to central tracker | 7 papers (2021-2023) |
| Swarm Robotics | Multi-UAV coordination, formation | 7 papers (2021-2023) |
| Cooperative Perception | Shared maps, distributed SLAM | 6 papers (2021-2023) |
| Multi-Agent RL | QMIX, MAPPO, MADDPG for task allocation | 8 papers (2017-2022) |
| Task Allocation | Auctions, optimization, Hungarian | 8 papers (2020-2023) |
| Mission Planning | Coverage planning, search patterns | 7 papers (2021-2023) |
| Real-time AI Systems | **Video stream processing, streaming latency, pipeline architecture** | 11 papers (2021-2023) |

---

## Hardware Tracks Summary

| Track | Focus | Key Papers |
|-------|-------|-----------|
| Autonomous UAVs | Complete SAR UAV platforms | 6 papers (2021-2023) |
| Flight Control | PX4, Pixhawk, MAVLink | 7 papers (2020-2022) |
| Companion Computers | **Raspberry Pi as streaming-only video encoder + telemetry relay** | 8 papers (2022-2023) |
| Embedded AI | Model compression, distillation — **de-emphasized now** | 7 papers (2021-2023) |
| Edge Inference | TensorRT, ONNX, TFLite — **de-emphasized now** | 8 papers (2021-2023) |
| Communication | **MAVLink + Video Streaming Protocols (RTSP/WebRTC/UDP)** | 10 papers (2021-2023) |
| Simulation-Hardware Integration | SITL, HITL, Gazebo | 10 papers (2021-2023) |

---

## Research Paper Priorities (Updated for Streaming Architecture)

### Must-Read (Start Here)
These papers cover the core of your updated system:

1. **Real-Time Video Streaming from UAVs: Protocols and Performance Analysis** (Communication)
2. **YOLOv8 / Aerial Person Detection** (Object Detection) — runs on backend now
3. **ByteTrack / Multi-Camera MOT** (Object Tracking) — centralized on backend
4. **MAPPO / QMix** (Multi-Agent RL) — Swarm coordination
5. **Auction-Based Task Allocation** — your assignment baseline
6. **Real-Time Video Stream Processing** (Real-time AI Systems) — NEW PRIORITY
7. **Bandwidth and Power Optimization for UAV Video Streaming** (Companion Computers)

### Medium Priority
- Multi-Target Multi-Camera Tracking (centralized tracking across all swarm feeds)
- Coverage Path Planning (search patterns)
- ROS2 DDS Performance (communication backbone)
- Latency Analysis in ROS2 (understand end-to-end delays)

### Background Knowledge
- Vision Transformers for Aerial Images
- Cooperative SLAM (map sharing across drones)
- 5G for UAV Communications
- Model Compression (only if you decide to add SOME onboard intelligence later)

---

## Connecting Papers to Your New Deliverables

| Deliverable | Relevant Paper Categories | Key Papers |
|------------|--------------------------|-----------|
| Physical drone build | Flight Control, Autonomous UAVs | PX4 SITL, Pixhawk architecture |
| **Live video stream to backend** | **Communication + Companion Computers** | **RTSP/WebRTC, streaming benchmarks** |
| **Person detection from live feed** | **Object Detection + Real-time AI** | **YOLOv8, stream processing** |
| **Multi-drone tracking** | **Object Tracking + Real-time AI** | **Multi-camera MOT, ByteTrack** |
| Swarm simulation | Swarm Robotics, Simulation-Hardware | Gazebo multi-vehicle, ROS2 |
| Sector allocation | Multi-Agent RL, Task Allocation | MAPPO, auction algorithms |
| Dashboard live view | Cooperative Perception, Communication | Shared maps, DDS |
| Fault tolerance | Swarm Robotics, Task Allocation | Decentralized control, online allocation |
| Rescue prioritization | Multi-Agent RL, Real-time AI | RODE, agent role learning |

---

## Tips for Efficient Paper Reading

1. **Start with surveys**: They give you the landscape quickly
2. **Read abstracts first**: Spend 5 minutes on each abstract; flag for deep read
3. **Focus on Related Work & Experimental Setup**: Skip methodology deep-dives if not immediately relevant
4. **Extract key numbers**: FPS, streaming latency (ms), bandwidth (Mbps), mAP — for your evaluation
5. **One-page summary per paper**: After reading, write a single-page summary in the folder

---

_Last updated: 2026-07-03_
_Architecture update: Drone now streams live video; all processing on backend_
_Generated for SARAS Final Year Project_
