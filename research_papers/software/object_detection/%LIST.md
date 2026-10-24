# Object Detection Papers for Aerial/Drone Person Detection

## Core - YOLO & Aerial Detection

1. **YOLOv5, YOLOv8 and YOLOv10: A Comprehensive Review** (2024)
   - Focus: Evolution of YOLO for object detection; performance benchmarking
   - Relevance: Choose version for ground-station deployment (recommend YOLOv8)

2. **Real-time Object Detection Using Deep Learning on Aerial Images** (2021, IEEE)
   - Focus: CNN-based detection from UAV-mounted cameras
   - Relevance: Establishes baselines for aerial person detection

3. **Small Object Detection in Aerial Images Using Improved YOLOv8** (2023)
   - Focus: Modifications to YOLOv8 for small objects (people) in aerial images
   - Relevance: People appear small from drone altitude - directly applicable

4. **YOLO-UAV: An Object Detection Network Applicable to Unmanned Aerial Vehicles Scenes** (2023)
   - Focus: YOLO variant optimized specifically for UAV-captured imagery
   - Relevance: Tailored architecture for your exact camera viewpoint

5. **Aerial Person Detection Using Deep Learning: A Comprehensive Review** (2022)
   - Focus: Survey of all deep learning approaches for detecting people from drones
   - Relevance: Choose the best-performing method for your ML track

## Live Video Streaming & Processing Architecture

6. **Real-Time Video Streaming from UAVs: Protocols and Performance Analysis** (2022)
   - Focus: RTSP, RTP, UDP streaming protocols for live drone video feeds
   - Relevance: Your camera streams live to the backend; this covers the transport mechanism

7. **Latency-Aware Video Transmission in UAV-Based Surveillance Systems** (2023)
   - Focus: Minimizing end-to-end latency from UAV camera to ground station display
   - Relevance: Critical for real-time victim detection from live feed

8. **Real-Time Object Detection on Live Video Streams: A Survey** (2022)
   - Focus: Processing continuous video feeds (not per-frame) for detection pipelines
   - Relevance: Your backend receives live video; this covers the processing side

9. **Edge-to-Cloud Video Streaming for Drone Surveillance** (2023)
   - Focus: Bandwidth-efficient streaming with selective processing (ROI-based)
   - Relevance: Optimize video bandwidth from drone to backend for real-time detection

## Notes
- Download the arXiv versions for open access
- Focus on YOLOv8 / YOLOv10 for your implementation
- Compare mAP vs inference speed (FPS) tradeoffs on your ground station (not RPi)
- Priority now is on the **video streaming pipeline** (camera -> network -> backend -> detection -> dashboard)
