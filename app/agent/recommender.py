"""
Policy recommendation cards: minimal / moderate / strict.
"""

from typing import Any


def generate_recommendations(
    coverage: dict[str, Any],
    conflicts: dict[str, Any],
) -> dict[str, Any]:
    """
    Produce three policy option cards with sample legislative language.
    """
    grid = coverage.get("grid", {})
    missing: list[str] = []
    for risk, areas in grid.items():
        for area, info in areas.items():
            if not info.get("covered"):
                missing.append(f"{risk}:{area}")

    conflict_count = conflicts.get("count", 0)

    # Full compliance fast-path
    if not missing and not conflict_count:
        compliant_card = {
            "title": "Full compliance indicated",
            "summary": (
                "The draft text addresses all required coverage sub-areas and no cross-border "
                "tensions were identified against the reference corpus. Consider periodic "
                "re-evaluation as regulations evolve."
            ),
            "sample_language": "",
        }
        return {
            "minimal": compliant_card,
            "moderate": compliant_card,
            "strict": compliant_card,
            "gaps_addressed_next": [],
            "full_compliance": True,
        }

    conflict_note = ""
    if conflict_count:
        conflict_note = (
            f"Detected {conflict_count} potential cross-border tension(s); "
            "align timelines and data-transfer clauses with stricter jurisdiction where operating."
        )

    minimal = {
        "title": "Minimal alignment",
        "summary": "Disclose AI use in terms of service; maintain incident logs for 12 months.",
        "sample_language": (
            "The provider shall maintain reasonable records of significant incidents affecting "
            "the availability or integrity of the service and shall notify affected users where required by law."
        ),
    }
    moderate = {
        "title": "Moderate alignment (EU AI Act–style)",
        "summary": "Risk management system, technical documentation, human oversight for high-risk systems.",
        "sample_language": (
            "High-risk AI systems shall be subject to a quality management system, post-market monitoring, "
            "and registration in the EU database prior to placement on the market, where applicable."
        ),
    }
    strict = {
        "title": "Strict alignment (multi-jurisdiction)",
        "summary": "Short incident notification windows, DPIA, cross-border transfer safeguards, red-team testing.",
        "sample_language": (
            "Without prejudice to stricter national requirements, significant incidents shall be notified "
            "to the competent authority within the shortest period required across jurisdictions in which "
            "the operator is established, and personal data transfers shall rely on adequacy or SCCs as applicable."
        ),
    }

    if missing:
        moderate["summary"] += f" Address gaps: {', '.join(missing[:5])}"
        if len(missing) > 5:
            moderate["summary"] += "…"

    if conflict_note:
        strict["summary"] = conflict_note + " " + strict["summary"]

    return {
        "minimal": minimal,
        "moderate": moderate,
        "strict": strict,
        "gaps_addressed_next": missing[:12],
    }
