"""Pydantic API schemas."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """POST /analyze body."""

    text: str = Field(..., min_length=10, max_length=100_000, description="Draft policy text")


class AnalyzeResponse(BaseModel):
    """Full analysis report."""

    report_id: Optional[int] = None
    clause_count: int
    coverage: dict[str, Any]
    conflicts: dict[str, Any]
    recommendations: dict[str, Any]
    classified_clauses_sample: list[dict[str, Any]] = Field(default_factory=list)


class RegulationOut(BaseModel):
    regulation_id: str
    country: Optional[str]
    law_name: Optional[str]
    law_category: Optional[str]
    law_type: Optional[str]
    year: Optional[int]


class ClauseOut(BaseModel):
    clause_id: str
    regulation_id: str
    article_number: Optional[str]
    char_count: Optional[int]


class ReportOut(BaseModel):
    id: int
    input_text: str
    coverage_result: Optional[dict[str, Any]]
    conflicts_result: Optional[dict[str, Any]]
    recommendations: Optional[dict[str, Any]]
    created_at: Optional[str]
