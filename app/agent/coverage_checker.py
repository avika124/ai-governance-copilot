"""
Reference coverage template: required areas per risk type.
"""

from typing import Any

REQUIRED_COVERAGE: dict[str, list[str]] = {
    "misinfo": ["deepfake_labeling", "provenance_tracking"],
    "cyber": ["incident_reporting", "vulnerability_disclosure"],
    "surveillance": ["biometric_restrictions", "purpose_limitation"],
    "safety": ["pre_deployment_testing", "red_teaming"],
    "bias": ["algorithmic_audit", "impact_assessment"],
    "reporting": ["incident_timeline", "authority_notification"],
}

# Keywords per sub-area for heuristic matching
_AREA_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "misinfo": {
        "deepfake_labeling": ["deepfake", "synthetic", "label", "disclosure", "manipulated"],
        "provenance_tracking": ["provenance", "watermark", "origin", "metadata", "source"],
    },
    "cyber": {
        "incident_reporting": ["incident", "breach", "notify", "report", "security incident"],
        "vulnerability_disclosure": ["vulnerability", "CVE", "patch", "disclosure", "security flaw"],
    },
    "surveillance": {
        "biometric_restrictions": ["biometric", "facial", "fingerprint", "surveillance"],
        "purpose_limitation": ["purpose", "limited", "specific", "proportionate"],
    },
    "safety": {
        "pre_deployment_testing": ["testing", "validation", "pre-market", "deployment"],
        "red_teaming": ["red team", "adversarial", "stress test", "robustness"],
    },
    "bias": {
        "algorithmic_audit": ["audit", "bias", "fairness", "discrimination"],
        "impact_assessment": ["impact assessment", "FRIA", "fundamental rights"],
    },
    "reporting": {
        "incident_timeline": ["timeline", "without undue delay", "72 hour", "hours"],
        "authority_notification": ["supervisory authority", "regulator", "notify authority"],
    },
}


def check_coverage(
    draft_text: str,
    classified_clauses: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compare draft text + classified clauses against REQUIRED_COVERAGE.

    Returns:
        Grid: risk_type -> area -> {covered: bool, evidence: str}
    """
    combined = (draft_text + " " + " ".join(
        c.get("clause_text", "") for c in classified_clauses
    )).lower()

    grid: dict[str, dict[str, dict[str, Any]]] = {}
    summary_covered = 0
    summary_total = 0

    for risk, areas in REQUIRED_COVERAGE.items():
        grid[risk] = {}
        for area in areas:
            summary_total += 1
            kws = _AREA_KEYWORDS.get(risk, {}).get(area, [])
            covered = any(kw in combined for kw in kws)
            evidence = ""
            if covered:
                for kw in kws:
                    if kw in combined:
                        evidence = f"Mention of '{kw}'"
                        break
                summary_covered += 1
            grid[risk][area] = {
                "covered": covered,
                "evidence": evidence or ("—" if not covered else "matched"),
            }

    return {
        "grid": grid,
        "summary": {
            "covered": summary_covered,
            "total": summary_total,
            "fraction": round(summary_covered / summary_total, 3) if summary_total else 0,
        },
    }
