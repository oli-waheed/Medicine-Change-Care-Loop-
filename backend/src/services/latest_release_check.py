"""Feature 005: download the latest Fimea release on request and ingest it.

One check runs at a time, in a background thread, because downloading and
ingesting a real release takes about a minute. The check sends the same
metadata as the n8n workflow and goes through the same ingestion as an upload,
so duplicate files, chronology and review-case creation follow existing rules.
"""

import hashlib
import logging
import tempfile
import threading
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger(__name__)

SOURCE_NAME = "Fimea Basic Register"
_CHUNK_SIZE = 1024 * 1024
_DOWNLOAD_TIMEOUT_SECONDS = 120


class CheckPhase(StrEnum):
    IDLE = "IDLE"
    DOWNLOADING = "DOWNLOADING"
    INGESTING = "INGESTING"
    PREPARING_CATALOGUE = "PREPARING_CATALOGUE"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


RUNNING_PHASES = frozenset(
    {CheckPhase.DOWNLOADING, CheckPhase.INGESTING, CheckPhase.PREPARING_CATALOGUE}
)


class DownloadError(Exception):
    """The release could not be downloaded; the message is shown to the user."""


@dataclass(frozen=True, slots=True)
class CheckStatus:
    phase: CheckPhase = CheckPhase.IDLE
    source_url: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    downloaded_bytes: int | None = None
    result: dict | None = None
    error: str | None = None

    @property
    def running(self) -> bool:
        return self.phase in RUNNING_PHASES


def download_release(url: str, max_bytes: int, target: BinaryIO) -> int:
    """Stream ``url`` into ``target``; return the byte count. Raises DownloadError."""

    total = 0
    try:
        with urllib.request.urlopen(url, timeout=_DOWNLOAD_TIMEOUT_SECONDS) as response:
            while chunk := response.read(_CHUNK_SIZE):
                total += len(chunk)
                if total > max_bytes:
                    raise DownloadError(
                        f"The download is larger than the configured maximum of {max_bytes} bytes."
                    )
                target.write(chunk)
    except urllib.error.HTTPError as error:
        raise DownloadError(f"Fimea answered HTTP {error.code}.") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        reason = getattr(error, "reason", error)
        raise DownloadError(f"Could not reach Fimea: {reason}.") from error
    if total == 0:
        raise DownloadError("The download was empty.")
    return total


# ingest(path, checksum, retrieved_at, release_reference) -> IngestedFile
Ingest = Callable[[Path, str, str, object], object]


class LatestReleaseCheck:
    """Runs at most one download-and-ingest check at a time."""

    def __init__(
        self,
        download: Callable[[str, int, BinaryIO], int] = download_release,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._download = download
        self._now = now
        self._lock = threading.Lock()
        self._status = CheckStatus()
        self._thread: threading.Thread | None = None

    def status(self) -> CheckStatus:
        with self._lock:
            return self._status

    def _set(self, **changes) -> None:
        with self._lock:
            self._status = replace(self._status, **changes)

    def start(
        self,
        *,
        url: str,
        max_bytes: int,
        ingest: Ingest,
        warm_catalogue: Callable[[], None],
    ) -> tuple[CheckStatus, bool]:
        """Start a check unless one is running. Returns ``(status, started)``."""

        with self._lock:
            if self._status.running:
                return self._status, False
            self._status = CheckStatus(
                phase=CheckPhase.DOWNLOADING, source_url=url, started_at=self._now()
            )
            status = self._status
            self._thread = threading.Thread(
                target=self._run,
                args=(url, max_bytes, ingest, warm_catalogue),
                name="latest-release-check",
                daemon=True,
            )
            self._thread.start()
        return status, True

    def wait(self, timeout: float | None = None) -> None:
        """Wait for the running check to finish (used by tests)."""
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    def _run(self, url, max_bytes, ingest, warm_catalogue) -> None:
        temporary_path: Path | None = None
        try:
            retrieved_at = self._now().isoformat()
            digest = hashlib.sha256()
            with tempfile.NamedTemporaryFile(
                prefix="latest-release-", suffix=".xml", delete=False
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                size = self._download(url, max_bytes, temporary_file)
            with temporary_path.open("rb") as written:
                while chunk := written.read(_CHUNK_SIZE):
                    digest.update(chunk)

            self._set(phase=CheckPhase.INGESTING, downloaded_bytes=size)
            reference = {"value": url, "evidenceClass": "VERIFIED"}
            ingested = ingest(temporary_path, digest.hexdigest(), retrieved_at, reference)
            result = {
                **ingested.response,
                "releaseDate": ingested.release_date,
                "reviewCasesCreated": ingested.review_cases_created,
            }

            if result["processingStatus"] == "VALIDATED":
                # Load the catalogue now so the next catalogue visit is fast.
                self._set(phase=CheckPhase.PREPARING_CATALOGUE, result=result)
                try:
                    warm_catalogue()
                except Exception:  # noqa: BLE001 - the check itself succeeded
                    logger.exception("Catalogue could not be prepared after the check.")

            if result["processingStatus"] != "VALIDATED":
                self._set(
                    phase=CheckPhase.FAILED,
                    result=result,
                    error=f"The release was not accepted: {result['failureDetail']}",
                    finished_at=self._now(),
                )
                return
            self._set(phase=CheckPhase.SUCCEEDED, result=result, finished_at=self._now())
        except DownloadError as error:
            self._set(phase=CheckPhase.FAILED, error=str(error), finished_at=self._now())
        except ValueError as error:
            self._set(
                phase=CheckPhase.FAILED,
                error=f"The release was not accepted: {error}",
                finished_at=self._now(),
            )
        except Exception:  # noqa: BLE001 - report, never crash the thread silently
            logger.exception("Latest-release check failed.")
            self._set(
                phase=CheckPhase.FAILED,
                error="The check failed unexpectedly; see the backend log.",
                finished_at=self._now(),
            )
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


def status_response(status: CheckStatus) -> dict:
    """camelCase JSON for the API (contracts/latest-release-check-api.md)."""

    def _time(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    return {
        "phase": status.phase.value,
        "running": status.running,
        "sourceUrl": status.source_url,
        "startedAt": _time(status.started_at),
        "finishedAt": _time(status.finished_at),
        "downloadedBytes": status.downloaded_bytes,
        "result": dict(status.result) if status.result is not None else None,
        "error": status.error,
    }
