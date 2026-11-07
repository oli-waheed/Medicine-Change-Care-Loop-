
"""Upload and ingest a source release."""

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from ..config import ApplicationConfig
from ..domain.evidence import EvidenceClassification
from ..services.ingest_source_release import (
    IngestionOutcome,
    ProcessingStatus,
    ingest_source_release,
)
from ..workflows.ingestion_to_review import run_ingested_release_to_review

router = APIRouter(prefix="/api/source-releases", tags=["source-releases"])

_UPLOAD_CHUNK_SIZE = 1024 * 1024


def _verified_order(outcome: IngestionOutcome) -> int | None:
    """Return source order only when it is explicitly VERIFIED and numeric."""
    evidence = outcome.source_order

    if (
        evidence.evidence_class is not EvidenceClassification.VERIFIED
        or evidence.value is None
    ):
        return None

    try:
        return int(evidence.value.strip())
    except ValueError:
        return None


@router.post("/ingest")
async def ingest_uploaded_source_release(
    request: Request,
    file: Annotated[UploadFile, File()],
    source_name: Annotated[str, Form(alias="sourceName")],
    source_release_reference: Annotated[str, Form(alias="sourceReleaseReference")],
    source_order: Annotated[str, Form(alias="sourceOrder")],
    retrieved_at: Annotated[str, Form(alias="retrievedAt")],
) -> dict[str, str | None]:
    """Capture a release and connect it to the comparison workflow."""
    try:
        release_reference = json.loads(source_release_reference)
        order_evidence = json.loads(source_order)
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

        filename = (
            (file.filename or "source-release.xml")
            .replace("\\", "/")
            .rsplit("/", 1)[-1]
        )

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
            outcome.captured_release.release_id
            if outcome.captured_release is not None
            else None
        )

        if (
            outcome.processing_status is ProcessingStatus.VALIDATED
            and outcome.captured_release is not None
        ):
            # Keep every unique validated capture for traceability and replay
            # detection, including releases with UNKNOWN or conflicting order.
            history: list[IngestionOutcome] = getattr(
                request.app.state,
                "source_release_history",
                [],
            )
            request.app.state.source_release_history = history

            known_release_ids = {
                item.captured_release.release_id
                for item in history
                if item.captured_release is not None
            }

            if captured_reference not in known_release_ids:
                history.append(outcome)

                current_order = _verified_order(outcome)
                baseline: IngestionOutcome | None = getattr(
                    request.app.state,
                    "source_release_comparison_baseline",
                    None,
                )

                # An UNKNOWN release is retained in capture history but
                # cannot become a comparison baseline.
                if current_order is not None:
                    if baseline is None:
                        # First release with usable verified chronology.
                        # Do not compare it against an UNKNOWN release.
                        request.app.state.source_release_comparison_baseline = (
                            outcome
                        )
                    else:
                        previous_order = _verified_order(baseline)

                        if previous_order is None:
                            # Recover safely if an older baseline has no
                            # usable chronology.
                            request.app.state.source_release_comparison_baseline = (
                                outcome
                            )
                        elif current_order > previous_order:
                            medication_records = tuple(
                                getattr(
                                    request.app.state,
                                    "medication_records",
                                    (),
                                )
                            )

                            run_ingested_release_to_review(
                                baseline,
                                outcome,
                                medication_records,
                                open_cases=request.app.state.open_review_cases,
                            )

                            request.app.state.source_release_comparison_baseline = (
                                outcome
                            )

                        # Equal or decreasing source order is retained in
                        # capture history but does not replace the baseline.

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
