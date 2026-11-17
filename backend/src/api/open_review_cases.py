"""Read-only API for pharmacist review of NEW cases."""

from fastapi import APIRouter, Request

from ..services.pipeline_store import PipelineStore

router = APIRouter(prefix="/api/open-review-cases", tags=["open-review-cases"])


@router.get("")
def get_open_review_cases(request: Request) -> list[dict[str, object]]:
    """Return persisted NEW cases with their change, simulated match, and source evidence."""
    store: PipelineStore = request.app.state.store
    return store.open_case_payloads()
