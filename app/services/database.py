"""Supabase read/write for the application layer."""

import json
import logging
from typing import Any, Optional

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from app.config import SUPABASE_DB_URL

logger = logging.getLogger(__name__)


def get_connection():
    if not SUPABASE_DB_URL:
        raise ValueError("SUPABASE_DB_URL not set")
    return psycopg2.connect(SUPABASE_DB_URL)


def ensure_app_tables() -> None:
    """Create analysis_reports if missing."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analysis_reports (
                    id SERIAL PRIMARY KEY,
                    input_text TEXT NOT NULL,
                    coverage_result JSONB,
                    conflicts_result JSONB,
                    recommendations JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()
    finally:
        conn.close()


def list_regulations() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT regulation_id, country, law_name, law_category, law_type,
                       year, source_url, fetched_at
                FROM regulations
                ORDER BY country, law_name
            """)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_clauses_for_regulation(regulation_id: str) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT clause_id, regulation_id, article_number, clause_text, char_count
                FROM clauses
                WHERE regulation_id = %s
                ORDER BY article_number, clause_id
            """, (regulation_id,))
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def fetch_all_clauses_for_index(limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Return clause rows for FAISS (clause_id, regulation_id, clause_text)."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            q = """
                SELECT c.clause_id, c.regulation_id, c.article_number, c.clause_text,
                       r.country, r.law_name
                FROM clauses c
                JOIN regulations r ON r.regulation_id = c.regulation_id
            """
            if limit:
                cur.execute(q + " LIMIT %s", (limit,))
            else:
                cur.execute(q)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def insert_analysis_report(
    input_text: str,
    coverage: dict,
    conflicts: dict,
    recommendations: dict,
) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO analysis_reports (input_text, coverage_result, conflicts_result, recommendations)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                input_text[:50000],
                Json(coverage),
                Json(conflicts),
                Json(recommendations),
            ))
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else 0
    finally:
        conn.close()


def get_report(report_id: int) -> Optional[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM analysis_reports WHERE id = %s",
                (report_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            for k in ("coverage_result", "conflicts_result", "recommendations"):
                if d.get(k) and isinstance(d[k], str):
                    d[k] = json.loads(d[k])
            return d
    finally:
        conn.close()


def list_recent_reports(limit: int = 20) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, input_text, created_at
                FROM analysis_reports
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
