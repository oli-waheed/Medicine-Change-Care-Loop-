"""Read-only API for pharmacist review of NEW cases."""

from fastapi import APIRouter, Request

from ..schemas.open_review_cases import with_evidence_availability
from ..services.pipeline_store import PipelineStore

router = APIRouter(prefix="/api/open-review-cases", tags=["open-review-cases"])


@router.get("")
def get_open_review_cases(request: Request) -> list[dict[str, object]]:
    """Return persisted NEW cases with their change, simulated match, and source evidence.

    Each source also reports whether its raw capture file is still stored
    (``evidenceAvailable``), and each case whether all its evidence is
    (``evidenceAvailability``).
    """
    store: PipelineStore = request.app.state.store
    available = store.available_file_checksums()
    return [with_evidence_availability(case, available) for case in store.open_case_payloads()]
