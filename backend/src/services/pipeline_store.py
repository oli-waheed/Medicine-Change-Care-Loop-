"""SQLite persistence for captures, review cases and case status events."""

import json
import threading
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, select, text, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..domain.case_status_event import OPEN_STATUSES, CaseStatusEvent
from ..domain.review_case import ReviewCase
from ..models import (
    Base,
    CaseStatusEventRow,
    ChangeProcessingOutcomeRow,
    DailyUpdateRunRow,
    ReviewCaseRow,
    ShortageCaptureRow,
    ShortageRetrievalRow,
    SourceReleaseCaptureRow,
    SourceReleaseRetrievalRow,
)
from ..schemas.change_processing_outcomes import change_processing_outcome_payload
from ..schemas.open_review_cases import open_review_case_payload
from .change_processing_outcomes import ChangeProcessingOutcome
from .ingest_source_release import IngestionOutcome, ProcessingStatus, source_order_key


def _as_utc(value: datetime) -> datetime:
    # SQLite does not keep offsets: every time is written as UTC and read back naive.
    # A naive value is therefore UTC, never the machine's local time zone.
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


# Columns added to existing tables after their first release. ``create_all`` only
# creates missing tables, so an existing database gets these columns here (they
# are all nullable, so existing rows stay valid).
_ADDED_COLUMNS = {
    "case_status_events": {"reviewer_initials": "VARCHAR(10)", "note": "TEXT"},  # feature 007
}


def _add_missing_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, columns in _ADDED_COLUMNS.items():
            present = {column["name"] for column in inspector.get_columns(table)}
            for name, column_type in columns.items():
                if name not in present:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {column_type}"))


