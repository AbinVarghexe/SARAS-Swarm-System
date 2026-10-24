from __future__ import annotations

from math import hypot
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .models import Drone, Sector


class SectorAllocator:
    """Auction-style assignment strategy for sectors."""

    def __init__(self, sectors: Iterable[Sector], drones: Sequence[Drone]):
        self.sectors = list(sectors)
        self.drones = list(drones)

    def assign(self) -> Dict[str, str]:
        assignments: Dict[str, str] = {}
        available_sectors = [s for s in self.sectors if not s.covered and s.status != "locked"]

        for drone in sorted(self.drones, key=lambda d: (d.battery, d.drone_id), reverse=True):
            if drone.health != "active":
                continue
            if not available_sectors:
                break
            best_sector = self._select_best_sector(drone, available_sectors)
            if best_sector is None:
                continue
            assignments[drone.drone_id] = best_sector.sector_id
            best_sector.assigned_to = drone.drone_id
            best_sector.status = "assigned"
            drone.sector_id = best_sector.sector_id
            drone.last_known_sector = best_sector.sector_id
            available_sectors.remove(best_sector)

        return assignments

    def _select_best_sector(self, drone: Drone, sectors: List[Sector]) -> Optional[Sector]:
        candidates: List[Tuple[float, Sector]] = []
        for sector in sectors:
            distance = self._distance_to_sector_center(drone, sector)
            battery_penalty = (100 - drone.battery) * 0.04
            cost = distance + battery_penalty
            candidates.append((cost, sector))
        if not candidates:
            return None
        return min(candidates, key=lambda item: item[0])[1]

    @staticmethod
    def _distance_to_sector_center(drone: Drone, sector: Sector) -> float:
        return hypot(drone.x - sector.x, drone.y - sector.y)
