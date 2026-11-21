"""Feature 006: Fimea's open-data shortage file (Shortages.txt).

The file is a semicolon-separated, double-quoted text file with one header row:
NordicArticleNumber (the VNR), Valid, UnavailableFrom, EndingDate,
DateOfTheNotification, Updated and Company. Values are kept exactly as Fimea
publishes them; the file itself is stored once per content, with its checksum,
and every download is recorded.
"""

import csv
import hashlib
import io
import logging
import re
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO

from ..config import ApplicationConfig
from ..models import ShortageCaptureRow
from .latest_release_check import DownloadError, download_release
from .pipeline_store import PipelineStore

COLUMNS = (
    "NordicArticleNumber",
    "Valid",
    "UnavailableFrom",
    "EndingDate",
    "DateOfTheNotification",
    "Updated",
    "Company",
)
_DATE_COLUMNS = ("UnavailableFrom", "EndingDate", "DateOfTheNotification", "Updated")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ShortageRecord:
    """One row of the shortage file, values as published (empty string when empty)."""

    line: int
    vnr: str
    valid: str
    unavailable_from: str
    ending_date: str
    notification_date: str
    updated: str
    company: str


def parse_shortage_file(data: bytes) -> tuple[ShortageRecord, ...]:
    """Parse and validate the file. Raises ValueError with the line number on error."""

    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("The shortage file is not UTF-8 text.") from error
    rows = csv.reader(io.StringIO(text, newline=""), delimiter=";", quotechar='"', strict=True)
    try:
        header = next(rows)
    except StopIteration as error:
        raise ValueError("The shortage file is empty.") from error
    except csv.Error as error:
        raise ValueError(f"Line 1 is not valid: {error}.") from error
    if tuple(header) != COLUMNS:
        raise ValueError(
            "The shortage file does not have the expected columns "
            f"({';'.join(COLUMNS)}); found {';'.join(header)}."
        )
    records: list[ShortageRecord] = []
    seen: dict[str, int] = {}
    try:
        for row in rows:
            line = rows.line_num
            if not row:
                continue
            if len(row) != len(COLUMNS):
                raise ValueError(f"Line {line} has {len(row)} values, not {len(COLUMNS)}.")
            values = dict(zip(COLUMNS, row, strict=True))
            if not values["NordicArticleNumber"].strip():
                raise ValueError(f"Line {line} has no NordicArticleNumber (VNR).")
            for column in _DATE_COLUMNS:
                value = values[column]
                if value and not _DATE.fullmatch(value):
                    raise ValueError(f"Line {line}: {column} {value!r} is not a YYYY-MM-DD date.")
            vnr = values["NordicArticleNumber"]
            if vnr in seen:
                raise ValueError(f"Line {line} repeats VNR {vnr} from line {seen[vnr]}.")
            seen[vnr] = line
            records.append(
                ShortageRecord(
                    line=line,
                    vnr=vnr,
                    valid=values["Valid"],
                    unavailable_from=values["UnavailableFrom"],
                    ending_date=values["EndingDate"],
                    notification_date=values["DateOfTheNotification"],
                    updated=values["Updated"],
                    company=values["Company"],
                )
            )
    except csv.Error as error:
        raise ValueError(f"Line {rows.line_num} is not valid: {error}.") from error
    return tuple(records)


@dataclass(frozen=True, slots=True)
class ShortageFile:
    capture: ShortageCaptureRow
    records: tuple[ShortageRecord, ...]


