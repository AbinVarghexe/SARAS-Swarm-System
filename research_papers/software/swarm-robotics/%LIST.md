# Swarm Robotics & Multi-UAV Coordination Papers

## Foundational Works

1. **Swarm Robotics: A Review and Future Directions** (2021, IEEE Access)
   - Focus: Comprehensive survey of swarm robotics principles, algorithms, and applications
   - Relevance: Core theory for your multi-drone coordination backbone

## UAV Swarm Specific

2. **UAV Swarm Coordination: A Review of Algorithms and Applications** (2022)
   - Focus: Classification and comparison of UAV swarm coordination strategies
   - Relevance: Choose the right approach (centralized vs decentralized) for SARAS

3. **Decentralized Control of Multi-UAV Systems: A Survey** (2021)
   - Focus: Decentralized algorithms for UAV formation, flocking, and task execution
   - Relevance: Your system must handle single-drone dropouts gracefully

4. **Software Architectures for Swarm Robotics: A Review** (2023)
   - Focus: Middleware, communication, and coordination architectures for robot swarms
   - Relevance: ROS2-based swarm design decisions

5. **A Review of Multi-UAV Cooperative Mission Planning and Control** (2022)
   - Focus: Integration of mission planning with real-time swarm control
   - Relevance: Connects your sector allocation with lower-level flight control

## Search & Rescue Applications

6. **Multi-UAV Cooperative Search and Rescue: A Review** (2021)
   - Focus: Direct application of UAV swarms to SAR scenarios
   - Relevance: Almost identical to your problem statement

7. **A Swarm Intelligence Approach for Search and Rescue UAVs** (2022)
   - Focus: Particle swarm optimization (PSO) for UAV search patterns
   - Relevance: Can inform your coverage planning approach

## Notes
- Decentralized systems are preferred for fault tolerance (single point of failure argument)
- Your architecture should support both centralized (simulation) and decentralized (real-world) modes
