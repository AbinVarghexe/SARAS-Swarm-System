from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class SimulationConfig:
    """Configuration options for the SARAS swarm simulation."""

    arena_width: float = 1000.0
    arena_height: float = 1000.0
    drone_count: int = 4
    sector_rows: int = 3
    sector_cols: int = 3
    victim_count: int = 8
    max_steps: int = 30
    drone_speed: float = 28.0
    failure_probability: float = 0.05
    battery_drain_per_step: float = 1.2
    search_rate: float = 0.16
    coverage_threshold: float = 0.85
    search_radius: float = 75.0
    risk_buffer: float = 20.0
    rescue_point: tuple[float, float] = (50.0, 50.0)

    # Operating mode: "pure_sim" (100% virtual swarm in hazardous environment)
    # or "hybrid_real" (1 physical drone with real video + N virtual companions)
    mode: str = "pure_sim"

    # Geographical Anchor: Wayanad Chooralmala Landslide Disaster Zone, Kerala
    base_lat: float = 11.5360
    base_lon: float = 76.1390
    base_alt: float = 850.0

