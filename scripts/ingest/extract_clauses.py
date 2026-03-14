"""
Extract clause-level chunks from article/section text.

Splits article text into individual clause sentences using spaCy.
Each sentence becomes one row in the clauses table.
Auto-detects article/section number from headings.
"""

import re
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session

from db.models import Clause, Regulation
from db.session import SessionLocal, init_db


def load_spacy() -> Optional["spacy.Language"]:
    """Load spaCy model. Downloads en_core_web_sm if not present."""
    try:
        import spacy

        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading en_core_web_sm...")
            import subprocess

            subprocess.run(
                [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
                check=True,
            )
            nlp = spacy.load("en_core_web_sm")
        return nlp
    except Exception as e:
        print(f"spaCy not available: {e}")
        return None


def split_into_sentences(text: str, nlp) -> list[str]:
    """
    Split text into sentences using spaCy.

    Args:
        text: Raw clause/article text.
        nlp: Loaded spaCy model.

    Returns:
        List of sentence strings.
    """
    if not text or not nlp:
        return [text] if text and len(text.strip()) > 0 else []

    doc = nlp(text[:100000])  # Limit length for performance
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 10]
    return sentences if sentences else [text.strip()]


def split_by_numbered_clauses(text: str) -> list[str]:
    """
    Split text by numbered sub-clauses (e.g. 1., 2., (a), (b)).

    Returns:
        List of clause strings.
    """
    clauses: list[str] = []
    # Pattern: "1." or "(a)" or "1.1" at start of line
    pattern = re.compile(
        r"^(?:\d+\.|\d+\.\d+\.?|\(\s*[a-z]\s*\)|\(\s*[ivx]+\s*\))\s*",
        re.IGNORECASE | re.MULTILINE,
    )
    parts = pattern.split(text)
    if len(parts) > 1:
        for p in parts[1:]:
            p = p.strip()
            if len(p) > 15:
                clauses.append(p)
    return clauses


def extract_clauses_from_article(
    article_text: str,
    article_number: str,
    nlp,
    use_sentences: bool = True,
) -> list[tuple[str, str]]:
    """
    Extract clause-level chunks from article text.

    Tries numbered sub-clauses first, then falls back to sentence splitting.

    Returns:
        List of (article_number.sub, clause_text) e.g. ("5.1", "text")
    """
    clauses: list[tuple[str, str]] = []

    numbered = split_by_numbered_clauses(article_text)
    if numbered:
        for i, c in enumerate(numbered, 1):
            sub_id = f"{article_number}.{i}"
            clauses.append((sub_id, c))
        return clauses

    if use_sentences and nlp:
        sentences = split_into_sentences(article_text, nlp)
        for i, s in enumerate(sentences, 1):
            sub_id = f"{article_number}.{i}"
            clauses.append((sub_id, s))
        return clauses

    # Fallback: single clause
    if article_text.strip():
        clauses.append((article_number, article_text.strip()))
    return clauses


def process_regulation(db: Session, regulation_id: int, nlp) -> int:
    """
    Process all clauses for a regulation: split article-level into clause-level.

    Replaces existing article-level clauses with finer clause-level entries.
    """
    # Get existing clauses (article-level)
    existing = (
        db.query(Clause)
        .filter(Clause.regulation_id == regulation_id)
        .order_by(Clause.id)
        .all()
    )

    if not existing:
        return 0

    new_clauses: list[dict] = []
    for c in existing:
        sub_clauses = extract_clauses_from_article(
            c.clause_text, c.article_number, nlp
        )
        for sub_num, sub_text in sub_clauses:
            new_clauses.append(
                {
                    "regulation_id": regulation_id,
                    "article_number": sub_num,
                    "clause_text": sub_text[:15000],
                    "is_annotated": c.is_annotated,
                }
            )

    # Delete old article-level clauses and insert new
    for c in existing:
        db.delete(c)
    db.flush()

    for nc in new_clauses:
        clause = Clause(**nc)
        db.add(clause)

    db.commit()
    return len(new_clauses)


def main() -> None:
    """Extract clause-level chunks for all regulations."""
    init_db()
    nlp = load_spacy()
    if not nlp:
        print("Cannot proceed without spaCy. Install: pip install spacy && python -m spacy download en_core_web_sm")
        return

    db = SessionLocal()
    try:
        regs = db.query(Regulation).all()
        total = 0
        for reg in regs:
            count = process_regulation(db, reg.id, nlp)
            print(f"  {reg.law_name}: {count} clauses")
            total += count
        print(f"\nTotal clauses: {total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
