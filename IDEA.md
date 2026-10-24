# IDEA.md

# Project Name

SARAS

**Search And Rescue Autonomous Swarm**

---

# Vision

SARAS is an AI-powered autonomous drone **swarm** platform designed for disaster response.

The goal is to reduce the time required to locate victims after disasters such as:

- Landslides
- Floods
- Building Collapse
- Earthquakes
- Forest Search Operations

The platform should autonomously explore affected areas using **coordinated multi-drone swarm behavior**, detect victims, map the disaster zone, and assist rescue operators using AI.

Rather than a single drone executing a fixed mission, SARAS is built around a **swarm intelligence layer** that allows any number of drones to self-organize, divide the search area, adapt to failures, and converge on victims faster than a single unit could.

Machine learning is not confined to one layer of the system — it is applied **both onboard the drone (edge inference)** and **at the swarm/decision layer (coordination + agentic reasoning)**. This dual-ML design is what gives the two-member team two genuinely distinct, publishable research contributions from a single shared platform.

The system should be designed as a modular platform so that future mission profiles can be added without redesigning the drone or the swarm logic.

Examples:

- Search & Rescue
- Infrastructure Inspection
- Flood Assessment
- Forest Fire Monitoring
- Missing Person Search

The drone hardware and swarm coordination layer remain the same.

Only the mission profile changes.

---

# Project Constraints

This project is a B.Tech Final Year Project.

Timeline:

2 Months

Team:

2 Members

- **Member 1 — Hardware Lead**: drone build, flight controller setup (Pixhawk/PX4), frame/motors/ESC/GPS/camera integration, companion computer (Raspberry Pi) setup, telemetry, physical test flights, **onboard/edge ML deployment**
- **Member 2 — Software Lead**: ROS2, simulation (Gazebo, multi-vehicle SITL), computer vision pipeline, swarm coordination layer, backend (FastAPI), dashboard (Next.js), **swarm-level ML / RL**, agentic AI, RAG

Physical Hardware:

ONE drone only.

The swarm — multiple drones operating in coordination — exists in simulation.

The software and swarm architecture must be written so that the same code base scales from 1 physical drone to N simulated drones without modification.

The interface between the two members' work is the **drone-to-backend telemetry/command contract** (MAVSDK/MAVLink + a defined message schema) — this should be agreed on early so hardware and software integration doesn't become a late-stage bottleneck.

Each member's ML component is independently evaluable and independently publishable — this is required so both members can produce separate research papers from one shared system.

---

# Core Objective

Build a complete autonomous rescue **swarm** system instead of only building a drone — with machine learning applied at two distinct layers:

1. **Edge ML (Hardware side)** — real-time perception running onboard the drone itself
2. **Swarm ML (Software side)** — learned/adaptive coordination and decision-making across the swarm

The project consists of

- Drone
- Edge ML (onboard inference)
- Swarm Coordination Layer
- Swarm ML / Agentic AI
- Mapping
- Dashboard
- RAG
- Simulation

---

# Deliverables

The final demonstration should include

✓ One autonomous physical drone

✓ Drone built from scratch

✓ Onboard edge ML inference running on the companion computer

✓ Multi-drone swarm simulation (3–5+ simulated drones)

✓ Simulation environment

✓ Human Detection

✓ GPS Mapping

✓ Learned/decentralized sector allocation across the swarm

✓ Swarm fault-tolerance (drone dropout / reassignment)

✓ Dashboard with live swarm view

✓ Agentic AI

✓ RAG

✓ Rescue Recommendation

✓ Two independent research papers (IEEE format) — Edge ML and Swarm ML

✓ Two-part presentation with a shared system demo

---

# What NOT To Build

Do NOT build

- Flight Controller Firmware
- Custom PID Controller
- A detection model architecture from scratch (fine-tune/optimize an existing one — YOLO)
- Drone Operating System
- A custom swarm communication protocol from scratch (use existing MAVLink/ROS2 multi-vehicle tooling)
- A custom RL algorithm from scratch (use established multi-agent RL / auction-learning approaches and adapt them)

Use existing open-source solutions. The research contribution is in **application, optimization, and evaluation**, not reinventing base algorithms.

---

# Hardware

Flight Controller

Pixhawk

Companion Computer

Raspberry Pi

Frame

450mm

Motors

Brushless Motors

ESC

30A ESC

GPS

GPS + Compass

Battery

LiPo

Camera

Raspberry Pi Camera

Telemetry

WiFi

