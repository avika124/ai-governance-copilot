"""
Shared text → clause splitting utility.

Uses spaCy (en_core_web_sm) to split article text into sentences.
Each sentence becomes one clause. Skips short sentences, numbers, headers.
Detects article_number from patterns. Generates clause_id as UUID4.
"""

import logging
import re
import sys
import uuid
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import ARTICLE_PATTERNS, CLAUSE_BATCH_SIZE, MIN_CLAUSE_LENGTH

logger = logging.getLogger(__name__)

_nlp: Optional[object] = None


def _load_spacy():
    """Load spaCy model. Downloads en_core_web_sm if not present."""
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.info("Downloading en_core_web_sm...")
            import subprocess
            subprocess.run(
                [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
                check=True,
            )
            _nlp = spacy.load("en_core_web_sm")
        return _nlp
    except Exception as e:
        logger.error("spaCy not available: %s", e)
        return None


def _is_skip_sentence(text: str) -> bool:
    """
    Return True if sentence should be skipped.

    Skips: under MIN_CLAUSE_LENGTH chars, just numbers, headers, article refs.
    """
    t = text.strip()
    if len(t) < MIN_CLAUSE_LENGTH:
        return True
    if re.match(r"^[\d\s\.\-\(\)]+$", t):
        return True
    if re.match(r"^(Article|Section|Clause)\s+\d+", t, re.IGNORECASE):
        return True
    if re.match(r"^\d+\.\s*$", t):
        return True
    return False


def _detect_article_number(text: str) -> str:
    """
    Detect article/section number from text using configured patterns.

    Returns:
        Article number string, or "1" if not detected.
    """
    for pattern in ARTICLE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    return "1"


def extract_clauses(
    raw_text: str,
    regulation_id: str,
    article_number: Optional[str] = None,
) -> list[dict]:
    """
    Split raw text into clause-level chunks.

    Uses spaCy for sentence splitting. Each sentence becomes one clause row.
    Skips sentences under 30 chars, numbers, headers, article references.
    Generates clause_id as UUID4.

    Args:
        raw_text: Full article/section text.
        regulation_id: FK to regulations table.
        article_number: Explicit article/section number. If None, detected from text.

    Returns:
        List of dicts with clause_id, regulation_id, article_number,
        clause_text, char_count.
    """
    nlp = _load_spacy()
    clauses: list[dict] = []

    if not raw_text or not raw_text.strip():
        return clauses

    article_num = article_number or _detect_article_number(raw_text) or "1"

    if nlp:
        doc = nlp(raw_text[:100000])
        for sent in doc.sents:
            t = sent.text.strip()
            if _is_skip_sentence(t):
                continue
            clauses.append({
                "clause_id": str(uuid.uuid4()),
                "regulation_id": regulation_id,
                "article_number": article_num,
                "clause_text": t,
                "char_count": len(t),
            })
    else:
        # Fallback: split by sentence-ending punctuation
        parts = re.split(r"(?<=[.!?])\s+", raw_text)
        for p in parts:
            t = p.strip()
            if _is_skip_sentence(t):
                continue
            clauses.append({
                "clause_id": str(uuid.uuid4()),
                "regulation_id": regulation_id,
                "article_number": article_num,
                "clause_text": t,
                "char_count": len(t),
            })

    return clauses


def extract_clauses_from_articles(
    articles: list[tuple[str, str]],
    regulation_id: str,
) -> list[dict]:
    """
    Extract clauses from a list of (article_number, article_text) tuples.

    Args:
        articles: List of (article_number, text) pairs.
        regulation_id: FK to regulations table.

    Returns:
        List of clause dicts.
    """
    all_clauses: list[dict] = []
    for art_num, art_text in articles:
        for c in extract_clauses(art_text, regulation_id, article_number=art_num):
            all_clauses.append(c)
    return all_clauses
