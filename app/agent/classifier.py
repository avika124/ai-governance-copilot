"""
Lightweight clause tagging: risk_type, actor_type, obligation_type.

Uses keyword priors (no fine-tuned DeBERTa required for baseline operation).
"""

from typing import Any

RISK_KEYWORDS = {
    "misinfo": ["misinformation", "disinformation", "deepfake", "synthetic media"],
    "cyber": ["cyber", "security", "vulnerability", "incident", "breach", "malware"],
    "surveillance": ["surveillance", "biometric", "monitoring", "facial recognition"],
    "safety": ["safety", "high-risk", "testing", "harm", "conformity"],
    "bias": ["bias", "discrimination", "fairness", "fundamental rights"],
    "reporting": ["report", "notify", "notification", "authority", "timeline"],
}

ACTOR_KEYWORDS = {
    "model_provider": ["provider", "model", "general purpose", "GPAI"],
    "app_deployer": ["deployer", "deploy", "user", "downstream"],
    "platform": ["platform", "intermediary", "hosting", "online"],
    "infra_operator": ["infrastructure", "operator", "cloud", "compute"],
}

OBL_KEYWORDS = {
    "testing": ["test", "validation", "conformity assessment"],
    "reporting": ["report", "notify", "notification"],
    "transparency": ["transparency", "disclose", "documentation"],
    "logging": ["log", "record", "retention"],
    "assessment": ["assessment", "audit", "evaluation"],
}


def _score_keywords(text: str, mapping: dict[str, list[str]]) -> dict[str, float]:
    t = text.lower()
    scores = {}
    for label, kws in mapping.items():
        scores[label] = sum(1 for k in kws if k in t) / max(len(kws), 1)
    return scores


def classify_clause(text: str) -> dict[str, str]:
    """Return primary risk_type, actor_type, obligation_type for one clause."""
    if len(text.strip()) < 15:
        return {
            "risk_type": "reporting",
            "actor_type": "platform",
            "obligation_type": "transparency",
        }

    rs = _score_keywords(text, RISK_KEYWORDS)
    risk = max(rs, key=rs.get)

    as_ = _score_keywords(text, ACTOR_KEYWORDS)
    actor = max(as_, key=as_.get)
    if as_[actor] == 0:
        actor = "platform"

    os_ = _score_keywords(text, OBL_KEYWORDS)
    obl = max(os_, key=os_.get)
    if os_[obl] == 0:
        obl = "assessment"

    return {
        "risk_type": risk,
        "actor_type": actor,
        "obligation_type": obl,
    }


def classify_clauses(clauses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Augment each clause dict with classification fields."""
    out = []
    for c in clauses:
        text = c.get("clause_text", c.get("text", ""))
        tags = classify_clause(text)
        row = {**c, **tags}
        out.append(row)
    return out
