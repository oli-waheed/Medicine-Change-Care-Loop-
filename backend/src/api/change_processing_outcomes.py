"""Read-only API exposing every matching outcome, including unmatched and ambiguous ones."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request

from ..services.match_detected_changes import MatchStatus
from ..services.pipeline_store import PipelineStore

router = APIRouter(prefix="/api/change-processing-outcomes", tags=["change-processing-outcomes"])


@router.get("")
def get_change_processing_outcomes(
    request: Request,
    result: Annotated[list[str] | None, Query()] = None,
) -> list[dict[str, object]]:
    """Return stored outcomes, optionally filtered, e.g. ``?result=NO_MATCH&result=AMBIGUOUS``.

    NO_MATCH and AMBIGUOUS outcomes never have a review case. This view reports
    what matching found; it does not create, change or close cases.
    """
    allowed = {status.value for status in MatchStatus}
    requested = set(result or ())
    unknown = sorted(requested - allowed)
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown result filter {unknown}; use one of {sorted(allowed)}.",
        )
    store: PipelineStore = request.app.state.store
    return store.processing_outcome_payloads(requested or None)
