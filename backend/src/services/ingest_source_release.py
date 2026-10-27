"""Validate captured source releases before exposing normalized snapshots."""

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from xml.etree.ElementTree import ParseError

from ..domain.evidence import EvidenceClassification
from ..domain.medicine_snapshot import MedicineSnapshot
from ..domain.source_release import SourceRelease
from .capture_source_release import (
    CapturedSourceRelease,
    RawReleaseFile,
    SourceEvidence,
    capture_source_release,
)
from .normalize_basic_register_release import normalize_basic_register_release


class ProcessingStatus(StrEnum):
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"


class ChronologyStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class IngestionOutcome:
    processing_status: ProcessingStatus
    source_order: SourceEvidence
    captured_release: CapturedSourceRelease | None = None
    source_releases: tuple[SourceRelease, ...] = ()
    snapshots: tuple[MedicineSnapshot, ...] = ()
    failure_detail: str | None = None

    @property
    def source_release(self) -> SourceRelease | None:
        """Return the sole normalized source release when the ingestion has one."""
        if len(self.source_releases) == 1:
            return self.source_releases[0]
        return None

    @property
    def verified_chronological_order(self) -> bool:
        return self.chronology_status is ChronologyStatus.AVAILABLE

    @property
    def chronology_status(self) -> ChronologyStatus:
        """Report order-evidence availability separately from data validation."""
        if (
            self.source_order.value is not None
            and bool(self.source_order.value.strip())
            and self.source_order.evidence_class is EvidenceClassification.VERIFIED
        ):
            return ChronologyStatus.AVAILABLE
        return ChronologyStatus.UNAVAILABLE


_SHA256 = re.compile(r"^(?:sha256:)?([0-9a-fA-F]{64})$")


def _failure(
    detail: str,
    source_order: SourceEvidence,
    captured_release: CapturedSourceRelease | None = None,
) -> IngestionOutcome:
    return IngestionOutcome(
        processing_status=ProcessingStatus.FAILED,
        source_order=source_order,
        captured_release=captured_release,
        failure_detail=detail,
    )


def _evidence(value: object, field_name: str) -> SourceEvidence:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must include a value and evidenceClass.")
    raw_value = value.get("value")
    if raw_value is not None and not isinstance(raw_value, str):
        raise ValueError(f"{field_name}.value must be a string or null.")
    try:
        classification = EvidenceClassification(value.get("evidenceClass"))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name}.evidenceClass is invalid.") from error
    return SourceEvidence(raw_value, classification)


def _retrieved_at(value: object) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("retrievedAt must be a timezone-aware ISO-8601 timestamp.")
    try:
        retrieved_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("retrievedAt must be a timezone-aware ISO-8601 timestamp.") from error
    if retrieved_at.utcoffset() is None:
        raise ValueError("retrievedAt must be a timezone-aware ISO-8601 timestamp.")
    return retrieved_at


def _read_files(payload: dict) -> tuple[RawReleaseFile, ...]:
    file_entries = payload.get("files")
    if not isinstance(file_entries, list) or not file_entries:
        raise ValueError("A complete source release must include at least one file.")

    capture_directory = payload.get("captureDirectory")
    if capture_directory is not None and not isinstance(capture_directory, str):
        raise ValueError("captureDirectory must be a path string when provided.")

    raw_files = []
    seen_names = set()
    for entry in file_entries:
        if not isinstance(entry, dict):
            raise ValueError("Each source release file must be an object.")
        name = entry.get("name")
        reference = entry.get("contentReference")
        checksum = entry.get("checksum")
        if not isinstance(name, str) or not name:
            raise ValueError("Each source release file must have a name.")
        if name in seen_names:
            raise ValueError(f"Duplicate source release file name: {name}")
        seen_names.add(name)
        if not isinstance(reference, str) or not reference:
            raise ValueError(f"File {name} has no retrievable contentReference.")
        checksum_match = _SHA256.fullmatch(checksum) if isinstance(checksum, str) else None
        if checksum_match is None:
            raise ValueError(f"File {name} must provide a SHA-256 checksum.")
        path = Path(reference)
        if not path.is_absolute() and capture_directory is not None:
            path = Path(capture_directory) / path
        try:
            content = path.read_bytes()
        except OSError as error:
            raise OSError(f"Cannot access source file {name}: {error}") from error
        actual_checksum = hashlib.sha256(content).hexdigest()
        if actual_checksum.lower() != checksum_match.group(1).lower():
            raise ValueError(f"Checksum mismatch for source file {name}.")

        locators = entry.get("recordLocators", [])
        if not isinstance(locators, list) or any(
            not isinstance(locator, str) or not locator.strip() for locator in locators
        ):
            raise ValueError(f"File {name} has invalid record locators.")
        raw_files.append(RawReleaseFile(name, content, tuple(locators)))
    return tuple(raw_files)


def ingest_source_release(payload: dict, *, storage_dir: str | Path) -> IngestionOutcome:
    """Capture and validate a release atomically, returning no partial snapshots."""
    if not isinstance(payload, dict):
        raise ValueError("A source release request must be an object.")

    source_order = _evidence(payload.get("sourceOrder"), "sourceOrder")
    source_name = payload.get("sourceName")
    reference = _evidence(payload.get("sourceReleaseReference"), "sourceReleaseReference")
    retrieved_at = _retrieved_at(payload.get("retrievedAt"))
    capture_status = payload.get("captureStatus")
    if not isinstance(source_name, str) or not source_name.strip():
        raise ValueError("sourceName is required.")
    if source_name != "Fimea Basic Register":
        raise ValueError("Only Fimea Basic Register releases are supported.")
    if not isinstance(capture_status, str) or capture_status not in {"COMPLETE", "FAILED"}:
        raise ValueError("captureStatus must be COMPLETE or FAILED.")
    if capture_status == "FAILED":
        return _failure("Source acquisition failed.", source_order)

    try:
        raw_files = _read_files(payload)
    except OSError as error:
        return _failure(str(error), source_order)
    except ValueError as error:
        return _failure(str(error), source_order)

    try:
        captured_release = capture_source_release(
            storage_dir=storage_dir,
            source_name=source_name,
            source_release_reference=reference,
            source_order=source_order,
            retrieved_at=retrieved_at,
            files=raw_files,
        )
    except OSError as error:
        return _failure(f"Unable to persist source release: {error}", source_order)
    except ValueError as error:
        return _failure(f"Unable to capture source release: {error}", source_order)

    normalized_releases = []
    all_snapshots = []
    package_identifiers = set()
    try:
        for raw_file in raw_files:
            checksum = hashlib.sha256(raw_file.content).hexdigest()
            source_release, snapshots = normalize_basic_register_release(
                raw_file.content, file_name=raw_file.name, checksum=checksum
            )
            for snapshot in snapshots:
                if snapshot.pakkaustunnus in package_identifiers:
                    raise ValueError(
                        "Duplicate package identifier across source release files: "
                        f"{snapshot.pakkaustunnus!r}"
                    )
                package_identifiers.add(snapshot.pakkaustunnus)
            normalized_releases.append(source_release)
            all_snapshots.extend(snapshots)
    except (ParseError, ValueError) as error:
        return _failure(
            f"Source release validation failed: {error}", source_order, captured_release
        )

    if not all_snapshots:
        return _failure(
            "Source release contains no medicine records.", source_order, captured_release
        )
    return IngestionOutcome(
        processing_status=ProcessingStatus.VALIDATED,
        source_order=source_order,
        captured_release=captured_release,
        source_releases=tuple(normalized_releases),
        snapshots=tuple(all_snapshots),
    )
