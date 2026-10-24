"""
SARAS Agentic AI & RAG Triage Engine
1. Rescue Triage Agent: Prioritizes detected victims by urgency score (injuries, thermal signatures,
   environmental hazards like flood/fire, and detection age).
2. RAG Knowledge Agent: Vector-less keyword/TF-IDF emergency SOP retriever answering operator
   queries based on disaster rescue guidelines.
"""

from __future__ import annotations
import math
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from swarm_core.telemetry_contract import (
    DetectionEvent,
    DetectionStatus,
    RescueRecommendation,
    TriageCategory,
)

# Disaster Search & Rescue Standard Operating Procedures (SOP) Knowledge Base
DISASTER_SOPS = [
    {
        "sop_id": "SOP-101",
        "title": "Swiftwater & Flood Victim Extraction",
        "category": "Flood & Water Rescue",
        "keywords": ["flood", "swiftwater", "water", "hypothermia", "submerged", "boat", "drowning", "current"],
        "content": (
            "1. Scene Assessment: Assess water velocity, debris flow, and upstream hazards before water entry. "
            "Never tie a rescuer to a rigid anchor in moving water.\n"
            "2. Victim Extraction: If victim is stranded in fast current or hypothermic (<35°C), deploy tethered rescue boat "
            "or aerial hoist immediately. Prioritize victims with fading grip or low freeboard.\n"
            "3. Hypothermia Treatment: Insulate victim from cold wind/water immediately. Remove wet clothing, wrap in vapor barrier "
            "and active heating blanket. Do not allow rapid aggressive rewarming or walking to prevent cardiac arrhythmias."
        ),
        "tactical_action": "Deploy inflatable motorized rescue craft or aerial extraction harness. Prepare hypothermia warming kit."
    },
    {
        "sop_id": "SOP-102",
        "title": "Landslide & Mudflow Pinned Survivor Extraction",
        "category": "Landslide & Mudflow",
        "keywords": ["landslide", "mudflow", "pinned", "debris", "boulder", "crush", "entrapment", "slope"],
        "content": (
            "1. Secondary Slide Watch: Establish an upstream lookout with visual safety horns before deploying ground crews to slide toe.\n"
            "2. Pinned Limb & Crush Protocol: If a limb has been compressed for >15 minutes under debris/boulders, administer IV hydration "
            "and sodium bicarbonate PRIOR to extrication to prevent acute renal failure and reperfusion cardiac arrest.\n"
            "3. Shoring: Stabilize unstable boulders using pneumatic lifting bags and timber cribbing. Avoid heavy excavators directly above victims."
        ),
        "tactical_action": "Post geological spotter on high ground. Dispatch heavy USAR extrication team with pneumatic airbags and IV fluids."
    },
    {
        "sop_id": "SOP-103",
        "title": "Structural Collapse & USAR Void Space Search",
        "category": "Earthquake & Collapse",
        "keywords": ["collapse", "building", "rubble", "void", "fire", "smoke", "structural", "unresponsive"],
        "content": (
            "1. Void Identification: Lean-to and pancake collapses offer primary survivable void spaces. Search voids using acoustic listening "
            "and thermal cameras.\n"
            "2. Proximity Hazards: When fire or smoke is within 30m of trapped victims, establish dual fog-stream water curtains immediately "
            "to suppress thermal radiation and displace toxic CO/HCN gas.\n"
            "3. Extraction: Triage unconscious victims as Red (Immediate). Administer high-flow oxygen upon reaching the patient."
        ),
        "tactical_action": "Establish fire barrier hose line. Route confined-space USAR extraction unit with air monitoring."
    },
    {
        "sop_id": "SOP-104",
        "title": "Drone Swarm Lost-Link & Battery Failsafe SOP",
        "category": "Swarm Operations",
        "keywords": ["battery", "failsafe", "dropout", "lost", "heartbeat", "rth", "sector", "reassignment"],
        "content": (
            "1. Heartbeat Timeout: If a swarm UAV ceases telemetry broadcasts for >5.0 seconds, the central coordinator flags the drone as LOST "
            "and immediately unassigns its search sector.\n"
            "2. Dynamic Reassignment: The unfinished sector is dynamically reassigned to the nearest active UAV possessing >25% battery.\n"
            "3. Low Battery Threshold: When a drone reaches 20% SoC, it triggers autonomous Return-to-Home (RTH). No manual pilot override "
            "is permitted below 15% battery."
        ),
        "tactical_action": "Verify sector handoff to nearest active UAV; track lost drone GPS last known fix; ready reserve battery swap."
    },
    {
        "sop_id": "SOP-105",
        "title": "START Field Triage & Urgency Classification",
        "category": "Medical Triage",
        "keywords": ["triage", "start", "critical", "urgent", "stable", "priority", "respiration", "perfusion"],
        "content": (
            "1. START Protocol Steps: Assess Ambulatory status -> Respiration (>30/min indicates Critical) -> Perfusion (cap refill >2s) -> Mental Status.\n"
            "2. Triage Categories:\n"
            "   - RED (Critical): Life-threatening compromised airway, severe hemorrhage, hypothermia (<34°C), or environmental fire threat.\n"
            "   - YELLOW (Urgent): Serious injuries, fractures, entrapment with stable vitals, evacuation within 1-2 hours.\n"
            "   - GREEN (Stable): Walking wounded, minor contusions, able to shelter in place under observation."
        ),
        "tactical_action": "Tag victim in mission control; alert trauma receiving facility; dispatch prioritized evacuation transport."
    },
    {
        "sop_id": "SOP-106",
        "title": "Roof & Isolated High-Ground Evacuation",
        "category": "Flood & Storm",
        "keywords": ["roof", "isolated", "stranded", "family", "surrounded", "aerial", "helicopter"],
        "content": (
            "1. Aerial Delivery: For victims stranded on rooftops or isolated dry ground with rising waters, drop emergency survival packs "
            "(potable water, VHF radio, life vests, thermal foils) via drone drop mechanism.\n"
            "2. Hoist Operations: Direct helicopter rescue basket to roof apex. Ensure all aerial drones maintain 500ft horizontal separation "
            "from manned aviation operations.\n"
            "3. Priority: If floodwaters are still rising, prioritize single-story structures before multi-story reinforced roofs."
        ),
        "tactical_action": "Deploy drone payload drop with VHF radio and flotation vests; schedule high-clearance rescue vehicle or boat."
    }
]