class ShortageFileReader:
    """Reads the active capture, verifying its checksum; cached by checksum."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cached: ShortageFile | None = None

    def active(self, store: PipelineStore) -> ShortageFile | None:
        capture = store.active_shortage_capture()
        if capture is None:
            return None
        with self._lock:
            if self._cached is not None and self._cached.capture.checksum == capture.checksum:
                return ShortageFile(capture, self._cached.records)
            data = Path(capture.file_path).read_bytes()
            if f"sha256-{hashlib.sha256(data).hexdigest()}" != capture.checksum:
                raise ValueError("The stored shortage file does not match its checksum.")
            self._cached = ShortageFile(capture, parse_shortage_file(data))
            return self._cached


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def store_shortage_file(
    *,
    store: PipelineStore,
    config: ApplicationConfig,
    path: Path,
    source_url: str,
    retrieved_at: datetime,
) -> dict:
    """Capture a downloaded shortage file once per content and record the retrieval.

    Returns the outcome: ``processingStatus`` VALIDATED or FAILED, ``alreadyCaptured``,
    ``captureReference`` (``sha256-…``), ``recordCount`` and ``failureDetail``.
    """
    data = path.read_bytes()
    checksum = f"sha256-{hashlib.sha256(data).hexdigest()}"
    existing = store.shortage_capture_by_checksum(checksum)
    if existing is not None:
        store.record_shortage_retrieval(existing, retrieved_at)
        return {
            "processingStatus": existing.processing_status,
            "alreadyCaptured": True,
            "captureReference": checksum,
            "recordCount": existing.record_count,
            "failureDetail": existing.failure_detail,
        }

    try:
        records = parse_shortage_file(data)
        status, failure, count = "VALIDATED", None, len(records)
    except ValueError as error:
        status, failure, count = "FAILED", str(error), None

    directory = config.shortage_storage_dir
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{checksum.removeprefix('sha256-')}.txt"
    if not target.exists():
        temporary = target.with_suffix(".partial")
        temporary.write_bytes(data)
        temporary.replace(target)
    store.record_shortage_capture(
        ShortageCaptureRow(
            checksum=checksum,
            processing_status=status,
            source_url=source_url,
            file_path=str(target),
            size_bytes=len(data),
            record_count=count,
            first_retrieved_at=_utc(retrieved_at),
            last_retrieved_at=_utc(retrieved_at),
            failure_detail=failure,
        )
    )
    return {
        "processingStatus": status,
        "alreadyCaptured": False,
        "captureReference": checksum,
        "recordCount": count,
        "failureDetail": failure,
    }


# review(prior_capture, current_capture) -> summary; feature 007 creates cases with it.
Review = Callable[[ShortageCaptureRow, ShortageCaptureRow], dict]


def update_shortages(
    *,
    store: PipelineStore,
    config: ApplicationConfig,
    download: Callable[[str, int, BinaryIO], int] = download_release,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    review: Review | None = None,
) -> dict:
    """Download the shortage file and store it. Raises DownloadError on download failure.

    If the active file changes as a result, ``review`` compares the previous and
    the new active file (feature 007); its summary is returned as ``review``.
    """

    temporary_path: Path | None = None
    try:
        retrieved_at = now()
        previous = store.active_shortage_capture()
        with tempfile.NamedTemporaryFile(
            prefix="shortages-", suffix=".txt", delete=False
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            size = download(
                config.fimea_shortages_url,
                config.max_source_release_upload_bytes,
                temporary_file,
            )
        outcome = store_shortage_file(
            store=store,
            config=config,
            path=temporary_path,
            source_url=config.fimea_shortages_url,
            retrieved_at=retrieved_at,
        )
        result = {**outcome, "downloadedBytes": size}
        current = store.active_shortage_capture()
        if (
            review is not None
            and previous is not None
            and current is not None
            and previous.checksum != current.checksum
        ):
            result["review"] = review(previous, current)
        return result
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


class UpdatePhase(StrEnum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class UpdateStatus:
    phase: UpdatePhase = UpdatePhase.IDLE
    trigger: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: dict | None = None
    error: str | None = None

    @property
    def running(self) -> bool:
        return self.phase is UpdatePhase.RUNNING


class ShortageUpdate:
    """At most one shortage update at a time, run in a background thread."""

    def __init__(
        self,
        download: Callable[[str, int, BinaryIO], int] = download_release,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.download = download
        self.now = now
        self._lock = threading.Lock()
        self._status = UpdateStatus()
        self._thread: threading.Thread | None = None

    def status(self) -> UpdateStatus:
        with self._lock:
            return self._status

    def start(
        self,
        store: PipelineStore,
        config: ApplicationConfig,
        trigger: str = "BUTTON",
        review: Review | None = None,
    ) -> tuple[UpdateStatus, bool]:
        with self._lock:
            if self._status.running:
                return self._status, False
            self._status = UpdateStatus(
                phase=UpdatePhase.RUNNING, trigger=trigger, started_at=self.now()
            )
            status = self._status
            self._thread = threading.Thread(
                target=self._run,
                args=(store, config, review),
                name="shortage-update",
                daemon=True,
            )
            self._thread.start()
        return status, True

    def wait(self, timeout: float | None = None) -> UpdateStatus:
        thread = self._thread
        if thread is not None:
            thread.join(timeout)
        return self.status()

    def _finish(self, **changes) -> None:
        with self._lock:
            self._status = replace(self._status, finished_at=self.now(), **changes)

    def _run(self, store: PipelineStore, config: ApplicationConfig, review) -> None:
        try:
            result = update_shortages(
                store=store, config=config, download=self.download, now=self.now, review=review
            )
        except DownloadError as error:
            self._finish(phase=UpdatePhase.FAILED, error=str(error))
            return
        except Exception:  # noqa: BLE001 - report, never crash the thread silently
            logger.exception("Shortage update failed.")
            self._finish(
                phase=UpdatePhase.FAILED,
                error="The update failed unexpectedly; see the backend log.",
            )
            return
        if result["processingStatus"] != "VALIDATED":
            self._finish(
                phase=UpdatePhase.FAILED,
                result=result,
                error=f"The shortage file was not accepted: {result['failureDetail']}",
            )
            return
        self._finish(phase=UpdatePhase.SUCCEEDED, result=result)


def update_status_response(status: UpdateStatus) -> dict:
    def _time(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    return {
        "phase": status.phase.value,
        "running": status.running,
        "trigger": status.trigger,
        "startedAt": _time(status.started_at),
        "finishedAt": _time(status.finished_at),
        "result": dict(status.result) if status.result is not None else None,
        "error": status.error,
    }
