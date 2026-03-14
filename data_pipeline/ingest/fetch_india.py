"""
Fetch India laws from legislative.gov.in (PDFs).

Uses PyMuPDF (fitz) for all India PDFs.
Tags each regulation with law_category from config.
"""

import io
import logging
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import (
    CLAUSE_BATCH_SIZE,
    INDIA_LAWS,
    PDF_DOWNLOAD_TIMEOUT,
    REQUEST_HEADERS,
)
from db_client import insert_clauses_batch, insert_regulation, regulation_exists
from ingest.extract_clauses import extract_clauses_from_articles

logger = logging.getLogger(__name__)

# Browser-like headers for legislative.gov.in
INDIA_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://legislative.gov.in/",
    "Connection": "keep-alive",
}


def fetch_pdf(url: str) -> Optional[bytes]:
    """
    Download a PDF from any Indian government source.

    Detects the host and uses appropriate session/headers.
    Verifies the response is actually a PDF before returning.

    Returns:
        PDF bytes or None if request fails or response is not a PDF.
    """
    try:
        session = requests.Session()
        session.headers.update(INDIA_HEADERS)

        # Visit the appropriate homepage to pick up session cookies
        if "indiacode.nic.in" in url:
            homepage = "https://www.indiacode.nic.in"
        elif "mha.gov.in" in url:
            homepage = "https://www.mha.gov.in"
        else:
            homepage = "https://legislative.gov.in"

        try:
            session.get(homepage, timeout=15, allow_redirects=True)
        except Exception:
            pass

        response = session.get(
            url,
            timeout=PDF_DOWNLOAD_TIMEOUT,
            allow_redirects=True,
            stream=False,
        )

        if response.status_code == 404:
            logger.warning("404 for %s", url)
            return None
        response.raise_for_status()

        content = response.content
        if not content.startswith(b"%PDF"):
            logger.error(
                "Response for %s is not a PDF (got %d bytes, starts with %r)",
                url, len(content), content[:20],
            )
            return None

        logger.debug("Downloaded %d bytes from %s", len(content), url)
        return content

    except requests.RequestException as e:
        logger.error("PDF download failed for %s: %s", url, e)
        return None


def extract_text_from_pdf(pdf_bytes: bytes) -> Optional[str]:
    """
    Extract text from PDF bytes using PyMuPDF.

    Returns:
        Full text or None if extraction fails.
    """
    try:
        import fitz
        doc = fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf")
        text_parts = [p.get_text() for p in doc]
        doc.close()
        full_text = "\n".join(text_parts)
        logger.debug("Extracted %d chars from PDF", len(full_text))
        return full_text
    except ImportError:
        logger.error("PyMuPDF (fitz) not installed. Run: pip install pymupdf")
        return None
    except Exception as e:
        logger.error("PDF extraction failed: %s", e)
        return None


def extract_sections_from_text(text: str) -> list[tuple[str, str]]:
    """
    Split regulation text into sections by 'Section X' pattern.

    Returns:
        List of (section_number, section_text) tuples.
    """
    pattern = re.compile(
        r"\n\s*Section\s+(\d+[A-Za-z]?(?:\([a-z]\))?)\.?\s*",
        re.IGNORECASE,
    )
    parts = pattern.split(text)

    sections: list[tuple[str, str]] = []
    if len(parts) > 1:
        for i in range(1, len(parts) - 1, 2):
            if i + 1 < len(parts):
                sec_num = parts[i].strip()
                sec_text = parts[i + 1].strip()
                if sec_num and sec_text and len(sec_text) > 10:
                    sections.append((sec_num, sec_text))
    else:
        # Fallback: try "Section X." pattern
        for m in re.finditer(
            r"Section\s+(\d+[A-Za-z]?)\.?\s*([^\n]*)",
            text,
            re.IGNORECASE,
        ):
            sec_num = m.group(1)
            title = m.group(2).strip() if m.lastindex >= 2 else ""
            start = m.end()
            next_m = re.search(
                r"Section\s+\d+[A-Za-z]?\.?\s*",
                text[start:],
                re.IGNORECASE,
            )
            end = start + (next_m.start() if next_m else len(text) - start)
            sec_text = (title + "\n" + text[start:end]).strip()
            if len(sec_text) > 20:
                sections.append((sec_num, sec_text))

    if not sections and text.strip():
        sections.append(("1", text[:100000]))

    return sections


def fetch_and_store_india(source: dict) -> tuple[int, int]:
    """
    Fetch one India law (PDF) and store in database.

    Returns:
        (clauses_inserted, 0) on success, (0, 1) on failure.
    """
    reg_id = source["regulation_id"]
    url = source["source_url"]

    if regulation_exists(reg_id):
        logger.info("Skipping %s (already exists)", reg_id)
        return 0, 0

    logger.info("Fetching %s from %s", source["law_name"], url)
    urls_to_try = [url] + source.get("fallback_urls", [])
    pdf_bytes = None
    for u in urls_to_try:
        pdf_bytes = fetch_pdf(u)
        if pdf_bytes:
            break
        if u != urls_to_try[-1]:
            time.sleep(1)
    if not pdf_bytes:
        logger.error("Could not download PDF for %s", reg_id)
        return 0, 1

    text = extract_text_from_pdf(pdf_bytes)
    if not text or len(text) < 100:
        logger.error("Could not extract text from PDF for %s", reg_id)
        return 0, 1

    sections = extract_sections_from_text(text)
    raw_text = "\n\n".join(
        f"Section {n}\n{t}" for n, t in sections
    )[:100000]

    insert_regulation({
        "regulation_id": reg_id,
        "country": source["country"],
        "law_name": source["law_name"],
        "law_category": source["law_category"],
        "law_type": source["law_type"],
        "year": source["year"],
        "source_url": url,
        "raw_text": raw_text,
    })

    clauses = extract_clauses_from_articles(sections, reg_id)
    for i in range(0, len(clauses), CLAUSE_BATCH_SIZE):
        batch = clauses[i : i + CLAUSE_BATCH_SIZE]
        insert_clauses_batch(batch)

    logger.info("Stored %s: %d clauses", reg_id, len(clauses))
    return len(clauses), 0


def run_fetch_india() -> tuple[int, int, int]:
    """
    Fetch all India laws. Skip on failure, continue with next.

    Returns:
        (regulations_fetched, clauses_inserted, failed_count)
    """
    total_regs = 0
    total_clauses = 0
    failed = 0
    for i, source in enumerate(INDIA_LAWS):
        if i > 0:
            time.sleep(2)  # Avoid rate limiting from legislative.gov.in
        try:
            clauses, fail = fetch_and_store_india(source)
            if fail:
                failed += 1
            else:
                total_regs += 1
                total_clauses += clauses
        except Exception as e:
            logger.exception(
                "Failed to fetch %s: %s", source["regulation_id"], e
            )
            failed += 1
    return total_regs, total_clauses, failed
