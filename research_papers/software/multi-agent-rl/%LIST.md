# Multi-Agent Reinforcement Learning for Swarm Task Allocation

## Foundational MARL

1. **Multi-Agent Reinforcement Learning: A Comprehensive Survey** (2021)
   - Focus: Classification of MARL algorithms, challenges, and applications
   - Relevance: Core theory for your learned sector allocation approach

2. **The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games** (2022)
   - Focus: Why simple PPO-based methods beat complex MARL in practice
   - Relevance: Start simple before trying advanced MARL algorithms

## Key Algorithms for Task Allocation

3. **QMIX: Monotonic Value Function Factorisation for Deep Multi-Agent Reinforcement Learning** (2018, ICML)
   - Focus: Decentralized value function factorization for cooperative agents
   - Relevance: One of the most cited MARL algorithms for cooperative settings

4. **MAPPO: Revisiting Simple Baselines for Cooperative Multi-Agent Reinforcement Learning** (2021)
   - Focus: Multi-agent variant of PPO, surprisingly competitive
   - Relevance: Easy to implement, works well in practice for your auction/reassignment problem

5. **Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments** (MADDPG) (2017, NeurIPS)
   - Focus: Centralized training with decentralized execution (CTDE)
   - Relevance: CTDE is the standard paradigm for your swarm learning

6. **RODE: Learning Roles to Decode with Multi-Agent Communication** (2021)
   - Focus: Role-based division of labor in multi-agent systems
   - Relevance: Drones can learn roles (searcher, tracker, rescuer) for your mission profiles

## Auction / Market-Based Learning

7. **Auction-Based Multi-Robot Task Allocation: A Survey** (2021)
   - Focus: Combinatorial and sequential auctions for task assignment in multi-robot systems
   - Relevance: Your baseline allocator; can be enhanced with learned bid functions

8. **Reinforcement Learning for Combinatorial Auctions: A Survey** (2022)
   - Focus: How RL agents learn to bid in auctions for task allocation
   - Relevance: Hybrid approach — your Swarm ML paper's core contribution

## Notes
- PettingZoo / RLlib are recommended libraries for MARL implementation
- Start with MAPPO (simpler, robust) before adopting QMIX or RODE
