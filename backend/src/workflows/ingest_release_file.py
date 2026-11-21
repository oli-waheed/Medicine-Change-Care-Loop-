"""Ingest one release file already on disk.

Shared by the upload endpoint (``POST /api/source-releases/ingest``) and the
latest-release check (feature 005), so both follow exactly the same capture,
duplicate, chronology and comparison rules.
"""

from dataclasses import dataclass
from pathlib import Path

from ..config import ApplicationConfig
from ..services.ingest_source_release import (
    IngestionOutcome,
    ProcessingStatus,
    ingest_source_release,
    reload_captured_release,
    source_order_key,
    validate_release_metadata,
)
from ..services.pipeline_store import PipelineStore
from .ingestion_to_review import run_ingested_release_to_review


@dataclass(frozen=True, slots=True)
class IngestedFile:
    """The ingestion response plus facts the latest-release check reports."""

    response: dict[str, str | bool | None]
    release_date: str | None = None
    review_cases_created: int = 0


def _compare_with_baseline(
    store: PipelineStore, outcome: IngestionOutcome, medication_records: tuple
) -> tuple[tuple, tuple]:
    """Return ``(review cases, matching outcomes)`` from comparing with the baseline.

    Only releases with backend-derived (Ajopvm) chronology are compared, and only
    when strictly newer than the baseline. Older, equal-dated and UNKNOWN-order
    releases are recorded for traceability but never compared.
    """
    current_key = source_order_key(outcome.source_order)
    if current_key is None:
        return (), ()
    baseline_row = store.comparison_baseline()
    if baseline_row is None or baseline_row.source_order_key >= current_key:
        return (), ()
    baseline = reload_captured_release(baseline_row.capture_directory)
    if baseline.processing_status is not ProcessingStatus.VALIDATED:
        raise RuntimeError(f"Stored baseline no longer validates: {baseline.failure_detail}")
    result = run_ingested_release_to_review(
        baseline,
        outcome,
        medication_records,
        open_cases=[],
    )
    return result.created_cases, result.outcomes


def ingest_release_file(
    *,
    store: PipelineStore,
    config: ApplicationConfig,
    medication_records: tuple,
    path: Path,
    filename: str,
    checksum: str,
    source_name: str,
    release_reference: object,
    order_evidence: object,
    retrieved_at: str,
) -> IngestedFile:
    """Capture a release file, persist it and compare it with the stored baseline.

    Raises ``ValueError`` for invalid metadata or an invalid capture payload.
    """
    parsed_retrieved_at = validate_release_metadata(
        source_name, release_reference, order_evidence, retrieved_at
    )

    # Identical content already captured (e.g. the unchanged daily Fimea file):
    # keep the single stored copy and record only this retrieval.
    existing = store.capture_with_identical_content(source_name, {checksum})
    if existing is not None:
        store.record_retrieval(existing, parsed_retrieved_at, release_reference)
        return IngestedFile(
            {
                "processingStatus": existing.processing_status,
                "chronologyStatus": (
                    "AVAILABLE" if existing.source_order_key is not None else "UNAVAILABLE"
                ),
                "capturedReleaseReference": existing.release_id,
                "failureDetail": existing.failure_detail,
                "alreadyCaptured": True,
            }
        )

    payload = {
        "sourceName": source_name,
        "sourceReleaseReference": release_reference,
        "sourceOrder": order_evidence,
        "retrievedAt": retrieved_at,
        "files": [
            {
                "name": filename,
                "checksum": checksum,
                "contentReference": str(path),
            }
        ],
        "captureStatus": "COMPLETE",
    }
    outcome = ingest_source_release(payload, storage_dir=config.source_release_storage_dir)

    captured_reference = (
        outcome.captured_release.release_id if outcome.captured_release is not None else None
    )
    cases: tuple = ()
    if outcome.captured_release is not None and not store.is_known_release(captured_reference):
        cases, processing_outcomes = (
            _compare_with_baseline(store, outcome, medication_records)
            if outcome.processing_status is ProcessingStatus.VALIDATED
            else ((), ())
        )
        # Capture, cases and matching outcomes are written in one transaction.
        store.record_ingestion(outcome, cases, processing_outcomes)

    release = outcome.source_release
    return IngestedFile(
        {
            "processingStatus": outcome.processing_status.value,
            "chronologyStatus": outcome.chronology_status.value,
            "capturedReleaseReference": captured_reference,
            "failureDetail": outcome.failure_detail,
            "alreadyCaptured": False,
        },
        release_date=release.ajopvm.value if release is not None else None,
        review_cases_created=len(cases),
    )