class RescueTriageAgent:
    """
    Intelligent rescue triage engine.
    Computes fine-grained urgency scores based on vital/thermal signatures,
    environmental hazards (fire, flood, crush), and detection staleness.
    Assigns START triage classes and prescribes actionable rescue directives.
    """

    def triage_detection(
        self,
        detection: DetectionEvent,
        now: Optional[float] = None
    ) -> RescueRecommendation:
        current_time = now or time.time()
        score = 40.0  # Baseline score

        reasons = []

        # 1. Thermal signature evaluation
        if detection.thermal_signature is not None:
            temp = detection.thermal_signature
            if temp < 35.0:
                # Severe hypothermia
                score += 28.0
                reasons.append(f"Severe hypothermia risk (body temp {temp:.1f}°C)")
            elif temp > 38.5:
                # Heat stroke / severe hyperthermia
                score += 22.0
                reasons.append(f"Hyperthermia / smoke exposure (temp {temp:.1f}°C)")
            else:
                score += 5.0

        # 2. Environmental context tags
        tags = set(detection.environment_tags or [])
        if "fire_proximity" in tags or "fire" in tags:
            score += 30.0
            reasons.append("Immediate fire hazard (<30m)")
        if "swiftwater" in tags or "flood" in tags:
            score += 22.0
            reasons.append("Fast-moving flood current")
        if "unresponsive" in tags:
            score += 25.0
            reasons.append("Subject appears non-responsive")
        if "pinned" in tags or "debris" in tags:
            score += 15.0
            reasons.append("Entrapment under debris / crush injury risk")
        if "roof_stranded" in tags or "isolated" in tags:
            score += 10.0
            reasons.append("Stranded on elevated structure")

        # 3. Detection confidence scaling
        if detection.confidence < 0.85:
            score *= 0.9  # slight dampening if confidence is lower

        # 4. Age penalty (escalates as minutes pass unassisted)
        elapsed_min = max(0.0, (current_time - detection.timestamp) / 60.0)
        age_bonus = min(elapsed_min * 2.0, 15.0)
        score += age_bonus
        if age_bonus > 4.0:
            reasons.append(f"Unassisted for {elapsed_min:.1f} mins")

        # Clamp score to 0-100
        urgency_score = min(100.0, max(10.0, score))

        # Determine Category & Recommended Action
        sop_refs = []
        if urgency_score >= 75.0:
            category = TriageCategory.CRITICAL
            if "flood" in tags or "swiftwater" in tags:
                action = "IMMEDIATE EXTRACTION: Dispatch Swiftwater Rescue Boat & aerial hoist. Deploy hypothermia warming kit."
                assigned_asset = "Swiftwater-Rescue-Boat-1"
                sop_refs = ["SOP-101", "SOP-105"]
            elif "fire_proximity" in tags or "unresponsive" in tags:
                action = "IMMEDIATE EVACUATION: Deploy fire barrier fog curtain and rapid air-evacuation hoist."
                assigned_asset = "Air-Medevac-Alpha"
                sop_refs = ["SOP-103", "SOP-105"]
            else:
                action = "IMMEDIATE CRITICAL RESPONSE: Dispatch tactical extrication unit with advanced life support."
                assigned_asset = "Tactical-Rescue-Team-1"
                sop_refs = ["SOP-102", "SOP-105"]
        elif urgency_score >= 45.0:
            category = TriageCategory.URGENT
            if "pinned" in tags or "landslide" in tags:
                action = "URGENT EXTINCTION: Deploy USAR team with hydraulic spreaders, shoring cribbing, and crush IV kit."
                assigned_asset = "USAR-Heavy-Rescue-2"
                sop_refs = ["SOP-102", "SOP-105"]
            elif "roof_stranded" in tags:
                action = "AERIAL DROP & FLOOD EVAC: Drop emergency flotation vests + VHF radio; dispatch shallow-draft skiff."
                assigned_asset = "Flood-Evac-Skiff-3"
                sop_refs = ["SOP-106"]
            else:
                action = "URGENT AMBULANCE: Ground paramedic evacuation within 60 minutes."
                assigned_asset = "Ground-Ambulance-4"
                sop_refs = ["SOP-105"]
        else:
            category = TriageCategory.STABLE
            action = "MONITOR & SHELTER: Drone to loiter or mark coordinates. Ground team dispatched for ambulatory escort."
            assigned_asset = "Ground-Patrol-Bravo"
            sop_refs = ["SOP-105"]

        notes = "; ".join(reasons) if reasons else "Standard detection without severe acute complications."

        return RescueRecommendation(
            rec_id=f"REC-{str(uuid.uuid4())[:6].upper()}",
            victim_id=detection.detection_id,
            urgency_score=round(urgency_score, 1),
            triage_category=category,
            recommended_action=action,
            assigned_asset=assigned_asset,
            sop_references=sop_refs,
            notes=notes,
            timestamp=current_time
        )


