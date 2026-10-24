from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Any, Dict, Iterable, List, Sequence

from .models import Drone, RescueRecommendation, Victim


@dataclass
class SOPDocument:
    title: str
    content: str
    tags: tuple[str, ...]


class RescueAgent:
    """Ranks detected victims according to severity and rescue path cost."""

    def prioritize(self, victims: Iterable[Victim], drones: Sequence[Drone], rescue_point: tuple[float, float]) -> List[RescueRecommendation]:
        detected = [victim for victim in victims if victim.detected and not victim.rescued]
        recommendations: List[RescueRecommendation] = []
        priority_rank = 1

        for victim in sorted(detected, key=self._priority_key, reverse=True):
            assigned_drone = self._closest_drone(victim, drones)
            if assigned_drone is None:
                continue
            estimated_distance = hypot(victim.x - rescue_point[0], victim.y - rescue_point[1])
            recommendations.append(
                RescueRecommendation(
                    victim_id=victim.victim_id,
                    priority=victim.rescue_priority,
                    estimated_distance=estimated_distance,
                    nearest_rescue_point=rescue_point,
                    suggested_order=priority_rank,
                    drone_id=assigned_drone.drone_id,
                    rationale=f"{victim.severity.title()} victim near {victim.sector_id or 'unknown sector'}",
                )
            )
            priority_rank += 1

        return recommendations

    @staticmethod
    def _priority_key(victim: Victim) -> tuple[int, int]:
        severity_priority = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        return (severity_priority.get(victim.severity.lower(), 0), victim.rescue_priority)

    @staticmethod
    def _closest_drone(victim: Victim, drones: Sequence[Drone]) -> Drone | None:
        active_drones = [drone for drone in drones if drone.health == "active"]
        if not active_drones:
            return None
        return min(active_drones, key=lambda drone: hypot(drone.x - victim.x, drone.y - victim.y))


class KnowledgeAgent:
    """Simple retrieval-based knowledge agent that answers questions using a small SOP base."""

    def __init__(self, documents: Sequence[SOPDocument] | None = None):
        self.documents = list(documents or self._default_documents())

    def answer(self, question: str) -> str:
        retrieval = self.retrieve(question)
        if not retrieval:
            return "No relevant rescue guidance was retrieved from the knowledge base."

        context = "\n".join(f"- {doc.title}: {doc.content}" for doc in retrieval[:2])
        return (
            f"Using the retrieved SOPs: \n{context}\n\nResponse: {retrieval[0].content}"
        )

    def retrieve(self, question: str) -> List[SOPDocument]:
        lowered = question.lower()
        scored: List[tuple[float, SOPDocument]] = []
        for doc in self.documents:
            score = 0.0
            for keyword in lowered.split():
                if keyword in doc.tags or keyword in doc.title.lower() or keyword in doc.content.lower():
                    score += 1.0
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [doc for _, doc in scored[:3]]

    @staticmethod
    def _default_documents() -> List[SOPDocument]:
        return [
            SOPDocument(
                title="Landslide Rescue",
                content="Mark the hazard perimeter, avoid unstable slopes, and prioritize victims with clear signals of life before sending rescue teams to distant debris zones.",
                tags=("landslide", "slope", "rescue", "hazard", "victim"),
            ),
            SOPDocument(
                title="Flood Response",
                content="Ensure the safe rescue route is clear of current risk, use flotation support for survivors, and triage victims by exposure severity and distance to recovery points.",
                tags=("flood", "water", "safe", "route", "survivor"),
            ),
            SOPDocument(
                title="Collapsed Structure Protocol",
                content="Maintain a search perimeter, identify void spaces, and send the nearest available crew to the highest-priority victims while avoiding secondary collapse zones.",
                tags=("collapse", "building", "structure", "search", "victim"),
            ),
            SOPDocument(
                title="Drone Swarm Failure Handling",
                content="When a drone becomes unavailable, its incomplete sector must be reassigned to the nearest healthy drone and the live swarm map should be updated immediately.",
                tags=("swarm", "drone", "failure", "reassignment", "fault", "sector"),
            ),
        ]
