"""Persist immutable raw source-release files and their capture evidence."""

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..domain.evidence import EvidenceClassification


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    value: str | None
    evidence_class: EvidenceClassification

    def __post_init__(self) -> None:
        if self.value is not None and not isinstance(self.value, str):
            raise TypeError("Source evidence values must be strings or None.")
        if not isinstance(self.evidence_class, EvidenceClassification):
            raise TypeError("Source evidence requires an EvidenceClassification.")


@dataclass(frozen=True, slots=True)
class RawReleaseFile:
    name: str
    content: bytes
    record_locators: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or self.name in {".", ".."} or "/" in self.name or "\\" in self.name:
            raise ValueError("A raw file name must be a non-empty base name.")
        if not isinstance(self.content, bytes):
            raise TypeError("Raw file content must be bytes.")
        if not isinstance(self.record_locators, tuple) or any(
            not isinstance(locator, str) or not locator.strip() for locator in self.record_locators
        ):
            raise ValueError("Record locators must be a tuple of non-empty strings.")


@dataclass(frozen=True, slots=True)
class CapturedReleaseFile:
    name: str
    checksum: str
    content_reference: str
    record_locators: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CapturedSourceRelease:
    release_id: str
    source_name: str
    source_release_reference: SourceEvidence
    source_order: SourceEvidence
    retrieved_at: datetime
    files: tuple[CapturedReleaseFile, ...]
    capture_directory: Path


def _serialize_evidence(evidence: SourceEvidence) -> dict[str, str | None]:
    return {
        "value": evidence.value,
        "evidenceClass": evidence.evidence_class.value,
    }


def _manifest(
    *,
    source_name: str,
    source_release_reference: SourceEvidence,
    source_order: SourceEvidence,
    retrieved_at: datetime,
    files: tuple[CapturedReleaseFile, ...],
) -> dict:
    return {
        "sourceName": source_name,
        "sourceReleaseReference": _serialize_evidence(source_release_reference),
        "sourceOrder": _serialize_evidence(source_order),
        "retrievedAt": retrieved_at.isoformat(),
        "files": [
            {
                "name": item.name,
                "checksum": item.checksum,
                "contentReference": item.content_reference,
                "recordLocators": list(item.record_locators),
            }
            for item in files
        ],
    }


def _json_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")


def _verify_existing_capture(
    capture_directory: Path,
    manifest_bytes: bytes,
    files: tuple[RawReleaseFile, ...],
    captured_files: tuple[CapturedReleaseFile, ...],
) -> None:
    manifest_path = capture_directory / "manifest.json"
    if not manifest_path.is_file() or manifest_path.read_bytes() != manifest_bytes:
        raise FileExistsError(f"Existing capture is not identical: {capture_directory}")
    for source_file, captured_file in zip(files, captured_files, strict=True):
        stored_path = capture_directory / captured_file.content_reference
        if not stored_path.is_file() or stored_path.read_bytes() != source_file.content:
            raise FileExistsError(f"Existing raw file differs: {stored_path}")


def capture_source_release(
    *,
    storage_dir: str | Path,
    source_name: str,
    source_release_reference: SourceEvidence,
    source_order: SourceEvidence,
    retrieved_at: datetime,
    files: tuple[RawReleaseFile, ...],
) -> CapturedSourceRelease:
    """Persist raw files once, retaining only source-supplied ordering evidence."""
    if not isinstance(source_name, str) or not source_name.strip():
        raise ValueError("A source name is required.")
    if not isinstance(source_release_reference, SourceEvidence):
        raise TypeError("A source release reference must include its evidence class.")
    if not isinstance(source_order, SourceEvidence):
        raise TypeError("Source order must include its evidence class.")
    if not isinstance(retrieved_at, datetime) or retrieved_at.utcoffset() is None:
        raise ValueError("Retrieval time must be a timezone-aware datetime.")
    if not isinstance(files, tuple) or not files:
        raise ValueError("At least one raw release file is required.")
    if any(not isinstance(item, RawReleaseFile) for item in files):
        raise TypeError("All release files must be RawReleaseFile values.")
    if len({item.name for item in files}) != len(files):
        raise ValueError("Raw release file names must be unique.")

    captured_files = tuple(
        CapturedReleaseFile(
            name=item.name,
            checksum=hashlib.sha256(item.content).hexdigest(),
            content_reference=f"files/{index:04d}/{item.name}",
            record_locators=item.record_locators,
        )
        for index, item in enumerate(files, start=1)
    )
    manifest = _manifest(
        source_name=source_name,
        source_release_reference=source_release_reference,
        source_order=source_order,
        retrieved_at=retrieved_at,
        files=captured_files,
    )
    manifest_bytes = _json_bytes(manifest)
    release_id = f"sha256-{hashlib.sha256(manifest_bytes).hexdigest()}"
    root = Path(storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    capture_directory = root / release_id

    if capture_directory.exists():
        _verify_existing_capture(capture_directory, manifest_bytes, files, captured_files)
    else:
        staging_directory = Path(tempfile.mkdtemp(prefix=".capture-", dir=root))
        try:
            for item, captured_file in zip(files, captured_files, strict=True):
                stored_path = staging_directory / captured_file.content_reference
                stored_path.parent.mkdir(parents=True, exist_ok=True)
                stored_path.write_bytes(item.content)
            (staging_directory / "manifest.json").write_bytes(manifest_bytes)
            try:
                os.rename(staging_directory, capture_directory)
            except OSError:
                if not capture_directory.exists():
                    raise
                _verify_existing_capture(capture_directory, manifest_bytes, files, captured_files)
        finally:
            if staging_directory.exists():
                shutil.rmtree(staging_directory)

    return CapturedSourceRelease(
        release_id=release_id,
        source_name=source_name,
        source_release_reference=source_release_reference,
        source_order=source_order,
        retrieved_at=retrieved_at,
        files=captured_files,
        capture_directory=capture_directory,
    )
