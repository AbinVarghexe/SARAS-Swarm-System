# Real-Time AI Systems & Video Processing Pipelines

## Real-Time System Design

1. **Real-Time Object Detection for Embedded Systems: A Survey** (2022)
   - Focus: Latency optimization techniques for real-time inference on embedded hardware
   - Relevance: Now applies to your **ground station** receiving live video, not the drone

2. **Design Principles for Real-Time Multi-Agent Systems** (2021)
   - Focus: Software architecture for real-time multi-agent coordination
   - Relevance: Ensure your swarm coordination doesn't create latency bottlenecks

3. **Latency Analysis in ROS2 Real-Time Applications** (2023)
   - Focus: Measurement and optimization of latency in ROS2-based robotic systems
   - Relevance: ROS2 is your backbone; understand its real-time behavior

## Live Video Stream Processing (NEW PRIORITY)

4. **Real-Time Video Analytics at the Edge: A Survey** (2022)
   - Focus: Processing live video streams for detection, tracking, and analysis
   - Relevance: Core to your new architecture - video in, detections out

5. **Video Stream Processing for Surveillance: Architecture and Algorithms** (2023)
   - Focus: Pipeline design for continuous video streams with detection and tracking
   - Relevance: Your backend processes N live video feeds from the swarm

6. **Low-Latency Video Streaming for Remote Drone Operations** (2022)
   - Focus: Technical approaches to minimize delay in drone-to-ground video transmission
   - Relevance: Every millisecond of video latency delays your rescue response

7. **Stream Processing Frameworks for Real-Time Video Analytics: A Comparative Study** (2023)
   - Focus: Apache Kafka, Redis Streams, custom pipelines for video processing
   - Relevance: Choose the right backend architecture for your video pipeline

## Pipeline Architecture

8. **End-to-End Perception and Planning Pipelines for Autonomous Vehicles** (2022)
   - Focus: Integration of perception, decision-making, and control in one pipeline
   - Relevance: Mirror this for your Camera -> Stream -> Backend -> Detection -> Coordination -> Control

9. **Cloud-Edge Collaborative Video Analytics: A Survey** (2023)
   - Focus: Splitting video processing between capture and cloud/backend
   - Relevance: Your drone is pure capture; all processing happens at the "cloud" (backend)

## System Integration

10. **A Modular Architecture for UAV-based Search and Rescue Systems** (2021)
    - Focus: Demonstrates modular design allowing hardware and software components to be independently replaced
    - Relevance: Supports your modular platform; drone can be swapped without changing backend processing

11. **Real-Time UAV Swarm for Disaster Response: System Design and Challenges** (2022)
    - Focus: End-to-end system that combines real-time perception, communication, and coordination
    - Relevance: Validates your architecture from drone video stream to dashboard

## Notes
- Real-time now means: camera -> stream -> backend -> detect -> dashboard in < 1 second
- Profile your pipeline at each stage: capture latency, network latency, decode latency, inference latency
- Your drone is now a "dumb" video sensor; all intelligence is in the backend
- Use hardware encoding (H.264/H.265) on the drone to reduce bandwidth
