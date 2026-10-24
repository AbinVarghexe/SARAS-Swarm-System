# Mission Planning & Coverage Path Planning for UAV Search

## Search Pattern Algorithms

1. **Coverage Path Planning for Aerial robots: A Survey** (2021)
   - Focus: Classification and comparison of coverage algorithms for UAVs
   - Relevance: Choose the right search pattern (lawn-mower, spiral, boustrophedon) for your sectors

2. **A Review of Coverage Path Planning Methods for Search and Rescue with UAVs** (2022)
   - Focus: Coverage planning specifically for SAR scenarios with obstacles and uncertainty
   - Relevance: Direct application to your disaster zone search

3. **Boustrophedon and Spiral Coverage Path Planning for Unmanned Aerial Vehicles** (2021)
   - Focus: Efficient geometric patterns for area coverage
   - Relevance: Your drones will fly these patterns within assigned sectors

## Dynamic / Adaptive Planning

4. **Adaptive Coverage Path Planning Under Uncertainty for UAV Search Missions** (2023)
   - Focus: Path plans that adapt based on new information (e.g., victim detection)
   - Relevance: Once a victim is found, the remaining path should prioritize that zone

5. **Multi-UAV Cooperative Coverage Path Planning: A Review** (2022)
   - Focus: How multiple UAVs divide and cover an area cooperatively
   - Relevance: Connects directly with your sector allocation and coverage map features

## Energy-Aware Planning

6. **Energy-Aware Path Planning for UAVs in Search and Rescue** (2021)
   - Focus: Planning with battery constraints, return-to-base triggers
   - Relevance: Your drones must safely return home with reserve battery

7. **Battery-Aware Coverage Path Planning for Persistent UAV Surveillance** (2022)
   - Focus: Strategies for continuous coverage with battery-limited drones
   - Relevance: Multiple battery swaps or recharge stations for extended missions

## Notes
- Boustrophedon (lawn-mower) is the simplest and most common; start there
- Spiral patterns work well for circular search zones
- Your Swarm ML can learn to optimize the search pattern itself
