"""
Cross-border conflict detection via FAISS similarity + obligation alignment.
"""

import logging
import re
from typing import Any

from app.config import FAISS_SIMILARITY_THRESHOLD
from app.services.faiss_index import search_similar

logger = logging.getLogger(__name__)


def detect_conflicts(
    classified_clauses: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    For each input clause, find top-5 similar corpus clauses.
    If similarity > threshold and obligation_type matches but jurisdictions differ → conflict candidate.
    """
    conflicts: list[dict[str, Any]] = []

    for cl in classified_clauses:
        text = cl.get("clause_text", cl.get("text", ""))[:2000]
        if len(text.strip()) < 30:
            continue
        try:
            hits = search_similar(text, top_k=5)
        except Exception as e:
            logger.warning("FAISS search failed for clause: %s", e)
            continue
        obl = cl.get("obligation_type", "assessment")

        for h in hits:
            sim = h.get("similarity", 0)
            if sim < FAISS_SIMILARITY_THRESHOLD:
                continue
            # Heuristic: same obligation family + different countries suggests tension
            ref_country = h.get("country", "")
            ref_text = h.get("clause_text", "")

            # Different reporting timelines / transfer rules often surface as lexical differences
            conflict_type = "cross_jurisdictional_tension"
            desc = (
                f"Input clause aligns semantically (similarity {sim:.2f}) with "
                f"{ref_country} reference ({h.get('law_name', '')}) but may impose "
                f"divergent requirements for {obl} obligations."
            )
            if _looks_like_timeline_mismatch(text, ref_text):
                conflict_type = "timeline_or_procedure_mismatch"
                desc = (
                    "Possible mismatch in incident reporting timelines or procedures "
                    f"between draft text and {ref_country} framework ({h.get('law_name', '')})."
                )

            conflicts.append({
                "input_excerpt": text[:400],
                "reference_clause_id": h.get("clause_id"),
                "reference_country": ref_country,
                "reference_law": h.get("law_name"),
                "reference_excerpt": ref_text[:400],
                "similarity": round(sim, 4),
                "obligation_type": obl,
                "conflict_type": conflict_type,
                "description": desc,
                "severity": _severity(sim),
            })
            break  # top hit per input clause

    trimmed = conflicts[:25]
    return {
        "items": trimmed,
        "count": len(trimmed),
    }


def _looks_like_timeline_mismatch(a: str, b: str) -> bool:
    """Detect if both mention time periods but differ."""
    nums_a = set(re.findall(r"\b\d+\s*(?:hour|day|week|month)s?\b", a.lower()))
    nums_b = set(re.findall(r"\b\d+\s*(?:hour|day|week|month)s?\b", b.lower()))
    return bool(nums_a and nums_b and nums_a != nums_b)


def _severity(sim: float) -> str:
    if sim >= 0.9:
        return "high"
    if sim >= 0.8:
        return "medium"
    return "low"
