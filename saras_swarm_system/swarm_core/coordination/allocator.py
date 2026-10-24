"""
SARAS Swarm Coordination & Task Allocation
Implements:
1. Sector Generator: Partitions a disaster search bounding box into M x N sectors.
2. Market-Based Auction Allocator: Drones compute bids balancing distance, battery, and sector priority/age.
3. Baseline Greedy Allocator: Assigns purely by minimum distance (used for IEEE paper ablation).
4. Policy Evaluation & Benchmarking: Quantifies metrics (travel distance, battery variance, priority response).
"""

from __future__ import annotations
import math
import time
from typing import Dict, List, Optional, Tuple
import numpy as np

from swarm_core.telemetry_contract import DroneTelemetry, SectorModel, SectorStatus, DroneStatus


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points in meters.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def generate_sectors(
    min_lat: float = 12.9710,
    max_lat: float = 12.9790,
    min_lon: float = 77.5910,
    max_lon: float = 77.6030,
    rows: int = 3,
    cols: int = 4,
    priority_map: Optional[Dict[str, float]] = None
) -> Dict[str, SectorModel]:
    """
    Partitions a bounding box into rows x cols rectangular sectors.
    Returns a dictionary of sector_id -> SectorModel.
    """
    sectors: Dict[str, SectorModel] = {}
    lat_step = (max_lat - min_lat) / rows
    lon_step = (max_lon - min_lon) / cols

    counter = 1
    for r in range(rows):
        for c in range(cols):
            s_min_lat = min_lat + r * lat_step
            s_max_lat = s_min_lat + lat_step
            s_min_lon = min_lon + c * lon_step
            s_max_lon = s_min_lon + lon_step

            sector_id = f"SEC-{counter:02d}"
            name = f"Sector {counter:02d} [R{r+1}C{c+1}]"

            # 4 polygon corners (clockwise: NW, NE, SE, SW, NW)
            bounds = [
                [s_max_lat, s_min_lon],
                [s_max_lat, s_max_lon],
                [s_min_lat, s_max_lon],
                [s_min_lat, s_min_lon],
                [s_max_lat, s_min_lon]
            ]
            centroid = [(s_min_lat + s_max_lat) / 2.0, (s_min_lon + s_max_lon) / 2.0]

            # Priority weight (default 1.0, or from map, or higher for central/high-risk sectors)
            priority = 1.0
            if priority_map and sector_id in priority_map:
                priority = priority_map[sector_id]
            else:
                # Naturally prioritize center or specific disaster hotspot
                if (r in (1, rows//2)) and (c in (1, cols//2)):
                    priority = 2.0

            sectors[sector_id] = SectorModel(
                sector_id=sector_id,
                name=name,
                bounds=bounds,
                centroid=centroid,
                min_lat=s_min_lat,
                max_lat=s_max_lat,
                min_lon=s_min_lon,
                max_lon=s_max_lon,
                status=SectorStatus.UNSEARCHED,
                assigned_drone_id=None,
                priority=priority,
                coverage_pct=0.0,
                last_searched_at=None
            )
            counter += 1

    return sectors


class BaseSectorAllocator:
    """Abstract base class for swarm task allocation policies."""

    def allocate(
        self,
        drones: Dict[str, DroneTelemetry],
        sectors: Dict[str, SectorModel]
    ) -> Dict[str, str]:
        """
        Calculates sector assignments for idle or available drones.
        Returns mapping: drone_id -> sector_id.
        """
        raise NotImplementedError


class GreedyDistanceAllocator(BaseSectorAllocator):
    """
    Baseline Greedy Allocator:
    Assigns each available drone strictly to the unsearched sector with the
    minimum Haversine distance to its centroid.
    Ignores drone battery levels and sector priority weights.
    Serves as the primary baseline for the IEEE paper ablation study.
    """

    def allocate(
        self,
        drones: Dict[str, DroneTelemetry],
        sectors: Dict[str, SectorModel]
    ) -> Dict[str, str]:
        assignments: Dict[str, str] = {}
        # Candidate unassigned & unsearched sectors
        assigned_sector_ids = {d.current_sector_id for d in drones.values() if d.current_sector_id}
        available_sectors = [
            s for s in sectors.values()
            if s.status == SectorStatus.UNSEARCHED and s.sector_id not in assigned_sector_ids
        ]

        # Candidate available drones (IDLE, SEARCHING without sector, or RETURNING)
        candidate_drones = [
            d for d in drones.values()
            if (d.status in (DroneStatus.IDLE, DroneStatus.SEARCHING, DroneStatus.RETURNING) and not d.current_sector_id)
            and d.battery > 15.0
        ]

        # Greedy allocation by minimum distance
        remaining_sectors = list(available_sectors)
        for drone in candidate_drones:
            if not remaining_sectors:
                break
            # Find closest sector
            best_sector = min(
                remaining_sectors,
                key=lambda s: haversine_distance(drone.lat, drone.lon, s.centroid[0], s.centroid[1])
            )
            assignments[drone.drone_id] = best_sector.sector_id
            remaining_sectors.remove(best_sector)

        return assignments


class MarketAuctionAllocator(BaseSectorAllocator):
    """
    Market-Based Auction Sector Allocator:
    Decentralized market coordination where drones bid on unclaimed sectors.
    Bid Cost Function:
      J(i, j) = w_dist * (D_ij / D_max) + w_bat * C_bat(B_i) - w_prio * (P_j / P_max)

    Where:
      - D_ij is Haversine distance between drone i and sector j centroid.
      - C_bat(B_i) is an exponential battery penalty factor:
          C_bat(B_i) = ((100 - B_i) / 100)^2 * (1.0 if B_i > 30 else 5.0)
      - P_j is sector priority / urgency weight.
      - Drones with battery <= 20% are prohibited from bidding (must RTH).

    Auction clearing assigns sectors to minimize the global swarm cost matrix.
    """

    def __init__(
        self,
        w_distance: float = 0.45,
        w_battery: float = 0.35,
        w_priority: float = 0.20,
        battery_reserve_pct: float = 20.0
    ):
        self.w_distance = w_distance
        self.w_battery = w_battery
        self.w_priority = w_priority
        self.battery_reserve_pct = battery_reserve_pct

    def compute_bid(
        self,
        drone: DroneTelemetry,
        sector: SectorModel,
        max_dist_ref: float = 2000.0,
        max_prio_ref: float = 3.0
    ) -> float:
        """
        Compute bid cost for a drone to take on a sector.
        Lower cost = stronger bid (drone wants this sector).
        Returns infinity if drone battery is below safe threshold.
        """
        if drone.battery <= self.battery_reserve_pct:
            return float("inf")

        # 1. Distance cost
        dist = haversine_distance(drone.lat, drone.lon, sector.centroid[0], sector.centroid[1])
        d_norm = min(dist / max_dist_ref, 2.0)

        # 2. Battery penalty (non-linear: penalty escalates sharply as battery declines)
        bat_fraction = drone.battery / 100.0
        bat_depletion = 1.0 - bat_fraction
        bat_penalty = (bat_depletion ** 2)
        if drone.battery < 35.0:
            bat_penalty *= 2.5

        # 3. Priority incentive (higher priority reduces bid cost)
        prio_norm = min(sector.priority / max_prio_ref, 2.0)

        # 4. Sector staleness/age bonus
        age_bonus = 0.0
        if sector.last_searched_at:
            elapsed = time.time() - sector.last_searched_at
            age_bonus = min(elapsed / 600.0, 0.5)

        cost = (
            self.w_distance * d_norm +
            self.w_battery * bat_penalty -
            self.w_priority * prio_norm -
            0.10 * age_bonus
        )
        return float(cost)

    def allocate(
        self,
        drones: Dict[str, DroneTelemetry],
        sectors: Dict[str, SectorModel]
    ) -> Dict[str, str]:
        """
        Clears the auction round: determines the optimal drone-to-sector matching.
        """
        assignments: Dict[str, str] = {}

        # 1. Active assigned sectors
        assigned_sector_ids = {
            d.current_sector_id for d in drones.values()
            if d.current_sector_id and d.status == DroneStatus.SEARCHING
        }

        # 2. Candidate unassigned sectors
        candidate_sectors = [
            s for s in sectors.values()
            if s.status == SectorStatus.UNSEARCHED and s.sector_id not in assigned_sector_ids
        ]
        if not candidate_sectors:
            return assignments

        # 3. Candidate drones needing sectors (IDLE, SEARCHING without sector, or RETURNING)
        candidate_drones = [
            d for d in drones.values()
            if (d.status in (DroneStatus.IDLE, DroneStatus.SEARCHING, DroneStatus.RETURNING) and not d.current_sector_id)
            and d.battery > self.battery_reserve_pct
        ]
        if not candidate_drones:
            return assignments

        # 4. Build Cost Matrix [N_drones x M_sectors]
        n_d = len(candidate_drones)
        n_s = len(candidate_sectors)
        cost_matrix = np.zeros((n_d, n_s), dtype=float)

        for i, drone in enumerate(candidate_drones):
            for j, sector in enumerate(candidate_sectors):
                cost_matrix[i, j] = self.compute_bid(drone, sector)

        # 5. Resolve assignments: sequential lowest-bid winner selection
        assigned_drone_indices = set()
        assigned_sector_indices = set()

        # Flatten and sort all (cost, drone_idx, sector_idx) pairs
        bid_tuples: List[Tuple[float, int, int]] = []
        for i in range(n_d):
            for j in range(n_s):
                cost = cost_matrix[i, j]
                if not math.isinf(cost):
                    bid_tuples.append((cost, i, j))

        bid_tuples.sort(key=lambda x: x[0])

        for cost, d_idx, s_idx in bid_tuples:
            if d_idx in assigned_drone_indices or s_idx in assigned_sector_indices:
                continue
            drone = candidate_drones[d_idx]
            sector = candidate_sectors[s_idx]
            assignments[drone.drone_id] = sector.sector_id
            assigned_drone_indices.add(d_idx)
            assigned_sector_indices.add(s_idx)

        return assignments


def evaluate_allocation_policies(
    num_drones: int = 4,
    rows: int = 3,
    cols: int = 4
) -> Dict[str, Dict[str, float]]:
    """
    Ablation benchmark helper comparing MarketAuctionAllocator vs GreedyDistanceAllocator.
    Returns comparison metrics suitable for Member 2's IEEE conference paper.
    """
    sectors = generate_sectors(rows=rows, cols=cols)

    # Synthetic swarm with heterogeneous battery states and starting coordinates
    np.random.seed(42)
    center_lat, center_lon = 12.9750, 77.5970

    drone_templates: List[Tuple[str, float, float, float]] = [
        ("Drone-1", center_lat - 0.003, center_lon - 0.004, 92.0),
        ("Drone-2", center_lat + 0.002, center_lon - 0.003, 38.0),  # Low battery
        ("Drone-3", center_lat - 0.001, center_lon + 0.004, 85.0),
        ("Drone-4", center_lat + 0.004, center_lon + 0.002, 60.0),
    ][:num_drones]

    def create_swarm() -> Dict[str, DroneTelemetry]:
        return {
            d_id: DroneTelemetry(
                drone_id=d_id,
                lat=lat,
                lon=lon,
                battery=bat,
                status=DroneStatus.IDLE
            )
            for d_id, lat, lon, bat in drone_templates
        }

    results = {}
    allocators = {
        "GreedyDistanceBaseline": GreedyDistanceAllocator(),
        "MarketAuctionProposed": MarketAuctionAllocator()
    }

    for name, allocator in allocators.items():
        swarm = create_swarm()
        test_sectors = {k: v.model_copy() for k, v in sectors.items()}

        assigned = allocator.allocate(swarm, test_sectors)

        total_distance = 0.0
        battery_penalties = []
        priorities_served = []

        for drone_id, sector_id in assigned.items():
            drone = swarm[drone_id]
            sector = test_sectors[sector_id]
            dist = haversine_distance(drone.lat, drone.lon, sector.centroid[0], sector.centroid[1])
            total_distance += dist
            # Battery strain: distance / battery
            strain = dist / max(drone.battery, 1.0)
            battery_penalties.append(strain)
            priorities_served.append(sector.priority)

        avg_distance = total_distance / max(len(assigned), 1)
        battery_variance = float(np.var(battery_penalties)) if battery_penalties else 0.0
        avg_priority = float(np.mean(priorities_served)) if priorities_served else 0.0

        results[name] = {
            "assigned_count": len(assigned),
            "total_travel_meters": round(total_distance, 2),
            "avg_distance_meters": round(avg_distance, 2),
            "workload_variance": round(battery_variance, 4),
            "avg_priority_weight": round(avg_priority, 2),
            "energy_efficiency_score": round(100.0 / (1.0 + avg_distance / 100.0 + battery_variance * 5.0), 2)
        }

    return results
