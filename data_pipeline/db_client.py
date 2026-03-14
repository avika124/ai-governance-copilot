"""
Supabase (PostgreSQL) connection and database operations.

Reads connection string from .env. Provides table creation, insert, and
existence checks for regulations and clauses.
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load .env from data_pipeline directory
load_dotenv(Path(__file__).resolve().parent / ".env")

logger = logging.getLogger(__name__)

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")


def get_connection():
    """
    Create a database connection using SUPABASE_DB_URL from .env.

    Returns:
        psycopg2 connection object.

    Raises:
        ValueError: If SUPABASE_DB_URL is not set.
    """
    if not SUPABASE_DB_URL:
        raise ValueError(
            "SUPABASE_DB_URL not set. Add it to .env: "
            "postgresql://postgres:[password]@[host]:5432/postgres"
        )
    return psycopg2.connect(SUPABASE_DB_URL)


def create_tables_if_not_exist() -> None:
    """
    Create regulations and clauses tables if they do not exist.

    Uses CREATE TABLE IF NOT EXISTS. Safe to run on every pipeline start.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS regulations (
                    regulation_id TEXT PRIMARY KEY,
                    country TEXT,
                    law_name TEXT,
                    law_category TEXT,
                    law_type TEXT,
                    year INT,
                    source_url TEXT,
                    raw_text TEXT,
                    fetched_at TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clauses (
                    clause_id TEXT PRIMARY KEY,
                    regulation_id TEXT REFERENCES regulations(regulation_id),
                    article_number TEXT,
                    clause_text TEXT,
                    char_count INT,
                    fetched_at TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()
        logger.info("Tables created or already exist")
    except Exception as e:
        conn.rollback()
        logger.error("Failed to create tables: %s", e)
        raise
    finally:
        conn.close()


def insert_regulation(row: dict[str, Any]) -> None:
    """
    Insert a single regulation row.

    Args:
        row: Dict with keys regulation_id, country, law_name, law_category,
             law_type, year, source_url, raw_text.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO regulations
                (regulation_id, country, law_name, law_category, law_type, year, source_url, raw_text)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (regulation_id) DO UPDATE SET
                    raw_text = EXCLUDED.raw_text,
                    fetched_at = NOW()
            """, (
                row["regulation_id"],
                row.get("country"),
                row.get("law_name"),
                row.get("law_category"),
                row.get("law_type"),
                row.get("year"),
                row.get("source_url"),
                row.get("raw_text"),
            ))
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error("Failed to insert regulation %s: %s", row.get("regulation_id"), e)
        raise
    finally:
        conn.close()


def insert_clauses_batch(rows: list[dict[str, Any]]) -> None:
    """
    Batch insert clause rows for performance.

    Args:
        rows: List of dicts with keys clause_id, regulation_id, article_number,
              clause_text, char_count.
    """
    if not rows:
        return

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO clauses (clause_id, regulation_id, article_number, clause_text, char_count)
                VALUES %s
                ON CONFLICT (clause_id) DO NOTHING
                """,
                [
                    (
                        r["clause_id"],
                        r["regulation_id"],
                        r.get("article_number"),
                        r.get("clause_text"),
                        r.get("char_count"),
                    )
                    for r in rows
                ],
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error("Failed to insert %d clauses: %s", len(rows), e)
        raise
    finally:
        conn.close()


def regulation_exists(regulation_id: str) -> bool:
    """
    Check if a regulation already exists in the database.

    Args:
        regulation_id: Primary key of the regulation.

    Returns:
        True if regulation exists, False otherwise.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM regulations WHERE regulation_id = %s",
                (regulation_id,),
            )
            return cur.fetchone() is not None
    finally:
        conn.close()


def clause_exists(clause_id: str) -> bool:
    """
    Check if a clause already exists in the database.

    Args:
        clause_id: Primary key of the clause.

    Returns:
        True if clause exists, False otherwise.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM clauses WHERE clause_id = %s",
                (clause_id,),
            )
            return cur.fetchone() is not None
    finally:
        conn.close()
