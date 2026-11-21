"""Feature 006: Fimea shortage data (contracts/shortages-api.md).

``GET /api/shortages`` lists the active shortage file with each VNR's packages
in the active catalogue release; ``POST``/``GET /api/shortages/update`` download
the latest file on request. Nothing here reads, changes or closes review cases.
"""

from collections import Counter
from datetime import UTC, datetime

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from ..config import ApplicationConfig
from ..models import ShortageCaptureRow
from ..schemas.medicine_catalogue import source_value
from ..services.medicine_shortages import (
    ShortageFileReader,
    ShortageRecord,
    ShortageUpdate,
    update_status_response,
)
from ..services.shortage_review_cases import (
    build_shortage_review,
    detect_shortage_changes,
    read_capture,
)
from .medicine_catalogue import catalogue_service

router = APIRouter(prefix="/api/shortages", tags=["shortages"])

MAX_PAGE_SIZE = 200
LICENCE = "CC BY 4.0"
SOURCE_NAME = "Fimea shortage data (Shortages.txt)"


def shortage_update(app: FastAPI) -> ShortageUpdate:
    update = getattr(app.state, "shortage_update", None)
    if update is None:
        update = ShortageUpdate()
        app.state.shortage_update = update
    return update


def shortage_review(app: FastAPI):
    """Feature 007: compare two active shortage files and store cases and outcomes."""

    def review(prior: ShortageCaptureRow, current: ShortageCaptureRow) -> dict:
        service = catalogue_service(app)
        try:
            baseline = service.get_baseline()
        except (ValueError, OSError):
            baseline = None
        packages = service.packages_by_vnr(baseline) if baseline is not None else None
        prior_records, current_records = read_capture(prior), read_capture(current)
        cases, outcomes = build_shortage_review(
            prior_capture=prior,
            prior_records=prior_records,
            current_capture=current,
            current_records=current_records,
            baseline=baseline,
            packages_by_vnr=packages,
            records=tuple(app.state.medication_records),
            now=datetime.now(UTC),
        )
        created = app.state.store.record_shortage_review(cases, outcomes)
        return {
            "comparedWith": prior.checksum,
            "changes": len(detect_shortage_changes(prior_records, current_records)),
            "outcomes": len(outcomes),
            "reviewCasesCreated": created,
        }

    return review


def start_shortage_update(app: FastAPI, trigger: str = "BUTTON"):
    config: ApplicationConfig = app.state.source_release_config
    return shortage_update(app).start(
        app.state.store, config, trigger=trigger, review=shortage_review(app)
    )


def _reader(app: FastAPI) -> ShortageFileReader:
    reader = getattr(app.state, "shortage_reader", None)
    if reader is None:
        reader = ShortageFileReader()
        app.state.shortage_reader = reader
    return reader


def _time(value) -> str | None:
    if value is None:
        return None
    return (value.replace(tzinfo=UTC) if value.tzinfo is None else value).isoformat()


def _package(snapshot) -> dict:
    product = snapshot.product
    return {
        "pakkaustunnus": snapshot.pakkaustunnus,
        "productReference": snapshot.product_reference.value,
        "productName": source_value(product.kauppanimi),
        "strength": source_value(product.vahvuus),
        "pharmaceuticalForm": source_value(product.laakemuoto),
        "packageSizeText": source_value(snapshot.package.pakkauskoko_teksti),
    }


def _text(field) -> str:
    return (field.value or "").casefold()


def _matches(record: ShortageRecord, query: str, packages) -> bool:
    if query in record.vnr.casefold() or query in record.company.casefold():
        return True
    return any(query in _text(snapshot.product.kauppanimi) for snapshot in packages or ())


@router.get("")
def list_shortages(
    request: Request,
    q: str = "",
    valid: str = "",
    page: int = Query(1),
    page_size: int = Query(50, alias="pageSize"),
) -> dict:
    if page < 1 or not 1 <= page_size <= MAX_PAGE_SIZE:
        raise HTTPException(
            status_code=422,
            detail=f"page must be at least 1 and pageSize between 1 and {MAX_PAGE_SIZE}.",
        )
    app = request.app
    try:
        active = _reader(app).active(app.state.store)
    except (ValueError, OSError) as error:
        raise HTTPException(
            status_code=503,
            detail={"code": "SHORTAGES_SOURCE_UNREADABLE", "message": str(error)},
        ) from error
    if active is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SHORTAGES_UNAVAILABLE",
                "message": "No shortage data has been downloaded yet.",
            },
        )

    # The catalogue is used only when already in memory, so this list never waits
    # for a 190 MB release to be reconstructed; otherwise it is prepared meanwhile.
    service = catalogue_service(app)
    baseline = service.cached_baseline()
    if baseline is not None:
        by_vnr = service.packages_by_vnr(baseline)
        catalogue = {
            "status": "READY",
            "releaseId": baseline.release_id,
            "releaseDate": baseline.capture.source_order_value,
        }
    else:
        by_vnr = None
        has_baseline = app.state.store.comparison_baseline() is not None
        if has_baseline:
            service.warm_in_background()
        catalogue = {
            "status": "LOADING" if has_baseline else "UNAVAILABLE",
            "releaseId": None,
            "releaseDate": None,
        }

    records = active.records
    query = q.strip().casefold()
    selected = [
        record
        for record in records
        if (not valid or record.valid == valid)
        and (
            not query
            or _matches(record, query, by_vnr.get(record.vnr) if by_vnr is not None else None)
        )
    ]
    start = (page - 1) * page_size
    capture = active.capture
    return {
        "source": {
            "sourceName": SOURCE_NAME,
            "sourceUrl": capture.source_url,
            "captureReference": capture.checksum,
            "sizeBytes": capture.size_bytes,
            "recordCount": len(records),
            "firstRetrievedAt": _time(capture.first_retrieved_at),
            "lastRetrievedAt": _time(capture.last_retrieved_at),
            "retrievalCount": app.state.store.shortage_retrieval_count(capture.sequence),
            "latestUpdated": max((record.updated for record in records), default=None),
            "licence": LICENCE,
        },
        "catalogue": catalogue,
        "validCounts": dict(sorted(Counter(record.valid for record in records).items())),
        "total": len(selected),
        "page": page,
        "pageSize": page_size,
        "items": [
            {
                "line": record.line,
                "vnr": record.vnr,
                "valid": record.valid,
                "unavailableFrom": record.unavailable_from,
                "endingDate": record.ending_date,
                "notificationDate": record.notification_date,
                "updated": record.updated,
                "company": record.company,
                "packages": (
                    [_package(snapshot) for snapshot in by_vnr.get(record.vnr, ())]
                    if by_vnr is not None
                    else None
                ),
            }
            for record in selected[start : start + page_size]
        ],
    }


@router.get("/update")
def get_shortage_update(request: Request) -> dict:
    """Progress and result of the most recent shortage update since the backend started."""
    return update_status_response(shortage_update(request.app).status())


@router.post("/update", status_code=status.HTTP_202_ACCEPTED)
def start_shortage_update_endpoint(request: Request) -> JSONResponse:
    """Download the latest shortage file now, unless an update is already running."""
    current, started = start_shortage_update(request.app)
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={**update_status_response(current), "started": started},
    )
