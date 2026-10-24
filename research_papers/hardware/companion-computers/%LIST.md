# Companion Computers — Raspberry Pi / Streaming-Only Setup

## Raspberry Pi as Drone Companion Computer

1. **Raspberry Pi in UAV Applications: A Comprehensive Survey** (2022)
   - Focus: Use of RPi as companion computer for sensing, streaming, and telemetry
   - Relevance: Your RPi now runs camera + streaming (not ML inference)

2. **Real-Time Video Streaming from Raspberry Pi on UAVs: Methods and Benchmarks** (2023)
   - Focus: Comparison of RTSP, WebRTC, and custom UDP streaming from RPi
   - Relevance: Core to your new architecture - optimized live video feed streaming

3. **Bandwidth and Power Optimization for UAV Video Streaming** (2022)
   - Focus: Techniques to reduce bandwidth and power for continuous video transmission
   - Relevance: Critical for battery-limited drones streaming continuously

## Camera + Streaming Configuration

4. **Raspberry Pi Camera Module: Performance and Configuration Guide** (2023)
   - Focus: Best practices for configuring the RPi camera for aerial applications
   - Relevance: Your camera is now the primary sensor; optimize its setup

5. **H.264/H.265 Hardware Encoding on Raspberry Pi: A Benchmark** (2022)
   - Focus: Hardware-accelerated encoding performance on RPi 4/5
   - Relevance: Hardware encoding reduces CPU load and improves streaming efficiency

## NVIDIA Jetson (Alternative — if you want SOME onboard processing)

6. **NVIDIA Jetson Platform for Edge AI: A Review** (2022)
   - Focus: Jetson Nano / NX / Orin for robotics and video processing
   - Relevance: Only if you later want SOME preprocessing (e.g., motion detection) before streaming

## System Integration — Streaming-First Architecture

7. **Integrating Companion Computers with PX4: A Guide** (2021)
   - Focus: Hardware connections, serial/UART setup, Linux-MAVLink bridge
   - Relevance: Your RPi still handles telemetry alongside video streaming

8. **A Streaming-First Architecture for UAV Companion Computers** (2023)
   - Focus: Design principles for companion computers that stream rather than process
   - Relevance: Exactly your new architecture - maximize stream quality, minimize onboard compute

## Notes
- Raspberry Pi 4b (8GB) or 5 + RPi Camera Module v3 is sufficient (no AI workload)
- Use --codec h264_v4l2m2m for hardware encoding (very low CPU usage)
- Lower CPU usage = longer flight time, lower heat, more reliable
- Consider WebRTC for lower latency than RTSP (though more complex to set up)
- Companion computer is now a "smart camera" that streams video + sends telemetry to backend
- All intelligence (YOLO, tracking, coordination) runs on the ground station
