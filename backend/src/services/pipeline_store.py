"""SQLite persistence for captures, review cases and case status events."""

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..domain.review_case import ReviewCase
from ..models import (
    Base,
    CaseStatusEventRow,
    ChangeProcessingOutcomeRow,
    ReviewCaseRow,
    SourceReleaseCaptureRow,
)
from ..schemas.change_processing_outcomes import change_processing_outcome_payload
from ..schemas.open_review_cases import open_review_case_payload
from .change_processing_outcomes import ChangeProcessingOutcome
from .ingest_source_release import IngestionOutcome, ProcessingStatus, source_order_key


def _as_utc(value: datetime) -> datetime:
    # SQLite does not keep offsets; values are stored and returned as UTC.
    return value.astimezone(UTC)


class PipelineStore:
    """Small repository; the schema is created lazily on first use."""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._engine: Engine | None = None
        self._sessions: sessionmaker[Session] | None = None

    def _session(self) -> Session:
        if self._sessions is None:
            if self.database_url.startswith("sqlite:///"):
                database_path = self.database_url.removeprefix("sqlite:///")
                if database_path and database_path != ":memory:":
                    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
            engine = create_engine(
                self.database_url,
                connect_args=(
                    {"check_same_thread": False} if self.database_url.startswith("sqlite") else {}
                ),
            )
            if self.database_url.startswith("sqlite"):

                @event.listens_for(engine, "connect")
                def _enable_foreign_keys(connection, _record):
                    connection.execute("PRAGMA foreign_keys=ON")

            Base.metadata.create_all(engine)
            self._engine = engine
            self._sessions = sessionmaker(engine, expire_on_commit=False)
        return self._sessions()

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()

    # --- source release captures -------------------------------------------------

    def is_known_release(self, release_id: str) -> bool:
        with self._session() as session:
            return (
                session.scalar(
                    select(SourceReleaseCaptureRow.sequence).where(
                        SourceReleaseCaptureRow.release_id == release_id
                    )
                )
                is not None
            )

    def comparison_baseline(self) -> SourceReleaseCaptureRow | None:
        """Latest validated capture with verified chronology.

        Among captures with the same Ajopvm, the first one captured stays the baseline,
        so an equal-dated reissue never silently replaces it.
        """
        with self._session() as session:
            return session.scalars(
                select(SourceReleaseCaptureRow)
                .where(
                    SourceReleaseCaptureRow.processing_status == ProcessingStatus.VALIDATED.value,
                    SourceReleaseCaptureRow.source_order_key.is_not(None),
                )
                .order_by(
                    SourceReleaseCaptureRow.source_order_key.desc(),
                    SourceReleaseCaptureRow.sequence.asc(),
                )
                .limit(1)
            ).first()

    def record_ingestion(
        self,
        outcome: IngestionOutcome,
        cases: tuple[ReviewCase, ...] = (),
        processing_outcomes: tuple[ChangeProcessingOutcome, ...] = (),
    ) -> tuple[ReviewCase, ...]:
        """Record a capture, its new cases and its matching outcomes in one transaction.

        Returns the cases that were actually inserted; a case whose idempotency key
        already exists is skipped, so replays never duplicate cases. Outcomes are
        likewise inserted once per change set.
        """
        captured = outcome.captured_release
        if captured is None:
            raise ValueError("Only captured releases can be recorded.")
        with self._session() as session, session.begin():
            exists = session.scalar(
                select(SourceReleaseCaptureRow.sequence).where(
                    SourceReleaseCaptureRow.release_id == captured.release_id
                )
            )
            if exists is None:
                session.add(
                    SourceReleaseCaptureRow(
                        release_id=captured.release_id,
                        processing_status=outcome.processing_status.value,
                        source_name=captured.source_name,
                        retrieved_at=_as_utc(captured.retrieved_at),
                        capture_directory=str(captured.capture_directory),
                        source_order_value=outcome.source_order.value,
                        source_order_evidence_class=outcome.source_order.evidence_class.value,
                        source_order_key=source_order_key(outcome.source_order),
                        failure_detail=outcome.failure_detail,
                    )
                )
            inserted = self._insert_cases(session, cases)
            self._insert_outcomes(session, processing_outcomes)
            return inserted

    def add_cases(self, cases: tuple[ReviewCase, ...]) -> tuple[ReviewCase, ...]:
        with self._session() as session, session.begin():
            return self._insert_cases(session, cases)

    @staticmethod
    def _insert_cases(session: Session, cases: tuple[ReviewCase, ...]) -> tuple[ReviewCase, ...]:
        inserted = []
        for case in cases:
            duplicate = session.scalar(
                select(ReviewCaseRow.case_id).where(
                    ReviewCaseRow.idempotency_key == case.idempotency_key
                )
            )
            if duplicate is not None:
                continue
            change_set = case.change_set
            session.add(
                ReviewCaseRow(
                    case_id=case.case_id,
                    idempotency_key=case.idempotency_key,
                    status=case.status.value,
                    created_at=_as_utc(case.created_at),
                    medicine_key=change_set.medicine_key,
                    record_id=case.medication_record.record_id,
                    change_set_id=change_set.change_set_id,
                    change_kind=change_set.kind.value,
                    prior_file_checksum=(
                        change_set.prior_evidence.source_release.provenance.raw_file_checksum
                    ),
                    current_file_checksum=(
                        change_set.current_evidence.source_release.provenance.raw_file_checksum
                    ),
                    evidence_payload=open_review_case_payload(case),
                )
            )
            session.flush()
            event_ = case.initial_event
            session.add(
                CaseStatusEventRow(
                    event_id=event_.event_id,
                    case_id=case.case_id,
                    from_status=None if event_.from_status is None else event_.from_status.value,
                    to_status=event_.to_status.value,
                    occurred_at=_as_utc(event_.occurred_at),
                )
            )
            inserted.append(case)
        return tuple(inserted)

    def add_processing_outcomes(self, outcomes: tuple[ChangeProcessingOutcome, ...]) -> int:
        with self._session() as session, session.begin():
            return self._insert_outcomes(session, outcomes)

    @staticmethod
    def _insert_outcomes(session: Session, outcomes: tuple[ChangeProcessingOutcome, ...]) -> int:
        inserted = 0
        for outcome in outcomes:
            if session.get(ChangeProcessingOutcomeRow, outcome.outcome_id) is not None:
                continue
            session.add(
                ChangeProcessingOutcomeRow(
                    outcome_id=outcome.outcome_id,
                    result=outcome.result.value,
                    reason=outcome.reason.value,
                    medicine_key=outcome.change_set.medicine_key,
                    change_kind=outcome.change_set.kind.value,
                    record_ids=[
                        record.record_id for record in outcome.match.simulated_record_references
                    ],
                    case_ids=list(outcome.case_ids),
                    detected_at=_as_utc(outcome.change_set.detected_at),
                    evidence_payload=change_processing_outcome_payload(outcome),
                )
            )
            inserted += 1
        session.flush()
        return inserted

    # --- read side ---------------------------------------------------------------

    def open_case_payloads(self) -> list[dict]:
        with self._session() as session:
            rows = session.scalars(
                select(ReviewCaseRow)
                .where(ReviewCaseRow.status == "NEW")
                .order_by(ReviewCaseRow.created_at, ReviewCaseRow.case_id)
            ).all()
            return [row.evidence_payload for row in rows]

    def status_events(self, case_id: str) -> list[CaseStatusEventRow]:
        with self._session() as session:
            return list(
                session.scalars(
                    select(CaseStatusEventRow)
                    .where(CaseStatusEventRow.case_id == case_id)
                    .order_by(CaseStatusEventRow.occurred_at)
                )
            )

    def captures(self) -> list[SourceReleaseCaptureRow]:
        with self._session() as session:
            return list(
                session.scalars(
                    select(SourceReleaseCaptureRow).order_by(SourceReleaseCaptureRow.sequence)
                )
            )

    def processing_outcome_payloads(self, results: set[str] | None = None) -> list[dict]:
        """Stored matching outcomes, optionally only those with the given results."""
        with self._session() as session:
            query = select(ChangeProcessingOutcomeRow).order_by(
                ChangeProcessingOutcomeRow.detected_at,
                ChangeProcessingOutcomeRow.medicine_key,
                ChangeProcessingOutcomeRow.outcome_id,
            )
            if results:
                query = query.where(ChangeProcessingOutcomeRow.result.in_(sorted(results)))
            return [row.evidence_payload for row in session.scalars(query)]