class RAGKnowledgeAgent:
    """
    Retrieval-Augmented Generation (RAG) agent for Emergency Response SOPs.
    Implements a fast, vector-less TF-IDF retrieval system over disaster rescue protocols.
    """

    def __init__(self, corpus: Optional[List[Dict]] = None):
        self.corpus = corpus or DISASTER_SOPS
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        """Simple, robust regex tokenizer with lowercasing."""
        clean = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
        tokens = [t for t in clean.split() if len(t) > 2]
        # Remove ultra-common stop words
        stopwords = {"the", "and", "for", "with", "that", "this", "from", "are", "was", "will"}
        return [t for t in tokens if t not in stopwords]

    def _build_index(self) -> None:
        """Builds term frequency and inverse document frequency structures."""
        self.doc_tokens: List[List[str]] = []
        self.df: Dict[str, int] = {}
        self.num_docs = len(self.corpus)

        for doc in self.corpus:
            combined_text = f"{doc['title']} {doc['category']} {' '.join(doc.get('keywords', []))} {doc['content']} {doc.get('tactical_action', '')}"
            tokens = self._tokenize(combined_text)
            self.doc_tokens.append(tokens)

            # Document frequency
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.df[t] = self.df.get(t, 0) + 1

        # Calculate IDF: log((N + 1) / (DF + 1)) + 1
        self.idf: Dict[str, float] = {}
        for token, df_count in self.df.items():
            self.idf[token] = math.log((self.num_docs + 1.0) / (df_count + 1.0)) + 1.0

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top-k relevant SOP documents using TF-IDF cosine similarity.
        """
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        # Query vector
        q_tf: Dict[str, int] = {}
        for t in q_tokens:
            q_tf[t] = q_tf.get(t, 0) + 1

        q_vec: Dict[str, float] = {}
        q_norm_sq = 0.0
        for t, count in q_tf.items():
            idf_val = self.idf.get(t, 1.0)
            weight = count * idf_val
            q_vec[t] = weight
            q_norm_sq += weight ** 2
        q_norm = math.sqrt(q_norm_sq) if q_norm_sq > 0 else 1.0

        scores: List[Tuple[float, int]] = []

        # Score documents
        for idx, tokens in enumerate(self.doc_tokens):
            if not tokens:
                continue
            doc_tf: Dict[str, int] = {}
            for t in tokens:
                doc_tf[t] = doc_tf.get(t, 0) + 1

            dot_product = 0.0
            doc_norm_sq = 0.0
            for t, count in doc_tf.items():
                idf_val = self.idf.get(t, 1.0)
                weight = count * idf_val
                doc_norm_sq += weight ** 2
                if t in q_vec:
                    dot_product += q_vec[t] * weight

            doc_norm = math.sqrt(doc_norm_sq) if doc_norm_sq > 0 else 1.0
            sim = dot_product / (q_norm * doc_norm) if (q_norm * doc_norm) > 0 else 0.0
            scores.append((sim, idx))

        scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sim, idx in scores[:top_k]:
            if sim > 0.01:
                doc_copy = dict(self.corpus[idx])
                doc_copy["relevance_score"] = round(sim, 3)
                results.append(doc_copy)

        return results

    def answer_query(self, query: str) -> Dict[str, Any]:
        """
        Answers an operator inquiry using the retrieved emergency SOP knowledge.
        Returns a structured response with guidance, SOP citations, and tactical action.
        """
        matches = self.search(query, top_k=2)

        if not matches:
            return {
                "query": query,
                "synthesized_guidance": "No directly relevant emergency SOP found in local knowledge base. Follow generic SAR safety protocols and contact incident command.",
                "sop_references": [],
                "recommended_action": "Maintain scene safety and escalate to Incident Commander.",
                "confidence": 0.0
            }

        top = matches[0]
        # Synthesize clear answer
        guidance = (
            f"According to {top['sop_id']} ({top['title']}):\n"
            f"{top['content']}"
        )
        sop_refs = [f"{m['sop_id']} - {m['title']}" for m in matches]

        return {
            "query": query,
            "synthesized_guidance": guidance,
            "sop_references": sop_refs,
            "recommended_action": top.get("tactical_action", "Proceed with standard protocol."),
            "confidence": top.get("relevance_score", 0.8)
        }
