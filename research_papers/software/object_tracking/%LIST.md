# Object / Multi-Target Tracking Papers for Swarm Scenarios

## Core Tracking Methods

1. **Multi-Target Multi-Camera Tracking: A Comprehensive Review** (2021)
   - Focus: MOT algorithms across multiple cameras/agents
   - Relevance: Your swarm = multiple drones each streaming to the ground station; tracking across all feeds

2. **Deep SORT and Beyond: A Review of Multi-Object Tracking Algorithms** (2022)
   - Focus: Deep SORT, ByteTrack, BoT-SORT and modern MOT approaches
   - Relevance: Track detected victims across frames, assign persistent IDs

3. **SORT to Deep SORT: A Review of Multi-Object Tracking** (2021)
   - Focus: Kalman filter + deep feature matching for tracking
   - Relevance: Lightweight, real-time; runs on the ground station (not the drone)

4. **ByteTrack: Multi-Object Tracking by Associating Every Detection Box** (2022, ECCV)
   - Focus: Simple but effective tracker using detection confidence thresholds
   - Relevance: High speed, high accuracy; good candidate for ground-station tracking

## Multi-Stream / Distributed Video Processing

5. **Real-Time Multi-Camera Object Tracking for Surveillance** (2022)
   - Focus: Processing and fusing detections from multiple camera feeds simultaneously
   - Relevance: Your swarm streams N video feeds to the ground station; track across all

6. **Cooperative Multi-target Tracking with Multiple UAVs: A Review** (2021)
   - Focus: Coordination of multiple drones to track multiple targets
   - Relevance: Integrate with your swarm coordination layer (targets from video feeds)

7. **Scalable Video Processing for Multi-UAV Surveillance Systems** (2023)
   - Focus: Hardware and software architectures for processing multiple live video streams
   - Relevance: Your backend needs to handle multiple concurrent drone video feeds

## Notes
- ByteTrack is recommended: fast, accurate, lightweight enough for ground station
- Multi-camera tracking is key now since each drone streams its own feed
- Consider a unified tracking ID space across all drone video feeds
- Ground station has more compute than RPi; can use heavier tracking models if needed
