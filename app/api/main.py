"""
Global AI Governance Copilot — FastAPI service.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent.pipeline import run_pipeline
from app.schemas import AnalyzeRequest, AnalyzeResponse, ClauseOut, RegulationOut, ReportOut
from app.services.database import (
    ensure_app_tables,
    get_clauses_for_regulation,
    get_report,
    list_recent_reports,
    list_regulations,
)
from app.services.faiss_index import build_or_load_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ensure_app_tables()
        build_or_load_index()
        logger.info("API ready: tables ensured, FAISS loaded or built")
    except Exception as e:
        logger.warning("Startup warning: %s", e)
    yield


app = FastAPI(
    title="Global AI Governance Copilot",
    description="Analyze draft AI policy text against EU and India legal corpora.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(body: AnalyzeRequest) -> dict[str, Any]:
    """Run full agent pipeline on draft text."""
    import re as _re
    cleaned = _re.sub(r"[\s\W]+", "", body.text)
    if len(cleaned) < 5:
        raise HTTPException(status_code=422, detail="Input contains no substantive text.")
    try:
        result = run_pipeline(body.text, persist=True)
    except Exception as e:
        logger.exception("Analyze failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {
        "report_id": result.get("report_id"),
        "clause_count": result.get("clause_count", 0),
        "coverage": result["coverage"],
        "conflicts": result["conflicts"],
        "recommendations": result["recommendations"],
        "classified_clauses_sample": result.get("classified_clauses", []),
    }


@app.get("/regulations", response_model=list[RegulationOut])
def regulations() -> list[dict]:
    """List all regulations."""
    return list_regulations()


@app.get("/clauses/{regulation_id}", response_model=list[ClauseOut])
def clauses(regulation_id: str) -> list[dict]:
    """List clauses for a regulation."""
    rows = get_clauses_for_regulation(regulation_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Regulation not found or no clauses")
    return [
        {
            "clause_id": r["clause_id"],
            "regulation_id": r["regulation_id"],
            "article_number": r.get("article_number"),
            "char_count": r.get("char_count"),
        }
        for r in rows
    ]


@app.get("/conflicts")
def conflicts() -> dict[str, Any]:
    """Recent conflict summaries from stored reports."""
    reports = list_recent_reports(10)
    items = []
    for r in reports:
        rep = get_report(r["id"])
        if rep and rep.get("conflicts_result"):
            items.append({
                "report_id": r["id"],
                "created_at": str(rep.get("created_at")),
                "conflicts": rep["conflicts_result"],
            })
    return {"recent": items}


@app.get("/reports/{report_id}", response_model=ReportOut)
def report(report_id: int) -> dict:
    """Fetch saved analysis report."""
    row = get_report(report_id)
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": row["id"],
        "input_text": row["input_text"][:50000],
        "coverage_result": row.get("coverage_result"),
        "conflicts_result": row.get("conflicts_result"),
        "recommendations": row.get("recommendations"),
        "created_at": str(row.get("created_at")),
    }


@app.get("/health")
def health() -> dict[str, Any]:
    """Report API, DB, and FAISS status."""
    status: dict[str, Any] = {"api": "ok"}
    # DB check
    try:
        from app.services.database import get_connection
        conn = get_connection()
        conn.close()
        status["database"] = "ok"
    except Exception as e:
        status["database"] = f"error: {e}"
    # FAISS check
    try:
        from app.services.faiss_index import _index
        status["faiss_vectors"] = _index.ntotal if _index else 0
    except Exception:
        status["faiss_vectors"] = 0
    return status
