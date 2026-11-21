"""Upload and ingest a source release."""

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from ..config import ApplicationConfig
from ..services.pipeline_store import PipelineStore
from ..workflows.ingest_release_file import ingest_release_file

router = APIRouter(prefix="/api/source-releases", tags=["source-releases"])

_UPLOAD_CHUNK_SIZE = 1024 * 1024


@router.post("/ingest")
async def ingest_uploaded_source_release(
    request: Request,
    file: Annotated[UploadFile, File()],
    source_name: Annotated[str, Form(alias="sourceName")],
    source_release_reference: Annotated[str, Form(alias="sourceReleaseReference")],
    retrieved_at: Annotated[str, Form(alias="retrievedAt")],
    source_order: Annotated[str | None, Form(alias="sourceOrder")] = None,
) -> dict[str, str | bool | None]:
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

        store: PipelineStore = request.app.state.store
        try:
            ingested = ingest_release_file(
                store=store,
                config=config,
                medication_records=tuple(request.app.state.medication_records),
                path=temporary_path,
                filename=filename,
                checksum=digest.hexdigest(),
                source_name=source_name,
                release_reference=release_reference,
                order_evidence=order_evidence,
                retrieved_at=retrieved_at,
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return ingested.response

    finally:
        try:
            await file.close()
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
