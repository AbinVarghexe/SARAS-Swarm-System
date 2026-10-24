# Communication & Telemetry for UAV Swarms — With Live Video

## MAVLink / MAVSDK

1. **MAVLink Protocol: Design, Evolution, and Use in UAV Swarms** (2021)
   - Focus: Message types, rate control, and scalability of MAVLink for multi-drone communication
   - Relevance: Core to your drone-to-backend telemetry link

2. **MAVSDK: A Modern SDK for MAVLink-Based Drone Communication** (2022)
   - Focus: High-level API for controlling PX4 drones from backend
   - Relevance: Your backend sends commands; MAVSDK abstracts MAVLink complexity

## Video Streaming Protocols (NEW ADDITION)

3. **Video Streaming Protocols for UAV Applications: A Comparative Survey** (2023)
   - Focus: RTSP, RTP, WebRTC, SRT, and custom protocols for drone video streaming
   - Relevance: Choose the best video streaming protocol for your system

4. **RTSP vs WebRTC for Drone Surveillance: Latency and Quality Analysis** (2022)
   - Focus: Head-to-head comparison of the two most common streaming protocols
   - Relevance: RTSP is simpler; WebRTC has lower latency; choose based on your needs

5. **Adaptive Bitrate Streaming for UAVs in Bandwidth-Constrained Environments** (2023)
   - Focus: Dynamic adjustment of video quality based on network conditions
   - Relevance: Maintain stable video feed even with variable WiFi signal

6. **Low-Latency Video Transmission Over WiFi for UAVs** (2022)
   - Focus: Methods to achieve sub-100ms latency in video streaming
   - Relevance: The faster the video reaches the backend, the faster detections happen

## DDS and ROS2 Communication

7. **ROS2 DDS Communication for Multi-UAV Systems: A Performance Analysis** (2022)
   - Focus: Latency, bandwidth, and reliability of DDS for multi-robot systems
   - Relevance: ROS2 DDS is your inter-agent (simulation to backend) communication

8. **Fast DDS vs Cyclone DDS: A Comparative Study for Robotics** (2023)
   - Focus: Comparison of the two main DDS implementations in ROS2
   - Relevance: Choose the best DDS implementation for your swarm

## Network Architecture

9. **A Dual-Channel Communication Architecture for UAV Swarms** (2023)
   - Focus: Separating telemetry/control and video data into distinct channels
   - Relevance: Your system uses one channel for MAVLink and another for video

10. **Network Topology and Bandwidth Requirements for Multi-UAV Real-Time Video Streaming** (2022)
    - Focus: Calculating and managing bandwidth for N concurrent video feeds
    - Relevance: Ensure your network can handle multiple drone video streams simultaneously

## Notes
- Separate your control and video traffic into different network channels if possible
- For simulation, DDS handles telemetry; add a video stream publisher (simulated camera -> ROS topic -> backend)
- For physical drone, use WiFi for both MAVLink and video (different ports/IPs)
- Consider MPEG-TS over UDP for very low-latency streaming
- Always have a fallback: if video drops, MAVLink continues so the drone remains controllable
