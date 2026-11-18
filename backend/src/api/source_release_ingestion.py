"""Upload and ingest a source release."""

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from ..config import ApplicationConfig
from ..services.ingest_source_release import (
    IngestionOutcome,
    ProcessingStatus,
    ingest_source_release,
    reload_captured_release,
    source_order_key,
)
from ..services.pipeline_store import PipelineStore
from ..workflows.ingestion_to_review import run_ingested_release_to_review

router = APIRouter(prefix="/api/source-releases", tags=["source-releases"])

_UPLOAD_CHUNK_SIZE = 1024 * 1024


def _compare_with_baseline(
    request: Request, store: PipelineStore, outcome: IngestionOutcome
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
        tuple(request.app.state.medication_records),
        open_cases=[],
    )
    return result.created_cases, result.outcomes


@router.post("/ingest")
async def ingest_uploaded_source_release(
    request: Request,
    file: Annotated[UploadFile, File()],
    source_name: Annotated[str, Form(alias="sourceName")],
    source_release_reference: Annotated[str, Form(alias="sourceReleaseReference")],
    retrieved_at: Annotated[str, Form(alias="retrievedAt")],
    source_order: Annotated[str | None, Form(alias="sourceOrder")] = None,
) -> dict[str, str | None]:
    """Capture a release, persist it, and compare it with the stored baseline."""
    try:
        release_reference = json.loads(source_release_reference)
        # Caller-declared order is recorded for traceability only; chronology
        # is derived by the backend from the release's own Ajopvm.
        order_evidence = json.loads(source_order) if source_order else None
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid JSON source metadata: {error.msg}.",
        ) from error

    config: ApplicationConfig = request.app.state.source_release_config
    temporary_path: Path | None = None

    try:
        digest = hashlib.sha256()
        total_bytes = 0

        with tempfile.NamedTemporaryFile(
            prefix="source-release-",
            suffix=".xml",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

            while chunk := await file.read(_UPLOAD_CHUNK_SIZE):
                total_bytes += len(chunk)

                if total_bytes > config.max_source_release_upload_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "Source release upload exceeds the configured maximum of "
                            f"{config.max_source_release_upload_bytes} bytes."
                        ),
                    )

                digest.update(chunk)
                temporary_file.write(chunk)

        filename = (file.filename or "source-release.xml").replace("\\", "/").rsplit("/", 1)[-1]

        payload = {
            "sourceName": source_name,
            "sourceReleaseReference": release_reference,
            "sourceOrder": order_evidence,
            "retrievedAt": retrieved_at,
            "files": [
                {
                    "name": filename,
                    "checksum": digest.hexdigest(),
                    "contentReference": str(temporary_path),
                }
            ],
            "captureStatus": "COMPLETE",
        }

        try:
            outcome = ingest_source_release(
                payload,
                storage_dir=config.source_release_storage_dir,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=422,
                detail=str(error),
            ) from error

        captured_reference = (
            outcome.captured_release.release_id if outcome.captured_release is not None else None
        )

        if outcome.captured_release is not None:
            store: PipelineStore = request.app.state.store
            if not store.is_known_release(captured_reference):
                cases, processing_outcomes = (
                    _compare_with_baseline(request, store, outcome)
                    if outcome.processing_status is ProcessingStatus.VALIDATED
                    else ((), ())
                )
                # Capture, cases and matching outcomes are written in one transaction.
                store.record_ingestion(outcome, cases, processing_outcomes)

        return {
            "processingStatus": outcome.processing_status.value,
            "chronologyStatus": outcome.chronology_status.value,
            "capturedReleaseReference": captured_reference,
            "failureDetail": outcome.failure_detail,
        }

    finally:
        try:
            await file.close()
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
