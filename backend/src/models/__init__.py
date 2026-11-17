"""SQLAlchemy ORM mappings (SQLite-portable types only)."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SourceReleaseCaptureRow(Base):
    """One immutable raw-release capture and its validation outcome."""

    __tablename__ = "source_release_captures"

    sequence: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    release_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    processing_status: Mapped[str] = mapped_column(String(20))
    source_name: Mapped[str] = mapped_column(String(200))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capture_directory: Mapped[str] = mapped_column(Text)
    # Backend-derived chronology (from Ajopvm), never caller-declared.
    source_order_value: Mapped[str | None] = mapped_column(String(40))
    source_order_evidence_class: Mapped[str] = mapped_column(String(20))
    source_order_key: Mapped[int | None] = mapped_column(Integer, index=True)
    failure_detail: Mapped[str | None] = mapped_column(Text)


class ReviewCaseRow(Base):
    """A review case; the evidence view is stored exactly as it was created."""

    __tablename__ = "review_cases"

    case_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(80), unique=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    medicine_key: Mapped[str] = mapped_column(String(200), index=True)
    record_id: Mapped[str] = mapped_column(String(200))
    change_id: Mapped[str] = mapped_column(String(80))
    prior_file_checksum: Mapped[str | None] = mapped_column(String(80))
    current_file_checksum: Mapped[str | None] = mapped_column(String(80))
    evidence_payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class CaseStatusEventRow(Base):
    """Recorded case status transitions, starting with creation in NEW."""

    __tablename__ = "case_status_events"

    event_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("review_cases.case_id"), index=True)
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
