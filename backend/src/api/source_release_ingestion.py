"""Upload and ingest a source release."""

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from ..config import ApplicationConfig
from ..services.ingest_source_release import ingest_source_release

router = APIRouter(prefix="/api/source-releases", tags=["source-releases"])

_UPLOAD_CHUNK_SIZE = 1024 * 1024


@router.post("/ingest")
async def ingest_uploaded_source_release(
    request: Request,
    file: Annotated[UploadFile, File()],
    source_name: Annotated[str, Form(alias="sourceName")],
    source_release_reference: Annotated[str, Form(alias="sourceReleaseReference")],
    source_order: Annotated[str, Form(alias="sourceOrder")],
    retrieved_at: Annotated[str, Form(alias="retrievedAt")],
) -> dict[str, str | None]:
    """Stream an uploaded release to temporary storage and invoke ingestion."""
    try:
        release_reference = json.loads(source_release_reference)
        order_evidence = json.loads(source_order)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=422, detail=f"Invalid JSON source metadata: {error.msg}."
        ) from error

    config: ApplicationConfig = request.app.state.source_release_config
    temporary_path: Path | None = None
    try:
        digest = hashlib.sha256()
        total_bytes = 0
        with tempfile.NamedTemporaryFile(prefix="source-release-", suffix=".xml", delete=False) as (
            temporary_file
        ):
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
            outcome = ingest_source_release(payload, storage_dir=config.source_release_storage_dir)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        captured_reference = (
            outcome.captured_release.release_id if outcome.captured_release is not None else None
        )
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
