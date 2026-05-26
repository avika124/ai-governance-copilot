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


def parse_clauses(draft_text: str) -> list[dict[str, Any]]:
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


def run_pipeline(draft_text: str, persist: bool = True) -> dict[str, Any]:
    if len(draft_text) > 100_000:
        draft_text = draft_text[:100_000]

    clauses = parse_clauses(draft_text)

    if not clauses:
        empty_coverage = {"grid": {}, "summary": {"covered": 0, "total": 0, "fraction": 0}}
        return {
            "input_preview": draft_text[:500],
            "clause_count": 0,
            "classified_clauses": [],
            "coverage": empty_coverage,
            "conflicts": {"items": [], "count": 0},
            "recommendations": {
                "minimal": {"title": "Insufficient input", "summary": "Please paste complete draft policy language.", "sample_language": ""},
                "moderate": {"title": "Insufficient input", "summary": "No analysis could be performed.", "sample_language": ""},
                "strict": {"title": "Insufficient input", "summary": "No analysis could be performed.", "sample_language": ""},
                "gaps_addressed_next": [],
            },
            "report_id": None,
            "no_clauses": True,
        }

    classified = classify_clauses(clauses)
    coverage = check_coverage(draft_text, classified)
    conflicts = detect_conflicts(classified)
    recommendations = generate_recommendations(coverage, conflicts)

    report = {
        "input_preview": draft_text[:500],
        "clause_count": len(classified),
        "classified_clauses": classified[:50],
        "coverage": coverage,
        "conflicts": conflicts,
        "recommendations": recommendations,
        "report_id": None,
    }

    # Only try to persist if DB is available
    if persist:
        try:
            from app.services.database import insert_analysis_report
            rid = insert_analysis_report(draft_text, coverage, conflicts, recommendations)
            report["report_id"] = rid
        except Exception as e:
            logger.warning("Could not persist report (no DB): %s", e)

    return report