class CaseTransitionError(Exception):
    """A requested status change is not allowed or the case has changed meanwhile."""

    def __init__(self, code: str, message: str, current_status: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.current_status = current_status


class PipelineStore:
    """Small repository; the schema is created lazily on first use."""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._engine: Engine | None = None
        self._sessions: sessionmaker[Session] | None = None
        # Capture manifests are immutable, so their file lists are cached by release id.
        self._manifest_files: dict[str, tuple[tuple[str, Path], ...]] = {}
        # The first requests to a new database can arrive together (a page loads
        # several APIs at once); only one of them may create the schema.
        self._init_lock = threading.Lock()

    def _session(self) -> Session:
        if self._sessions is None:
            with self._init_lock:
                if self._sessions is None:
                    self._open()
        return self._sessions()

    def _open(self) -> None:
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
        _add_missing_columns(engine)
        self._engine = engine
        self._sessions = sessionmaker(engine, expire_on_commit=False)

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

    # --- raw capture files -------------------------------------------------------

    def _capture_files(self, row: SourceReleaseCaptureRow) -> tuple[tuple[str, Path], ...]:
        """``(checksum, raw file path)`` for every file listed in a capture's manifest."""
        cached = self._manifest_files.get(row.release_id)
        if cached is not None:
            return cached
        directory = Path(row.capture_directory)
        try:
            manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return ()  # Not cached: the capture may be restored later.
        files = tuple(
            (entry["checksum"], directory / entry["contentReference"])
            for entry in manifest.get("files", ())
        )
        self._manifest_files[row.release_id] = files
        return files

    def capture_with_identical_content(
        self, source_name: str, checksums: set[str]
    ) -> SourceReleaseCaptureRow | None:
        """The earliest capture of the same source whose raw files have exactly these checksums."""
        for row in self.captures():
            if row.source_name != source_name:
                continue
            if {checksum for checksum, _ in self._capture_files(row)} == checksums:
                return row
        return None

    def record_retrieval(
        self, row: SourceReleaseCaptureRow, retrieved_at: datetime, reference: dict
    ) -> bool:
        """Record a later download of already-captured content; returns True if new."""
        retrieved_at = _as_utc(retrieved_at)
        if _as_utc(row.retrieved_at) == retrieved_at:
            return False  # The capture itself already records this retrieval.
        with self._session() as session, session.begin():
            exists = session.scalar(
                select(SourceReleaseRetrievalRow.id).where(
                    SourceReleaseRetrievalRow.release_id == row.release_id,
                    SourceReleaseRetrievalRow.retrieved_at == retrieved_at,
                )
            )
            if exists is not None:
                return False
            session.add(
                SourceReleaseRetrievalRow(
                    release_id=row.release_id,
                    retrieved_at=retrieved_at,
                    source_release_reference=reference,
                )
            )
            return True

    def retrievals(self, release_id: str) -> list[SourceReleaseRetrievalRow]:
        with self._session() as session:
            return list(
                session.scalars(
                    select(SourceReleaseRetrievalRow)
                    .where(SourceReleaseRetrievalRow.release_id == release_id)
                    .order_by(SourceReleaseRetrievalRow.retrieved_at)
                )
            )

    def available_file_checksums(self) -> set[str]:
        """Checksums of raw files that are still present in the capture store.

        Includes stored shortage files (feature 007), whose cases cite them.
        """
        with self._session() as session:
            shortage_files = session.scalars(select(ShortageCaptureRow)).all()
        return {
            checksum
            for row in self.captures()
            for checksum, path in self._capture_files(row)
            if path.is_file()
        } | {
            row.checksum.removeprefix("sha256-")
            for row in shortage_files
            if Path(row.file_path).is_file()
        }

    # --- read side ---------------------------------------------------------------

    def open_case_payloads(self) -> list[dict]:
        """Cases still to be reviewed (NEW and IN_PROGRESS), oldest first."""
        return self.case_payloads(include_reviewed=False)

    def case_payloads(self, *, include_reviewed: bool) -> list[dict]:
        """Stored case views with their current status and full status history."""
        with self._session() as session:
            query = select(ReviewCaseRow).order_by(ReviewCaseRow.created_at, ReviewCaseRow.case_id)
            if not include_reviewed:
                query = query.where(
                    ReviewCaseRow.status.in_(sorted(status.value for status in OPEN_STATUSES))
                )
            rows = session.scalars(query).all()
            events = self._events_by_case(session, [row.case_id for row in rows])
            return [
                {
                    **row.evidence_payload,
                    "status": row.status,
                    "statusHistory": events.get(row.case_id, []),
                }
                for row in rows
            ]

    def case_payload(self, case_id: str) -> dict | None:
        with self._session() as session:
            row = session.get(ReviewCaseRow, case_id)
            if row is None:
                return None
            events = self._events_by_case(session, [case_id])
            return {**row.evidence_payload, "status": row.status, "statusHistory": events[case_id]}

    @staticmethod
    def _events_by_case(session: Session, case_ids: list[str]) -> dict[str, list[dict]]:
        result: dict[str, list[dict]] = {case_id: [] for case_id in case_ids}
        if not case_ids:
            return result
        rows = session.scalars(
            select(CaseStatusEventRow)
            .where(CaseStatusEventRow.case_id.in_(case_ids))
            .order_by(CaseStatusEventRow.occurred_at, CaseStatusEventRow.event_id)
        ).all()
        for row in rows:
            result[row.case_id].append(
                {
                    "eventId": row.event_id,
                    "fromStatus": row.from_status,
                    "toStatus": row.to_status,
                    "occurredAt": _as_utc(row.occurred_at).isoformat(),
                    "reviewerInitials": row.reviewer_initials,
                    "note": row.note,
                }
            )
        return result

    def record_status_event(self, event: CaseStatusEvent) -> None:
        """Apply a person's status change if the case still has ``event.from_status``.

        The check and the change are one statement in one transaction, so two
        reviewers can never overwrite each other (FR-004). Raises
        ``CaseTransitionError``: NOT_FOUND, or STALE_STATUS with the current status.
        """
        with self._session() as session, session.begin():
            changed = session.execute(
                update(ReviewCaseRow)
                .where(
                    ReviewCaseRow.case_id == event.case_id,
                    ReviewCaseRow.status == event.from_status.value,
                )
                .values(status=event.to_status.value)
            ).rowcount
            if changed != 1:
                current = session.scalar(
                    select(ReviewCaseRow.status).where(ReviewCaseRow.case_id == event.case_id)
                )
                if current is None:
                    raise CaseTransitionError("CASE_NOT_FOUND", "No case has this identifier.")
                raise CaseTransitionError(
                    "STALE_STATUS",
                    "The case's status has changed since it was loaded; reload and try again.",
                    current,
                )
            session.add(
                CaseStatusEventRow(
                    event_id=event.event_id,
                    case_id=event.case_id,
                    from_status=event.from_status.value,
                    to_status=event.to_status.value,
                    occurred_at=_as_utc(event.occurred_at),
                    reviewer_initials=event.reviewer_initials,
                    note=(event.note or "").strip() or None,
                )
            )

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

    # --- shortage captures (feature 006) -------------------------------------------

    def shortage_capture_by_checksum(self, checksum: str) -> ShortageCaptureRow | None:
        with self._session() as session:
            return session.scalars(
                select(ShortageCaptureRow).where(ShortageCaptureRow.checksum == checksum)
            ).first()

    def record_shortage_capture(self, row: ShortageCaptureRow) -> ShortageCaptureRow:
        """Store a new capture and its first retrieval in one transaction."""
        with self._session() as session, session.begin():
            session.add(row)
            session.flush()
            session.add(
                ShortageRetrievalRow(
                    capture_sequence=row.sequence, retrieved_at=_as_utc(row.first_retrieved_at)
                )
            )
        return row

    def record_shortage_retrieval(
        self, capture: ShortageCaptureRow, retrieved_at: datetime
    ) -> ShortageCaptureRow:
        """Record another download of content that is already captured."""
        with self._session() as session, session.begin():
            row = session.get(ShortageCaptureRow, capture.sequence)
            row.last_retrieved_at = _as_utc(retrieved_at)
            session.add(
                ShortageRetrievalRow(
                    capture_sequence=capture.sequence, retrieved_at=_as_utc(retrieved_at)
                )
            )
        return row

    def active_shortage_capture(self) -> ShortageCaptureRow | None:
        """The validated capture retrieved most recently: what Fimea publishes now."""
        with self._session() as session:
            return session.scalars(
                select(ShortageCaptureRow)
                .where(ShortageCaptureRow.processing_status == "VALIDATED")
                .order_by(
                    ShortageCaptureRow.last_retrieved_at.desc(),
                    ShortageCaptureRow.sequence.desc(),
                )
                .limit(1)
            ).first()

    def shortage_retrieval_count(self, capture_sequence: int) -> int:
        with self._session() as session:
            return len(
                session.scalars(
                    select(ShortageRetrievalRow.id).where(
                        ShortageRetrievalRow.capture_sequence == capture_sequence
                    )
                ).all()
            )

    # --- daily automatic update runs (feature 006) -----------------------------------

    def daily_update_run_on(self, run_date: str) -> DailyUpdateRunRow | None:
        with self._session() as session:
            return session.scalars(
                select(DailyUpdateRunRow)
                .where(
                    DailyUpdateRunRow.run_date == run_date,
                    DailyUpdateRunRow.trigger == "SCHEDULE",
                )
                .limit(1)
            ).first()

    def start_daily_update_run(
        self, run_date: str, trigger: str, started_at: datetime
    ) -> DailyUpdateRunRow:
        row = DailyUpdateRunRow(run_date=run_date, trigger=trigger, started_at=_as_utc(started_at))
        with self._session() as session, session.begin():
            session.add(row)
        return row

    def finish_daily_update_run(
        self, run: DailyUpdateRunRow, finished_at: datetime, outcome: dict
    ) -> DailyUpdateRunRow:
        with self._session() as session, session.begin():
            row = session.get(DailyUpdateRunRow, run.id)
            row.finished_at = _as_utc(finished_at)
            row.outcome = outcome
        return row

    def latest_daily_update_run(self) -> DailyUpdateRunRow | None:
        with self._session() as session:
            return session.scalars(
                select(DailyUpdateRunRow)
                .order_by(DailyUpdateRunRow.started_at.desc(), DailyUpdateRunRow.id.desc())
                .limit(1)
            ).first()

    # --- shortage review cases (feature 007) ----------------------------------------

    def record_shortage_review(self, cases: list[dict], outcomes: list[dict]) -> int:
        """Store shortage cases (each with its NEW event) and outcomes in one transaction.

        A case or outcome that already exists is skipped, so processing the same
        pair of files again adds nothing. Returns the number of cases inserted.
        """
        inserted = 0
        with self._session() as session, session.begin():
            for case in cases:
                if session.scalar(
                    select(ReviewCaseRow.case_id).where(
                        ReviewCaseRow.idempotency_key == case["idempotency_key"]
                    )
                ):
                    continue
                session.add(
                    ReviewCaseRow(
                        case_id=case["case_id"],
                        idempotency_key=case["idempotency_key"],
                        status="NEW",
                        created_at=_as_utc(case["created_at"]),
                        medicine_key=case["medicine_key"],
                        record_id=case["record_id"],
                        change_set_id=case["change_set_id"],
                        change_kind=case["change_kind"],
                        prior_file_checksum=case["prior_file_checksum"],
                        current_file_checksum=case["current_file_checksum"],
                        evidence_payload=case["payload"],
                    )
                )
                session.flush()
                session.add(
                    CaseStatusEventRow(
                        event_id=case["event_id"],
                        case_id=case["case_id"],
                        from_status=None,
                        to_status="NEW",
                        occurred_at=_as_utc(case["created_at"]),
                    )
                )
                inserted += 1
            for outcome in outcomes:
                if session.get(ChangeProcessingOutcomeRow, outcome["outcomeId"]) is not None:
                    continue
                session.add(
                    ChangeProcessingOutcomeRow(
                        outcome_id=outcome["outcomeId"],
                        result=outcome["result"],
                        reason=outcome["reason"],
                        medicine_key=outcome["medicineIdentifier"],
                        change_kind=outcome["changeKind"],
                        record_ids=[r["recordId"] for r in outcome["simulatedRecords"]],
                        case_ids=outcome["caseIds"],
                        detected_at=_as_utc(datetime.fromisoformat(outcome["detectedAt"])),
                        evidence_payload=outcome,
                    )
                )
        return inserted
