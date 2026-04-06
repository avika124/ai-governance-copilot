"""
End-to-end analysis pipeline for draft AI policy text.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

from app.agent.classifier import classify_clauses
from app.agent.conflict_detector import detect_conflicts
from app.agent.coverage_checker import check_coverage
from app.agent.recommender import generate_recommendations
from app.services.database import insert_analysis_report


def parse_clauses(draft_text: str) -> list[dict[str, Any]]:
    """
    Split draft into sentence-level clauses.

    Uses regex split if spaCy unavailable; otherwise spaCy sents.
    """
    text = draft_text.strip()
    if not text:
        return []

    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text[:100000])
        sents = [s.text.strip() for s in doc.sents if len(s.text.strip()) > 25]
    except Exception:
        sents = re.split(r"(?<=[.!?])\s+", text)
        sents = [s.strip() for s in sents if len(s.strip()) > 25]

    return [{"clause_text": s, "article_number": "draft"} for s in sents[:500]]


def run_pipeline(
    draft_text: str,
    persist: bool = True,
) -> dict[str, Any]:
    """
    Execute full analysis: parse → classify → coverage → conflicts → recommendations.

    Returns structured JSON report.
    """
    clauses = parse_clauses(draft_text)
    classified = classify_clauses(clauses)
    coverage = check_coverage(draft_text, classified)
    conflicts = detect_conflicts(classified)
    recommendations = generate_recommendations(coverage, conflicts)

    report = {
        "input_preview": draft_text[:500],
        "clause_count": len(classified),
        "classified_clauses": classified[:50],  # trim for response size
        "coverage": coverage,
        "conflicts": conflicts,
        "recommendations": recommendations,
    }

    if persist:
        try:
            rid = insert_analysis_report(
                draft_text,
                coverage,
                conflicts,
                recommendations,
            )
            report["report_id"] = rid
        except Exception as e:
            logger.warning("Could not persist report: %s", e)
            report["report_id"] = None

    return report