*(The swarm's other members are PX4 SITL instances in simulation — no additional physical hardware required.)*

---

# Software Stack

Robot Middleware

ROS2 (multi-robot / namespaced nodes per drone)

Simulation

Gazebo Harmonic (multi-vehicle simulation)

Flight Stack

PX4 (SITL, multi-instance for swarm simulation)

Swarm Communication

MAVSDK / MAVLink (multi-vehicle)

ROS2 DDS for inter-agent messaging

Mission Planning

QGroundControl (swarm-aware, multi-vehicle view)

Computer Vision

OpenCV

Ultralytics YOLO

Edge ML Runtime

TensorRT / ONNX Runtime / TFLite (quantized inference on Raspberry Pi)

Swarm ML

Multi-agent RL framework (e.g., PettingZoo / RLlib) or auction-based learning for task allocation

Backend

FastAPI

Frontend

Next.js

Tailwind

Leaflet

Database

PostgreSQL

or SQLite

---

# Machine Learning — Two Tracks

## 1. Edge ML (Hardware Lead)

**Research question:** How do you get real-time, reliable human detection running onboard a power- and compute-constrained drone?

- Base model: Ultralytics YOLO (person detection; optional: vehicle, building, debris)
- Optimization for edge deployment: quantization, pruning, and/or knowledge distillation
- Target runtime: ONNX Runtime / TensorRT / TFLite on Raspberry Pi
- Evaluation metrics: mAP vs. baseline, inference latency (ms/frame), power draw, model size, frames-per-second on companion computer
- Optional extension: ML-based sensor fusion (GPS + IMU) for improved position estimation, or a lightweight ML model for battery/flight-time prediction (feeds into the swarm allocator on the software side)

This is the empirical, systems-oriented ML contribution — accuracy/latency/resource tradeoffs on real embedded hardware.

## 2. Swarm ML / Agentic AI (Software Lead)

**Research question:** How should a decentralized drone swarm learn to allocate search sectors, adapt to failures, and reason about rescue priority — without a single point of failure?

- Sector allocation framed as a multi-agent decision problem: auction-based learning or lightweight multi-agent RL (drones bid on sectors based on distance, battery, and coverage history)
- Reassignment and fault tolerance as a learned/adaptive policy, not fixed heuristics
- Evaluation metrics: time-to-full-coverage, redundant-search rate, recovery time after simulated drone failure, victim-detection latency across N drones
- Agentic AI layer: Rescue Agent (prioritization) and Knowledge Agent (RAG) evaluated on decision quality and retrieval relevance respectively

This is the coordination/decision-making ML contribution — swarm-level intelligence and adaptive agentic reasoning.

**Why the split works:** Edge ML's output (detections + drone status) is a direct input to Swarm ML's system (which consumes it for coordination and rescue decisions). The two papers cite each other and describe one working system from two different, independently defensible angles.

---

# Simulation

Everything should first work inside simulation, including the full swarm and both ML layers.

Simulation should contain

- Terrain
- Trees
- Roads
- Buildings
- Victims
- Multiple simulated drones (swarm)

The physical drone should only be used after simulation succeeds — it acts as one live node within the same swarm architecture used in simulation, running the actual edge ML model.

---

# Drone Software

Each drone (physical or simulated) must support

Takeoff

Waypoint Navigation

Autonomous Flight

Landing

Camera Streaming

GPS Streaming

Telemetry

Onboard inference (physical drone) / simulated inference (SITL drones)

Swarm heartbeat / status broadcast (position, battery, current sector, health)

---

# Detection Pipeline

Camera

↓

Edge ML (YOLO, optimized runtime)

↓

Person Detection

↓

GPS Position

↓

Backend

↓

Swarm Coordination Layer (Swarm ML)

↓

Dashboard

---

# Dashboard

Dashboard must contain

Live Map

All Drone Positions (swarm view)

Victim Position

Live Camera (per selected drone)

Mission Status (per-drone and swarm-wide)

Victim List

Search Progress

Battery (per drone)

Coverage Map

Swarm Health (active / lost / reassigned drones)

Edge inference stats (latency/FPS on the physical drone) — useful for the hardware paper's live results

---

# Rescue Recommendation

When victims are detected

System should generate

Priority List

Estimated Distance

Nearest Rescue Point

Suggested Rescue Order

Which drone made the detection

Use simple heuristics if necessary, or the learned prioritization policy from the Swarm ML track.

---

# Swarm Coordination Layer

This is the core intelligence differentiating SARAS from a single-drone search tool.

### Area Coverage

The disaster area is divided into sectors.

Example

Sector A

Sector B

Sector C

Sector D

Each drone in the swarm is assigned one sector at a time.

No overlapping search between active drones.

The dashboard displays, per sector:

Covered

Searching

Remaining

### Task Allocation Strategy

- **Market-based / auction allocation** (baseline): each drone "bids" on unclaimed sectors based on distance and battery, lowest-cost bid wins the sector
- **Learned allocation** (research extension): multi-agent RL policy trained in simulation to improve on the auction baseline — this is the core evaluated contribution of the Swarm ML paper
- Fallback: a lightweight centralized coordinator service (FastAPI) with graceful degradation if the coordinator link drops

### Dynamic Sector Reassignment

If a drone finishes its sector

↓

It requests/claims a new unclaimed sector

If a drone fails or drops connection

↓

Its last-known incomplete sector is flagged

↓

The nearest healthy drone is reassigned to continue it

### Victim Locking

Once a victim is detected

↓

A rescue zone is created and broadcast to the swarm

↓

Other drones treat that zone as covered and do not re-search it

↓

Swarm continues covering remaining sectors

### Fault Tolerance

The swarm must tolerate:

- A single drone losing connectivity (its sector is reassigned)
- A single drone running low on battery (it returns to base; sector reassigned)
- Coordinator downtime (drones fall back to last-assigned sector until reconnected)

---

# Agentic AI

The system should include multiple AI agents.

Mission Agent

Controls individual drone missions.

Vision Agent

Validates detections from the Edge ML pipeline.

Mapping Agent

Maintains search coverage across the swarm.

**Swarm Coordination Agent**

Owns sector allocation, reassignment, and fault handling logic across all drones (implements the Swarm ML policy).

Rescue Agent

Prioritizes victims across all swarm detections.

Knowledge Agent

Uses RAG to answer rescue questions.

---

# RAG

The system should include a Retrieval-Augmented Generation pipeline.

Knowledge Base

- Disaster SOPs
- First Aid Manuals
- Drone Manuals
- Landslide Guidelines
- Rescue Protocols
- Emergency Procedures
- Swarm Operating Procedures (mission handoff, failure response)

The AI should answer questions only using retrieved knowledge.

Example

"What is the safest rescue procedure for a buried victim?"

The answer should be generated from retrieved documents.

---

# Research & Publication Plan

Two independent, IEEE-format research papers from one shared system — one per member.

## Paper 1 — Hardware Lead: Edge ML

**Working title:** *Edge-Optimized Real-Time Human Detection for Resource-Constrained Autonomous Search-and-Rescue Drones*

Focus: model optimization (quantization/pruning/distillation) and real-time deployment of YOLO-based human detection on a Raspberry Pi companion computer. Evaluated on accuracy, latency, power, and model size.

## Paper 2 — Software Lead: Swarm ML / Agentic AI

**Working title:** *Decentralized Task Allocation and Agentic Decision Support for Multi-Drone Search-and-Rescue Swarms Using Reinforcement Learning and RAG*

Focus: swarm-level task allocation (auction baseline vs. learned multi-agent RL policy), fault-tolerant reassignment, and an agentic RAG layer for rescue decision support. Evaluated on coverage efficiency, redundant-search rate, and failure-recovery time.

## Shared Paper Structure (IEEE Conference Format)

1. Abstract (150–250 words)
2. Keywords (5–6, IEEE-style)
3. Introduction — problem, motivation, contribution statement
4. Related Work — literature review, gap identification
5. System Architecture / Methodology
6. Implementation
7. Results & Evaluation
8. Conclusion & Future Work
9. References (IEEE numbered citation style)

Format: two-column IEEE conference layout, Times New Roman 10pt body text.

Each paper references the other where the systems connect (Edge ML's detection output feeding Swarm ML's coordination layer), establishing that both are part of one integrated platform.

## Presentation Plan

- Each member presents their own paper independently (10–12 slides: problem → method → results → contribution)
- A shared final section covers overall system architecture and a live/simulated demo, presented jointly

---

# Future Vision

The software architecture must support

- Larger drone swarms (10+)
- Thermal Cameras
- LiDAR
- Mesh Networking (drone-to-drone, no central coordinator)
- LTE
- Cloud Dashboard
- Cross-swarm collaboration (multiple independent swarms on one disaster zone)

These are future extensions.

Do not implement unless time permits.

---

# Project Architecture

Drone(s)

↓

PX4

↓

ROS2

↓

Edge ML (Vision AI, onboard)

↓

Swarm Coordination Layer (Swarm ML)

↓

Backend

↓

Database

↓

Dashboard

↓

Agentic AI

↓

RAG

↓

Operator

---

# Folder Structure

project/

    drone/

    simulation/

    ros2/

    edge_ml/

    swarm_ml/

    backend/

    dashboard/

    rag/

    agents/

    datasets/

    papers/

        paper_1_edge_ml/

        paper_2_swarm_ml/

    docs/

---

# Coding Standards

Use Python for AI, edge ML, and swarm coordination logic.

Use FastAPI for backend.

Use Next.js for frontend.

Use TypeScript whenever possible.

Follow clean architecture.

Avoid hardcoded values — especially drone count, which must be configurable.

Every module should be independent.

Every drone-facing module must work identically whether it's talking to 1 physical drone or N simulated drones.

Everything should be configurable, including which allocation strategy (auction baseline vs. learned policy) the Swarm Coordination Agent uses — needed to produce the comparison results for Paper 2.

---

# Documentation

Every module should include

Purpose

Inputs

Outputs

Dependencies

API

Configuration

Future Improvements

---

# Priority Order

Hardware and software tracks run in parallel. Software does not wait on hardware — simulation is the primary development environment, and the physical drone is integrated once both tracks are stable.

**Hardware Track (Member 1 — Edge ML)**

1. Drone frame assembly (motors, ESC, GPS, camera, companion computer)
2. Pixhawk + PX4 flight controller setup and tuning
3. Manual test flights (stability, calibration)
4. Autonomous flight test (waypoint navigation via QGroundControl)
5. Baseline YOLO detection running on companion computer (unoptimized)
6. Edge optimization pass (quantization/pruning) + latency/accuracy benchmarking
7. Companion computer ↔ backend telemetry link (MAVSDK/MAVLink)
8. Camera streaming to companion computer
9. Physical drone integration into the swarm system (final phase)
10. Edge ML results write-up (Paper 1)

**Software Track (Member 2 — Swarm ML)**

1. Drone Simulation (Gazebo + PX4 SITL, single vehicle)
2. Human Detection (YOLO on simulated camera feed)
3. GPS Localization / mapping pipeline
4. Multi-Drone Simulation (swarm baseline, PX4 multi-instance)
5. Swarm Coordination Layer — auction-based allocation (baseline)
6. Swarm ML — multi-agent RL policy training and comparison vs. baseline
7. Dashboard (swarm view)
8. Rescue Recommendation + Agentic AI
9. RAG
10. Swarm Fault Tolerance & Stress Testing
11. Swarm ML results write-up (Paper 2)

**Joint / Integration Milestones**

- Agree on the telemetry/command message schema (early, before both tracks build against it)
- Integrate physical drone (with its edge ML model) as one live node in the swarm system
- Full system demo: physical drone + simulated swarm + dashboard + agentic AI + RAG, running together
- Cross-reference both papers so they describe one coherent system

---

# Success Criteria

The project is considered successful if

✓ Drone flies autonomously

✓ Edge ML model runs onboard in real time with measured latency/accuracy tradeoffs

✓ Detects humans

✓ Maps victim location

✓ Displays victims on dashboard

✓ Generates rescue recommendations

✓ Agent answers rescue questions using RAG

✓ Swarm coordinates sector allocation with no overlapping search

✓ Learned allocation policy shows measurable improvement over the auction baseline

✓ Swarm reassigns sectors when a drone fails or finishes early

✓ Swarm locks and avoids re-searching zones with confirmed victims

✓ Multi-drone swarm coordination works in simulation (3–5+ drones)

✓ Single physical drone demonstrates the complete workflow as one live swarm node, running real edge ML

✓ Two IEEE-format research papers completed, each independently defensible, both describing one integrated system

---

# Development Philosophy

Do not reinvent existing robotics, ML, or swarm software.

Reuse mature open-source technologies (PX4 multi-vehicle SITL, MAVSDK, ROS2, YOLO, standard RL frameworks).

Focus on integration, optimization, and evaluation — not low-level algorithm design from scratch.

The research contribution is the intelligent coordination between

- Robotics
- Edge ML
- Swarm Intelligence
- Agentic AI
- Mapping
- RAG
- Rescue Decision Support

The project should resemble an industrial disaster-response swarm platform rather than a simple student drone project — and should produce two rigorous, independently evaluable research contributions from that single platform.

End of IDEA.md
