"""
Fetch DPDP Act 2023 and IT Act from India Code.

Downloads regulation text from indiacode.nic.in. Uses PDF download + PyMuPDF for
extraction when HTML structure is not suitable. Also supports scraping individual
sections from show-data pages.

Stores each section as a row in regulations and clauses tables.
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

from db.models import Regulation, Clause
from db.session import SessionLocal, init_db

load_dotenv(PROJECT_ROOT / ".env")

# India sources
INDIA_SOURCES = [
    {
        "name": "Digital Personal Data Protection Act",
        "short_name": "DPDP Act",
        "pdf_url": "https://www.indiacode.nic.in/bitstream/123456789/22037/1/a2023-22.pdf",
        "browse_url": "https://www.indiacode.nic.in/handle/123456789/22037?view_type=browse",
        "country": "India",
        "law_type": "Act",
        "year": 2023,
    },
    {
        "name": "Information Technology Act",
        "short_name": "IT Act",
        "browse_url": "https://www.indiacode.nic.in/handle/123456789/1362",
        "country": "India",
        "law_type": "Act",
        "year": 2000,
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/pdf,text/html,*/*",
}


def fetch_pdf(url: str, output_path: Path) -> bool:
    """
    Download PDF from URL and save to file.

    Returns:
        True if successful.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  PDF download failed: {e}")
        return False


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text from PDF using PyMuPDF.

    Returns:
        Full text content.
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)
    except ImportError:
        print("  PyMuPDF (fitz) not installed. Run: pip install pymupdf")
        return ""
    except Exception as e:
        print(f"  PDF extraction failed: {e}")
        return ""


def extract_sections_from_text(text: str) -> list[tuple[str, str]]:
    """
    Split regulation text into sections by 'Section X' or 'Section X.' pattern.

    Returns:
        List of (section_number, section_text) tuples.
    """
    sections: list[tuple[str, str]] = []
    # Match "Section 1.", "Section 2.", "Section 10.", "Section 1A.", etc.
    pattern = re.compile(
        r"Section\s+(\d+[A-Za-z]?(?:\([a-z]\))?)\.?\s*([^\n]*)",
        re.IGNORECASE,
    )

    parts = re.split(
        r"\n\s*Section\s+(\d+[A-Za-z]?(?:\([a-z]\))?)\.?\s*",
        text,
        flags=re.IGNORECASE,
    )

    if len(parts) > 1:
        # parts[0] = preamble, then alternating: section_num, section_text
        for i in range(1, len(parts) - 1, 2):
            if i + 1 < len(parts):
                sec_num = parts[i].strip()
                sec_text = parts[i + 1].strip()
                if sec_num and sec_text and len(sec_text) > 10:
                    sections.append((sec_num, sec_text))
    else:
        # Fallback: split by numbered sections
        for m in pattern.finditer(text):
            sec_num = m.group(1)
            title = m.group(2).strip() if m.lastindex >= 2 else ""
            start = m.end()
            next_m = pattern.search(text, start)
            end = next_m.start() if next_m else len(text)
            sec_text = (title + "\n" + text[start:end]).strip()
            if len(sec_text) > 20:
                sections.append((sec_num, sec_text))

    return sections


def save_to_raw(content: str, output_path: Path) -> None:
    """Save raw content to data/raw."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def fetch_and_store_india(db, source: dict) -> int:
    """
    Fetch one India source and store in database.

    Uses PDF when available, else attempts HTML scrape of browse page.
    """
    print(f"Fetching {source['name']}...")

    pdf_url = source.get("pdf_url")
    raw_path = PROJECT_ROOT / "data" / "raw"
    safe_name = re.sub(r"[^\w\-]", "_", source["short_name"].lower())

    text = ""
    if pdf_url:
        pdf_path = raw_path / f"india_{safe_name}.pdf"
        if fetch_pdf(pdf_url, pdf_path):
            print(f"  Downloaded PDF to {pdf_path}")
            text = extract_text_from_pdf(pdf_path)
            if text:
                txt_path = raw_path / f"india_{safe_name}.txt"
                save_to_raw(text[:100000], txt_path)
        else:
            print(f"  PDF not available, trying HTML...")
    else:
        print(f"  No PDF URL, trying HTML browse page...")

    if not text and source.get("browse_url"):
        try:
            response = requests.get(
                source["browse_url"], headers=HEADERS, timeout=30
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            text = soup.get_text(separator="\n", strip=True)
            html_path = raw_path / f"india_{safe_name}.html"
            save_to_raw(response.text, html_path)
        except Exception as e:
            print(f"  HTML fetch failed: {e}")

    if not text or len(text) < 100:
        print(f"  Could not extract text for {source['name']}")
        return 0

    sections = extract_sections_from_text(text)
    print(f"  Extracted {len(sections)} sections")

    if not sections:
        full_text = text[:100000]
        reg = Regulation(
            country=source["country"],
            law_name=source["name"],
            law_type=source["law_type"],
            year=source["year"],
            source_url=source.get("browse_url") or source.get("pdf_url"),
            full_text=full_text,
        )
        db.add(reg)
        db.flush()
        clause = Clause(
            regulation_id=reg.id,
            article_number="1",
            clause_text=full_text[:15000],
            is_annotated=False,
        )
        db.add(clause)
        db.commit()
        return 1

    full_text_parts = [f"Section {num}\n{txt}" for num, txt in sections]
    full_text = "\n\n".join(full_text_parts)[:100000]

    reg = Regulation(
        country=source["country"],
        law_name=source["name"],
        law_type=source["law_type"],
        year=source["year"],
        source_url=source.get("browse_url") or source.get("pdf_url"),
        full_text=full_text,
    )
    db.add(reg)
    db.flush()

    clause_count = 0
    for sec_num, sec_text in sections:
        clause = Clause(
            regulation_id=reg.id,
            article_number=sec_num,
            clause_text=sec_text[:15000],
            is_annotated=False,
        )
        db.add(clause)
        clause_count += 1

    db.commit()
    print(f"  Stored {clause_count} clauses for {source['name']}")
    return clause_count


def main() -> None:
    """Fetch all India sources and store in database."""
    init_db()
    db = SessionLocal()
    total = 0
    try:
        for source in INDIA_SOURCES:
            count = fetch_and_store_india(db, source)
            total += count
        print(f"\nTotal clauses stored: {total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
