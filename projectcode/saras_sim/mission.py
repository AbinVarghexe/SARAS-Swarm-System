from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class DisasterMission:
    """Defines the search-and-rescue mission layout for the swarm."""

    arena_width: float = 1000.0
    arena_height: float = 1000.0
    sector_rows: int = 2
    sector_cols: int = 2
    victim_count: int = 8
    rescue_point: tuple[float, float] = (50.0, 50.0)
    obstacles: List[tuple[float, float, float, float]] = field(default_factory=list)

    @property
    def sector_count(self) -> int:
        return self.sector_rows * self.sector_cols

    def build_sector_centers(self) -> List[tuple[float, float]]:
        centers: List[tuple[float, float]] = []
        gw = self.arena_width / self.sector_cols
        gh = self.arena_height / self.sector_rows
        for row in range(self.sector_rows):
            for col in range(self.sector_cols):
                centers.append(((col + 0.5) * gw, (row + 0.5) * gh))
        return centers

    def add_obstacle(self, x: float, y: float, width: float, height: float) -> None:
        self.obstacles.append((x, y, width, height))
