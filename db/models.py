"""
SQLAlchemy ORM models for the AI Governance Copilot.

Schema: regulations, clauses, conflicts, analysis_reports
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class RiskType(str, PyEnum):
    """Risk type classification for clauses."""

    MISINFO = "misinfo"
    CYBER = "cyber"
    SURVEILLANCE = "surveillance"
    SAFETY = "safety"
    BIAS = "bias"
    REPORTING = "reporting"


class ActorType(str, PyEnum):
    """Actor type classification for clauses."""

    MODEL_PROVIDER = "model_provider"
    APP_DEPLOYER = "app_deployer"
    PLATFORM = "platform"
    INFRA_OPERATOR = "infra_operator"


class ObligationType(str, PyEnum):
    """Obligation type classification for clauses."""

    TESTING = "testing"
    REPORTING = "reporting"
    TRANSPARENCY = "transparency"
    LOGGING = "logging"
    ASSESSMENT = "assessment"


class ConflictSeverity(str, PyEnum):
    """Severity level for detected conflicts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Regulation(Base):
    """Regulation/law document from a jurisdiction."""

    __tablename__ = "regulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    law_name: Mapped[str] = mapped_column(String(255), nullable=False)
    law_type: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    full_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    clauses: Mapped[list["Clause"]] = relationship(
        "Clause", back_populates="regulation", cascade="all, delete-orphan"
    )


class Clause(Base):
    """Individual clause extracted from a regulation."""

    __tablename__ = "clauses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    regulation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regulations.id", ondelete="CASCADE"), nullable=False
    )
    article_number: Mapped[str] = mapped_column(String(50), nullable=False)
    clause_text: Mapped[str] = mapped_column(Text, nullable=False)
    risk_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # ENUM stored as string
    actor_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    obligation_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_annotated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    regulation: Mapped["Regulation"] = relationship(
        "Regulation", back_populates="clauses"
    )
    conflicts_as_clause_1: Mapped[list["Conflict"]] = relationship(
        "Conflict",
        foreign_keys="Conflict.clause_id_1",
        back_populates="clause_1",
    )
    conflicts_as_clause_2: Mapped[list["Conflict"]] = relationship(
        "Conflict",
        foreign_keys="Conflict.clause_id_2",
        back_populates="clause_2",
    )


class Conflict(Base):
    """Detected conflict between two clauses from different jurisdictions."""

    __tablename__ = "conflicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clause_id_1: Mapped[int] = mapped_column(
        Integer, ForeignKey("clauses.id", ondelete="CASCADE"), nullable=False
    )
    clause_id_2: Mapped[int] = mapped_column(
        Integer, ForeignKey("clauses.id", ondelete="CASCADE"), nullable=False
    )
    conflict_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # low/medium/high
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    clause_1: Mapped["Clause"] = relationship(
        "Clause", foreign_keys=[clause_id_1], back_populates="conflicts_as_clause_1"
    )
    clause_2: Mapped["Clause"] = relationship(
        "Clause", foreign_keys=[clause_id_2], back_populates="conflicts_as_clause_2"
    )


class AnalysisReport(Base):
    """Stored analysis report from pipeline runs."""

    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    coverage_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    conflicts_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
