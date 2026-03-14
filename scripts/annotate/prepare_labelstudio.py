"""
Prepare clauses for Label Studio import.

Exports clauses as Label Studio JSON format with three labeling tasks per clause:
- risk_type
- actor_type
- obligation_type

Output: data/annotated/labelstudio_import.json
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from db.models import Clause
from db.session import SessionLocal, init_db

OUTPUT_PATH = PROJECT_ROOT / "data" / "annotated" / "labelstudio_import.json"

# Label Studio choice options
RISK_TYPES = ["misinfo", "cyber", "surveillance", "safety", "bias", "reporting"]
ACTOR_TYPES = ["model_provider", "app_deployer", "platform", "infra_operator"]
OBLIGATION_TYPES = ["testing", "reporting", "transparency", "logging", "assessment"]


def build_labelstudio_tasks() -> list[dict]:
    """Build Label Studio tasks from clauses."""
    init_db()
    db = SessionLocal()
    tasks = []
    try:
        clauses = db.query(Clause).filter(Clause.is_annotated == False).limit(500).all()
        for c in clauses:
            task = {
                "data": {
                    "text": c.clause_text[:2000],
                    "clause_id": c.id,
                    "article_number": c.article_number,
                },
                "predictions": [],
                "annotations": [],
                "meta": {"regulation_id": c.regulation_id},
            }
            # Add labeling config hints
            task["label_config"] = {
                "risk_type": {"type": "choices", "choices": RISK_TYPES},
                "actor_type": {"type": "choices", "choices": ACTOR_TYPES},
                "obligation_type": {"type": "choices", "choices": OBLIGATION_TYPES},
            }
            tasks.append(task)
    finally:
        db.close()
    return tasks


def main() -> None:
    """Export clauses to Label Studio JSON."""
    tasks = build_labelstudio_tasks()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    print(f"Exported {len(tasks)} tasks to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
