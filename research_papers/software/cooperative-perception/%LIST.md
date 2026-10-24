# Cooperative Perception & Information Fusion in Swarms

## Core Papers

1. **Cooperative Perception for Autonomous Driving and Robotics: A Survey** (2023)
   - Focus: Information sharing and fusion among multiple agents for perception
   - Relevance: Parallels to your swarm's shared victim detection and mapping

2. **Distributed Multi-UAV Cooperative Perception for Search and Rescue** (2022)
   - Focus: How multiple UAVs share and fuse sensor data for improved scene understanding
   - Relevance: Direct application to your swarm's shared camera/GPS data

3. **Multi-Agent Perception: A Survey and a Potential Application for Autonomous Vehicles** (2021)
   - Focus: Communication-aware perception in multi-agent systems
   - Relevance: Bandwidth constraints when sharing camera data among drones

4. **Cooperative Aerial-Ground Robotic System for Search and Rescue: A Review** (2022)
   - Focus: Perception pipeline combining aerial and ground robots
   - Relevance: Expands to other SARAS mission profiles beyond aerial

## Map Sharing / Distributed SLAM

5. **Visual SLAM for UAVs: A Review** (2021)
   - Focus: Simultaneous Localization and Mapping from aerial camera feeds
   - Relevance: Your GPS + camera can generate an occupancy/coverage map

6. **Cooperative SLAM for Multiple UAVs: A Review** (2023)
   - Focus: How multiple drones build and share a single consistent map
   - Relevance: Each drone contributes to a shared disaster zone map

## Notes
- Consider a shared occupancy grid / heatmap that all drones update
- This connects to your Dashboard's Coverage Map feature
