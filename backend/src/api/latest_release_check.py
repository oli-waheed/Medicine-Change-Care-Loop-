"""Feature 005: check Fimea for the latest release from the app.

``POST`` starts one background check (download, then the same ingestion as
``POST /api/source-releases/ingest``); ``GET`` reports its progress. Neither
operation reads, changes or closes review cases directly.
"""

from pathlib import Path

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import JSONResponse

from ..config import ApplicationConfig
from ..services.latest_release_check import (
    SOURCE_NAME,
    LatestReleaseCheck,
    status_response,
)
from ..workflows.ingest_release_file import ingest_release_file
from .medicine_catalogue import catalogue_service

router = APIRouter(prefix="/api/source-releases", tags=["source-releases"])

_UNKNOWN_ORDER = {"value": None, "evidenceClass": "UNKNOWN"}


def latest_release_check(app: FastAPI) -> LatestReleaseCheck:
    check = getattr(app.state, "latest_release_check", None)
    if check is None:
        check = LatestReleaseCheck()
        app.state.latest_release_check = check
    return check


@router.get("/latest-check")
def get_latest_release_check(request: Request) -> dict:
    """Progress and result of the most recent check since the backend started."""
    return status_response(latest_release_check(request.app).status())


def start_latest_release_check(app: FastAPI):
    """Start a check for ``app`` unless one runs. Returns ``(status, started)``.

    Used by the button (``POST``) and by the daily automatic update (feature 006).
    """
    config: ApplicationConfig = app.state.source_release_config
    store = app.state.store
    records = tuple(app.state.medication_records)

    def ingest(path: Path, checksum: str, retrieved_at: str, reference: object):
        # Same metadata as the n8n workflow (workflow/n8n/fimea-basic-register-ingestion.json).
        return ingest_release_file(
            store=store,
            config=config,
            medication_records=records,
            path=path,
            filename="Perusrekisteri.xml",
            checksum=checksum,
            source_name=SOURCE_NAME,
            release_reference=reference,
            order_evidence=_UNKNOWN_ORDER,
            retrieved_at=retrieved_at,
        )

    def warm_catalogue() -> None:
        catalogue_service(app).get_baseline()

    return latest_release_check(app).start(
        url=config.fimea_release_url,
        max_bytes=config.max_source_release_upload_bytes,
        ingest=ingest,
        warm_catalogue=warm_catalogue,
    )


@router.post("/latest-check", status_code=status.HTTP_202_ACCEPTED)
def start_latest_release_check_endpoint(request: Request) -> JSONResponse:
    """Start a check; if one is already running, report it instead of starting another."""
    current, started = start_latest_release_check(request.app)
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={**status_response(current), "started": started},
    )
