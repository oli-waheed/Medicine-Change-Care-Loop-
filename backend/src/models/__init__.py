"""SQLAlchemy ORM mappings (SQLite-portable types only)."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
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
    change_set_id: Mapped[str] = mapped_column(String(80))
    change_kind: Mapped[str] = mapped_column(String(30))
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
    # Feature 007: who recorded a human status change, and why.
    reviewer_initials: Mapped[str | None] = mapped_column(String(10))
    note: Mapped[str | None] = mapped_column(Text)


class ChangeProcessingOutcomeRow(Base):
    """The matching outcome of one package change set (MATCHED, NO_MATCH, AMBIGUOUS)."""

    __tablename__ = "change_processing_outcomes"

    outcome_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    result: Mapped[str] = mapped_column(String(20), index=True)
    reason: Mapped[str] = mapped_column(String(40))
    medicine_key: Mapped[str] = mapped_column(String(200), index=True)
    change_kind: Mapped[str] = mapped_column(String(30))
    record_ids: Mapped[list[str]] = mapped_column(JSON)
    case_ids: Mapped[list[str]] = mapped_column(JSON)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    evidence_payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class SourceReleaseRetrievalRow(Base):
    """A later download of content that is already captured.

    The raw files are stored once; each further retrieval of identical content is
    recorded here instead of storing another full copy.
    """

    __tablename__ = "source_release_retrievals"
    __table_args__ = (UniqueConstraint("release_id", "retrieved_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    release_id: Mapped[str] = mapped_column(String(80), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_release_reference: Mapped[dict[str, Any]] = mapped_column(JSON)


# --- Feature 006: medicine shortages --------------------------------------------------


class ShortageCaptureRow(Base):
    """One immutable download of Fimea's shortage file (Shortages.txt), stored once by content."""

    __tablename__ = "shortage_captures"

    sequence: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    checksum: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    processing_status: Mapped[str] = mapped_column(String(20))
    source_url: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(Text)
    size_bytes: Mapped[int] = mapped_column(Integer)
    record_count: Mapped[int | None] = mapped_column(Integer)
    first_retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    failure_detail: Mapped[str | None] = mapped_column(Text)


class ShortageRetrievalRow(Base):
    """Every download of the shortage file, including unchanged ones."""

    __tablename__ = "shortage_retrievals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    capture_sequence: Mapped[int] = mapped_column(
        ForeignKey("shortage_captures.sequence"), index=True
    )
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DailyUpdateRunRow(Base):
    """One run of the backend's daily automatic update (feature 006)."""

    __tablename__ = "daily_update_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_date: Mapped[str] = mapped_column(String(10), index=True)
    trigger: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class ReleaseQualityCheckRow(Base):
    """Automatic data-quality checks of one compared release pair (feature 010)."""

    __tablename__ = "release_quality_checks"

    check_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    prior_release_id: Mapped[str] = mapped_column(String(80), index=True)
    current_release_id: Mapped[str] = mapped_column(String(80), index=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
