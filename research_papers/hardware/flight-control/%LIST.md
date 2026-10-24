# Flight Control Systems — PX4 / Pixhawk / Autopilots

## PX4 Flight Stack

1. **PX4 Flight Stack: Architecture, Capabilities, and Recent Advances** (2021)
   - Focus: Overview of PX4 autopilot architecture and development
   - Relevance: Your drone uses PX4; understand its internals and interfaces

2. **PX4 SITL: Simulation in the Loop for Multi-Vehicle Scenarios** (2022)
   - Focus: Multi-instance PX4 SITL for building and testing multi-drone swarms in simulation
   - Relevance: Core to your swarm simulation before physical flight

3. **MAVLink and MAVSDK for UAV Communication: A Review** (2021)
   - Focus: Protocol design, message types, and SDK capabilities
   - Relevance: Your drone-to-backend telemetry/command interface

## Pixhawk Hardware

4. **Pixhawk 4: Hardware Architecture and Performance** (2020)
   - Focus: Technical specifications and capabilities of Pixhawk 4 autopilot
   - Relevance: Understand the capabilities of your flight controller

5. **A Comparison of Open-Source Autopilots for UAV Applications** (2022)
   - Focus: Comparison of PX4, Ardupilot, Betaflight for different use cases
   - Relevance: Validate your choice of PX4 for SARAS

## Autonomous Flight Modes

6. **Autonomous Mission Modes in PX4: Offboard and Auto** (2021)
   - Focus: How to use PX4's offboard control for custom autonomous behavior
   - Relevance: Your swarm coordination will send offboard commands via MAVSDK

7. **Waypoint Navigation and Path Following in PX4** (2022)
   - Focus: Implementation and tuning of waypoint-based autonomous flight
   - Relevance: Your drones will execute waypoint lists for search sectors

## Notes
- PX4 user and developer guides (online) are essential references alongside these papers
- Understand the "offboard" mode thoroughly — it's how your software commands the drone
