"""
Fetch EU laws from EUR-Lex.

Uses requests + BeautifulSoup to extract article text from HTML.
Falls back to PyMuPDF (fitz) if HTML unavailable.
Tags each regulation with law_category from config.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import EU_LAWS, PDF_DOWNLOAD_TIMEOUT, REQUEST_HEADERS, REQUEST_TIMEOUT
from db_client import insert_clauses_batch, insert_regulation, regulation_exists
from ingest.extract_clauses import extract_clauses_from_articles
from config import CLAUSE_BATCH_SIZE

logger = logging.getLogger(__name__)


def fetch_html(url: str) -> Optional[str]:
    """
    Fetch HTML content from EUR-Lex URL.

    Converts TXT url to TXT/HTML/ for full legal text.
    Returns:
        HTML string or None if request fails.
    """
    # Force HTML format for full text content
    html_url = url.replace("/TXT/?uri=", "/TXT/HTML/?uri=")
    try:
        response = requests.get(
            html_url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 404:
            logger.warning("404 for %s", html_url)
            return None
        response.raise_for_status()
        logger.debug("Fetched %d chars from %s", len(response.text), html_url)
        return response.text
    except requests.RequestException as e:
        logger.error("Request failed for %s: %s", html_url, e)
        return None


def extract_articles_from_html(html: str) -> list[tuple[str, str]]:
    """
    Extract article number and text from EUR-Lex HTML.

    Returns:
        List of (article_number, article_text) tuples.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove nav, header, footer, scripts, styles - keep only legal content
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    # Try EUR-Lex specific content containers first
    content = (
        soup.find("div", class_="eli-main-title")
        or soup.find("div", id="docHtml")
        or soup.find("div", class_="tabContent")
        or soup.find("main")
        or soup.find("article")
        or soup.find("body")
        or soup
    )

    text = content.get_text(separator="\n", strip=True)
    logger.debug("Extracted %d chars of raw text", len(text))

    # Split by "Article X" boundaries
    pattern = re.compile(
        r"(?:^|\n)\s*Article\s+(\d+[a-z]?(?:\s*[-–]\s*[^\n]+)?)\s*\n",
        re.IGNORECASE | re.MULTILINE,
    )
    parts = pattern.split(text)

    articles: list[tuple[str, str]] = []
    if len(parts) > 1:
        for i in range(1, len(parts) - 1, 2):
            if i + 1 < len(parts):
                art_num = parts[i].strip()
                art_text = parts[i + 1].strip()
                if art_num and art_text and len(art_text) > 20:
                    articles.append((art_num, art_text))
        logger.debug("Found %d articles via Article X pattern", len(articles))

    # Fallback: try recital/paragraph splitting if no articles found
    if not articles and text and len(text) > 200:
        # Split into chunks of ~2000 chars to ensure we get clauses
        chunks = [text[i:i+2000] for i in range(0, min(len(text), 100000), 2000)]
        for idx, chunk in enumerate(chunks, 1):
            if len(chunk.strip()) > 50:
                articles.append((str(idx), chunk.strip()))
        logger.debug("Fallback: split into %d chunks", len(articles))

    return articles


def try_fetch_pdf(url: str) -> Optional[str]:
    """
    Try to fetch PDF from EUR-Lex and extract text via PyMuPDF.

    EUR-Lex often has PDF links. Returns extracted text or None.
    """
    try:
        import fitz
        response = requests.get(
            url.replace("/TXT/", "/PDF/").replace("?uri=", "/"),
            headers=REQUEST_HEADERS,
            timeout=PDF_DOWNLOAD_TIMEOUT,
            stream=True,
        )
        if response.status_code != 200:
            return None
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
            path = f.name
        try:
            doc = fitz.open(path)
            text_parts = [p.get_text() for p in doc]
            doc.close()
            return "\n".join(text_parts)
        finally:
            Path(path).unlink(missing_ok=True)
    except Exception as e:
        logger.debug("PDF fallback failed: %s", e)
        return None


def fetch_and_store_eu(source: dict) -> tuple[int, int]:
    """
    Fetch one EU law and store in database.

    Returns:
        (clauses_inserted, 0) on success, (0, 1) on failure.
    """
    reg_id = source["regulation_id"]
    url = source["source_url"]

    if regulation_exists(reg_id):
        logger.info("Skipping %s (already exists)", reg_id)
        return 0, 0

    logger.info("Fetching %s from %s", source["law_name"], url)
    html = fetch_html(url)
    raw_text = ""
    articles: list[tuple[str, str]] = []

    if html:
        articles = extract_articles_from_html(html)
        if articles:
            raw_text = "\n\n".join(
                f"Article {n}\n{t}" for n, t in articles
            )[:100000]
        else:
            raw_text = BeautifulSoup(html, "lxml").get_text(
                separator="\n", strip=True
            )[:100000]

    if not raw_text:
        raw_text = try_fetch_pdf(url)
    if not raw_text or len(raw_text) < 100:
        logger.error("Could not extract text for %s", reg_id)
        return 0, 1

    # Re-extract articles from raw_text for clause splitting
    if not articles:
        pattern = re.compile(
            r"\n\s*Article\s+(\d+[a-z]?(?:\([a-z]\))?(?:\s*[-–][^\n]+)?)\s*\n",
            re.IGNORECASE,
        )
        parts = pattern.split(raw_text)
        articles = []
        if len(parts) > 1:
            for i in range(1, len(parts) - 1, 2):
                if i + 1 < len(parts):
                    art_num = parts[i].strip()
                    art_text = parts[i + 1].strip()
                    if art_num and art_text and len(art_text) > 20:
                        articles.append((art_num, art_text))
        if not articles:
            articles = [("1", raw_text)]

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

    clauses = extract_clauses_from_articles(articles, reg_id)
    for i in range(0, len(clauses), CLAUSE_BATCH_SIZE):
        batch = clauses[i : i + CLAUSE_BATCH_SIZE]
        insert_clauses_batch(batch)

    logger.info("Stored %s: %d clauses", reg_id, len(clauses))
    return len(clauses), 0


def run_fetch_eu() -> tuple[int, int, int]:
    """
    Fetch all EU laws. Skip on failure, continue with next.

    Returns:
        (regulations_fetched, clauses_inserted, failed_count)
    """
    total_regs = 0
    total_clauses = 0
    failed = 0
    for source in EU_LAWS:
        try:
            clauses, fail = fetch_and_store_eu(source)
            if fail:
                failed += 1
            else:
                total_regs += 1
                total_clauses += clauses
        except Exception as e:
            logger.exception("Failed to fetch %s: %s", source["regulation_id"], e)
            failed += 1
    return total_regs, total_clauses, failed
