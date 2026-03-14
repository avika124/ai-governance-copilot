"""
Prepare clauses for Label Studio import.

Exports clauses from Supabase as Label Studio JSON format.
Three labeling tasks per clause: risk_type, actor_type, obligation_type.

Output: data_pipeline/annotated/labelstudio_import.json

Usage:
    cd data_pipeline && python -m annotate.prepare_labelstudio
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db_client import get_connection

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "annotated" / "labelstudio_import.json"

# Label Studio choice options (for project config reference)
RISK_TYPES = ["misinfo", "cyber", "surveillance", "safety", "bias", "reporting"]
ACTOR_TYPES = ["model_provider", "app_deployer", "platform", "infra_operator"]
OBLIGATION_TYPES = ["testing", "reporting", "transparency", "logging", "assessment"]

# Max clauses to export (for initial annotation batch)
DEFAULT_LIMIT = 500


def fetch_clauses(limit: int = DEFAULT_LIMIT) -> list[dict]:
    """
    Fetch clauses from Supabase for annotation.

    Returns:
        List of dicts with clause_id, regulation_id, article_number, clause_text.
    """
    conn = get_connection()
    clauses = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.clause_id, c.regulation_id, c.article_number, c.clause_text
                FROM clauses c
                ORDER BY c.regulation_id, c.article_number
                LIMIT %s
                """,
                (limit,),
            )
            for row in cur.fetchall():
                clauses.append({
                    "clause_id": row[0],
                    "regulation_id": row[1],
                    "article_number": row[2],
                    "clause_text": row[3] or "",
                })
    finally:
        conn.close()
    return clauses


def build_labelstudio_tasks(clauses: list[dict]) -> list[dict]:
    """
    Convert clauses to Label Studio task format.

    Each task has:
    - data.text: clause text (truncated to 2000 chars)
    - meta: clause_id, regulation_id, article_number
    """
    tasks = []
    for c in clauses:
        text = (c["clause_text"] or "")[:2000]
        if len(text.strip()) < 30:
            continue
        tasks.append({
            "data": {"text": text},
            "meta": {
                "clause_id": c["clause_id"],
                "regulation_id": c["regulation_id"],
                "article_number": c["article_number"],
            },
        })
    return tasks


def main() -> None:
    """Export clauses to Label Studio JSON."""
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LIMIT
    clauses = fetch_clauses(limit=limit)
    tasks = build_labelstudio_tasks(clauses)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    print(f"Exported {len(tasks)} tasks to {OUTPUT_PATH}")
    print(f"Label config options: risk_type={RISK_TYPES}, actor_type={ACTOR_TYPES}, obligation_type={OBLIGATION_TYPES}")


if __name__ == "__main__":
    main()
