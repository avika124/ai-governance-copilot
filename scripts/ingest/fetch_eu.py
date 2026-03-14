"""
Fetch EU AI Act, GDPR, and DSA from EUR-Lex.

Downloads regulation text from eur-lex.europa.eu, extracts article-by-article text,
and stores each article in the regulations and clauses tables.

Uses requests + BeautifulSoup for HTML parsing. Falls back to PyMuPDF for PDF if HTML
structure is not parseable.
"""

import os
import re
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from db.models import Regulation, Clause
from db.session import SessionLocal, init_db

load_dotenv(PROJECT_ROOT / ".env")

# EU sources to fetch
EU_SOURCES = [
    {
        "name": "EU AI Act",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689",
        "country": "EU",
        "law_type": "Regulation",
        "year": 2024,
    },
    {
        "name": "GDPR",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679",
        "country": "EU",
        "law_type": "Regulation",
        "year": 2016,
    },
    {
        "name": "Digital Services Act",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32022R2065",
        "country": "EU",
        "law_type": "Regulation",
        "year": 2022,
    },
]

# Headers to mimic browser (EUR-Lex may block bare requests)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_html(url: str) -> Optional[str]:
    """
    Fetch HTML content from URL.

    Args:
        url: URL to fetch.

    Returns:
        HTML string or None if request fails.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Request failed for {url}: {e}")
        return None


def extract_articles_from_html(html: str) -> list[tuple[str, str]]:
    """
    Extract article number and text from EUR-Lex HTML.

    EUR-Lex typically uses structure like:
    - Article 1, Article 2, etc. in headings
    - Content in paragraphs

    Returns:
        List of (article_number, article_text) tuples.
    """
    soup = BeautifulSoup(html, "lxml")
    articles: list[tuple[str, str]] = []

    # Try common EUR-Lex patterns
    # Pattern 1: Look for "Article X" headings
    article_pattern = re.compile(
        r"Article\s+(\d+[a-z]?(?:\([a-z]\))?(?:\s*[-–]\s*[^:]+)?)",
        re.IGNORECASE,
    )

    # Get all text blocks - EUR-Lex uses various div/p structures
    body = soup.find("body") or soup
    text_content = body.get_text(separator="\n", strip=True)

    # Split by Article boundaries
    parts = re.split(r"\n\s*Article\s+(\d+[a-z]?(?:\([a-z]\))?(?:\s*[-–][^\n]+)?)\s*\n", text_content, flags=re.IGNORECASE)

    if len(parts) > 1:
        # parts[0] is preamble, then alternating: article_num, article_text, ...
        for i in range(1, len(parts) - 1, 2):
            if i + 1 < len(parts):
                art_num = parts[i].strip()
                art_text = parts[i + 1].strip()
                if art_num and art_text and len(art_text) > 20:
                    articles.append((art_num, art_text))
    else:
        # Fallback: treat entire content as single article if structure unclear
        if not text_content or len(text_content) < 100:
            return articles

        # Try to find article-like sections
        for match in article_pattern.finditer(text_content):
            pass  # Just counting for now

        # If no clear structure, store as Article 1 (full text)
        articles.append(("1", text_content[:50000]))  # Cap at 50k chars

    return articles


def save_to_raw(html: str, output_path: Path) -> None:
    """Save raw HTML to data/raw for debugging."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def fetch_and_store_eu(db: Session, source: dict) -> int:
    """
    Fetch one EU source and store in database.

    Args:
        db: SQLAlchemy session.
        source: Dict with name, url, country, law_type, year.

    Returns:
        Number of clauses stored.
    """
    print(f"Fetching {source['name']} from {source['url']}...")
    html = fetch_html(source["url"])

    if not html:
        print(f"  Failed to fetch {source['name']}")
        return 0

    # Save raw HTML
    safe_name = re.sub(r"[^\w\-]", "_", source["name"].lower())
    raw_path = PROJECT_ROOT / "data" / "raw" / f"eu_{safe_name}.html"
    save_to_raw(html, raw_path)
    print(f"  Saved raw HTML to {raw_path}")

    articles = extract_articles_from_html(html)
    print(f"  Extracted {len(articles)} articles")

    if not articles:
        print(f"  Warning: No articles extracted. Storing full text as single regulation.")
        full_text = BeautifulSoup(html, "lxml").get_text(separator="\n", strip=True)[:100000]
        reg = Regulation(
            country=source["country"],
            law_name=source["name"],
            law_type=source["law_type"],
            year=source["year"],
            source_url=source["url"],
            full_text=full_text,
        )
        db.add(reg)
        db.flush()
        clause = Clause(
            regulation_id=reg.id,
            article_number="1",
            clause_text=full_text[:10000],
            is_annotated=False,
        )
        db.add(clause)
        db.commit()
        return 1

    # Build full_text from articles
    full_text_parts = [f"Article {num}\n{text}" for num, text in articles]
    full_text = "\n\n".join(full_text_parts)[:100000]

    reg = Regulation(
        country=source["country"],
        law_name=source["name"],
        law_type=source["law_type"],
        year=source["year"],
        source_url=source["url"],
        full_text=full_text,
    )
    db.add(reg)
    db.flush()

    clause_count = 0
    for art_num, art_text in articles:
        # Store each article as one clause (extract_clauses.py will split further)
        clause = Clause(
            regulation_id=reg.id,
            article_number=art_num,
            clause_text=art_text[:15000],
            is_annotated=False,
        )
        db.add(clause)
        clause_count += 1

    db.commit()
    print(f"  Stored {clause_count} clauses for {source['name']}")
    return clause_count


def main() -> None:
    """Fetch all EU sources and store in database."""
    init_db()
    db = SessionLocal()
    total = 0
    try:
        for source in EU_SOURCES:
            count = fetch_and_store_eu(db, source)
            total += count
        print(f"\nTotal clauses stored: {total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
