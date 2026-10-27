"""Read-only API for pharmacist review of NEW cases."""

from fastapi import APIRouter, Request

from ..domain.case_status_event import CaseStatus
from ..domain.review_case import ReviewCase
from ..schemas.open_review_cases import open_review_case_payload

router = APIRouter(prefix="/api/open-review-cases", tags=["open-review-cases"])


@router.get("")
def get_open_review_cases(request: Request) -> list[dict[str, object]]:
    """Return NEW cases with their change, simulated match, and source evidence."""
    cases: list[ReviewCase] = request.app.state.open_review_cases
    return [
        open_review_case_payload(case) for case in cases if case.status is CaseStatus.NEW
    ]
