"""Read API for pharmacist review of cases."""

from fastapi import APIRouter, Query, Request

from ..schemas.open_review_cases import with_evidence_availability
from ..services.pipeline_store import PipelineStore

router = APIRouter(prefix="/api/open-review-cases", tags=["open-review-cases"])


@router.get("")
def get_open_review_cases(
    request: Request, include_reviewed: bool = Query(False, alias="includeReviewed")
) -> list[dict[str, object]]:
    """Return cases to review (NEW and IN_PROGRESS) with their change, match and evidence.

    With ``includeReviewed=true`` reviewed cases are included too (feature 007).
    Every case carries its current ``status`` and its ``statusHistory``.

    Each source also reports whether its raw capture file is still stored
    (``evidenceAvailable``), and each case whether all its evidence is
    (``evidenceAvailability``).
    """
    store: PipelineStore = request.app.state.store
    available = store.available_file_checksums()
    return [
        with_evidence_availability(case, available)
        for case in store.case_payloads(include_reviewed=include_reviewed)
    ]
