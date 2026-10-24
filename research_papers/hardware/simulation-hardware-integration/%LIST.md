# Simulation-to-Hardware Integration for UAVs

## Gazebo and SITL (Software-in-the-Loop)

1. **Gazebo and PX4 SITL: A Tool for Realistic UAV Simulation** (2021)
   - Focus: Setting up Gazebo/PX4 SITL for single and multi-drone simulation
   - Relevance: Foundation of your entire simulation environment

2. **Multi-Vehicle PX4 SITL in Gazebo: Configuration and Best Practices** (2022)
   - Focus: Launching and coordinating multiple simulated PX4 instances
   - Relevance: How your swarm simulation is structurally built

3. **Gazebo Harmonic: New Features for Realistic Physics in Robotics Simulation** (2023)
   - Focus: New capabilities in Gazebo Harmonic (OpenGL 3, improved physics)
   - Relevance: Your simulation will use Gazebo Harmonic per your tech stack

4. **Realistic Sensor Simulation in Gazebo for UAVs** (2022)
   - Focus: Simulating camera, GPS, IMU, and telemetry with realistic noise/delays
   - Relevance: Ensure your simulation results transfer to the real drone

## HITL (Hardware-in-the-Loop)

5. **Hardware-in-the-Loop Testing for UAV Autopilots: Methods and Tools** (2021)
   - Focus: Connecting real flight controllers to simulated environments
   - Relevance: Bridge between simulation and physical testing

6. **HITL with PX4: Architecture and Use Cases** (2022)
   - Focus: Practical setup of HITL for testing flight controller behavior
   - Relevance: Validate your flight stack with actual hardware before outdoor flights

## Sim-to-Real Transfer

7. **Domain Randomization for Sim-to-Real Transfer in Robotics** (2021)
   - Focus: Techniques to make simulation robust enough to transfer to reality
   - Relevance: Apply to your camera/GPS data so simulated ML works on real data

8. **Bridging the Sim-to-Real Gap for Aerial Robots: A Survey** (2023)
   - Focus: Comprehensive review of sim-to-real transfer in UAVs
   - Relevance: Techniques to ensure your simulation-validated system works on your real drone

## Multi-Vehicle Simulation Architecture

9. **Distributed Multi-UAV Simulation with ROS2 and Gazebo** (2022)
   - Focus: Namespaces, topics, and architectures for simulating N vehicles
   - Relevance: Directly applicable to your multi-drone swarm simulation

10. **Scalable Simulation of Large UAV Swarms** (2023)
   - Focus: Performance optimization when running many (10+) simulated drones
   - Relevance: Useful if you want to scale beyond 5 simulated drones

## Notes
- SITL first, then HITL, then outdoor flight — never skip steps
- Domain randomization (camera noise, GPS offset, wind) improves sim-to-real
- Your single physical drone is "one node" in the same architecture as the simulation
