# Task Allocation & Optimization in Multi-UAV Systems

## Auction-Based Approaches

1. **A Market-Based Approach for Multi-Robot Task Allocation with Time Constraints** (2021)
   - Focus: Auction algorithms with temporal constraints for dynamic environments
   - Relevance: Your sector assignment has time-to-completion as a factor

2. **Combinatorial Auctions for Multi-Robot Coordination: A Review** (2022)
   - Focus: Theoretical and practical aspects of combinatorial auctions in robotics
   - Relevance: When sectors have dependencies or bundling makes sense

3. **Distributed Auction Algorithms for Multi-Agent Task Allocation** (2021)
   - Focus: Fully distributed (no central auctioneer) task allocation
   - Relevance: Your swarms fallback mode when coordinator is down

## Optimization Approaches

4. **Multi-UAV Task Allocation: A Review of Optimization Approaches** (2022)
   - Focus: Genetic algorithms, ant colony, particle swarm optimization for task allocation
   - Relevance: Alternatives to auction for comparison in your Swarm ML paper

5. **Mixed-Integer Linear Programming for Multi-UAV Mission Planning** (2021)
   - Focus: MILP formulation of task allocation with constraints (battery, distance, no-fly zones)
   - Relevance: Baseline optimal allocation for small swarms; compare against learned policies

6. **Hungarian Algorithm and Its Variants for Multi-Robot Assignment** (2020)
   - Focus: Optimal assignment problem solvers
   - Relevance: Simple, fast allocation baseline when sector-drone counts are small

## Dynamic / Online Allocation

7. **Online Task Allocation for UAV Swarms with Changing Environments** (2023)
   - Focus: Allocation policies that adapt to dynamic conditions (new victims, drone failures)
   - Relevance: Your fault-tolerance requirement demands online reassignment

8. **A Biologically-Inspired Task Allocation Framework for UAV Swarms** (2022)
   - Focus: Ant-inspired (pheromone-based) decentralized allocation
   - Relevance: Nature-inspired alternative to auction/optimization approaches

## Notes
- Auction-based is your primary baseline (mentioned in IDEA.md)
- MILP / Hungarian provides an "optimal" comparison point for small N
- Learned allocation (MAPPO/RL) should outperform both after training
