"""Read-only API for the medicine catalogue (feature 004, contracts/catalogue-api.md).

Every endpoint serves only the active baseline: the latest validated release with
verified chronology. None of them writes to the store, triggers ingestion, or
changes cases, outcomes or the baseline (FR-010).
"""

from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request

from ..schemas import medicine_catalogue as schema
from ..services.medicine_catalogue import (
    ABSENCE_FIELDS,
    CatalogueFilters,
    CatalogueUnavailableError,
    MedicineCatalogueService,
)

router = APIRouter(prefix="/api/medicine-catalogue", tags=["medicine-catalogue"])

UNAVAILABLE = {
    "code": "CATALOGUE_UNAVAILABLE",
    "message": "No validated source release with verified chronology is available.",
}
MAX_PAGE_SIZE = 200


def catalogue_service(app: FastAPI) -> MedicineCatalogueService:
    """The app's catalogue service, recreated when the store is replaced."""
    service = getattr(app.state, "medicine_catalogue", None)
    if service is None or service.store is not app.state.store:
        service = MedicineCatalogueService(app.state.store)
        app.state.medicine_catalogue = service
    return service


def _service(request: Request) -> MedicineCatalogueService:
    return catalogue_service(request.app)


def _baseline(service: MedicineCatalogueService):
    """The active baseline, or an explicit 503 (FR-009). Never falls back."""

    try:
        baseline = service.get_baseline()
    except (ValueError, OSError) as error:
        raise HTTPException(
            status_code=503,
            detail={"code": "CATALOGUE_SOURCE_UNREADABLE", "message": str(error)},
        ) from error
    if baseline is None:
        raise HTTPException(status_code=503, detail=UNAVAILABLE)
    return baseline


def _paging(page: int, page_size: int) -> tuple[int, int]:
    if page < 1:
        raise HTTPException(status_code=422, detail="page must be 1 or greater.")
    if not 1 <= page_size <= MAX_PAGE_SIZE:
        raise HTTPException(
            status_code=422, detail=f"pageSize must be between 1 and {MAX_PAGE_SIZE}."
        )
    return page, page_size


@router.get("")
def get_catalogue(
    request: Request,
    q: str = "",
    activeSubstance: str | None = None,
    atc: str | None = None,
    form: str | None = None,
    route: str | None = None,
    available: str | None = None,
    vnr: str | None = None,
    missing: str = "",
    page: int = 1,
    pageSize: Annotated[int, Query()] = 50,
) -> dict[str, object]:
    """Search and filter packages of the active release (FR-002, FR-003, FR-011)."""

    page, pageSize = _paging(page, pageSize)
    required_absent = frozenset(name.strip() for name in missing.split(",") if name.strip())
    unknown = sorted(required_absent - ABSENCE_FIELDS)
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown missing filter {unknown}; use one of {sorted(ABSENCE_FIELDS)}.",
        )
    if available not in (None, "", "0", "1"):
        raise HTTPException(status_code=422, detail="available must be 1 or 0.")
    service = _service(request)
    baseline = _baseline(service)
    filters = CatalogueFilters(
        active_substance=activeSubstance,
        atc=atc,
        form=form,
        route=route,
        available=available or None,
        vnr=vnr,
        missing=required_absent,
    )
    items = service.filter(q, filters) or ()
    return schema.catalogue_page(baseline, items, page=page, page_size=pageSize)


@router.get("/products/{product_reference}")
def get_product(request: Request, product_reference: str) -> dict[str, object]:
    """One product of the active release and its packages (FR-004)."""

    service = _service(request)
    baseline = _baseline(service)
    view = service.product(product_reference)
    if view is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PRODUCT_NOT_FOUND", "releaseId": baseline.release_id},
        )
    return schema.product_detail(baseline, view)


@router.get("/packages/{pakkaustunnus}")
def get_package(request: Request, pakkaustunnus: str) -> dict[str, object]:
    """One package record, its VNR and packages sharing that VNR (FR-005, FR-012, FR-013)."""

    service = _service(request)
    baseline = _baseline(service)
    view = service.package(pakkaustunnus)
    if view is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PACKAGE_NOT_FOUND", "releaseId": baseline.release_id},
        )
    return schema.package_detail(baseline, view)


@router.get("/active-substances")
def get_active_substances(
    request: Request, q: str = "", page: int = 1, pageSize: int = 50
) -> dict[str, object]:
    """Active substances with every occurrence in source order (FR-006)."""

    page, pageSize = _paging(page, pageSize)
    service = _service(request)
    baseline = _baseline(service)
    entries = service.active_substances(q) or ()
    return schema.substances_page(baseline, entries, page=page, page_size=pageSize)


@router.get("/compare")
def get_comparison(request: Request, productA: str = "", productB: str = "") -> dict[str, object]:
    """Side-by-side source fields of two products; no equivalence claim (FR-007)."""

    if not productA or not productB:
        raise HTTPException(status_code=422, detail="productA and productB are both required.")
    if productA == productB:
        raise HTTPException(status_code=422, detail="Choose two different products.")
    service = _service(request)
    baseline = _baseline(service)
    try:
        result = service.compare(productA, productB)
    except CatalogueUnavailableError as error:
        raise HTTPException(status_code=503, detail=UNAVAILABLE) from error
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PRODUCT_NOT_FOUND", "releaseId": baseline.release_id},
        )
    return schema.comparison(baseline, result)


@router.get("/source")
def get_source(request: Request) -> dict[str, object]:
    """The active release, its provenance and record counts (FR-008)."""

    service = _service(request)
    _baseline(service)
    summary = service.source_summary()
    if summary is None:
        raise HTTPException(status_code=503, detail=UNAVAILABLE)
    return schema.source_summary(summary)
