"""Feature 007: a pharmacist records a review step on a case.

The only operation that changes a case. It is always a person's action with
their initials (and a note where required); the system itself never changes a
status. Every step is kept as an event and never edited.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..domain.case_status_event import HUMAN_TRANSITIONS, CaseStatus, CaseStatusEvent
from ..schemas.open_review_cases import with_evidence_availability
from ..services.pipeline_store import CaseTransitionError, PipelineStore

router = APIRouter(prefix="/api/review-cases", tags=["review-cases"])


class StatusChange(BaseModel):
    expected_status: CaseStatus = Field(alias="expectedStatus")
    to_status: CaseStatus = Field(alias="toStatus")
    reviewer_initials: str = Field(alias="reviewerInitials")
    note: str | None = None


@router.post("/{case_id}/status-events", status_code=status.HTTP_201_CREATED)
def record_status_event(case_id: str, change: StatusChange, request: Request) -> dict:
    store: PipelineStore = request.app.state.store
    if change.to_status not in HUMAN_TRANSITIONS[change.expected_status]:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "TRANSITION_NOT_ALLOWED",
                "message": (
                    f"A case cannot move from {change.expected_status.value} "
                    f"to {change.to_status.value}."
                ),
            },
        )
    try:
        event = CaseStatusEvent(
            event_id=f"EVENT-{uuid.uuid4().hex}",
            case_id=case_id,
            from_status=change.expected_status,
            to_status=change.to_status,
            occurred_at=datetime.now(UTC),
            reviewer_initials=change.reviewer_initials.strip(),
            note=change.note,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422, detail={"code": "INVALID_REVIEW_STEP", "message": str(error)}
        ) from error
    try:
        store.record_status_event(event)
    except CaseTransitionError as error:
        raise HTTPException(
            status_code=404 if error.code == "CASE_NOT_FOUND" else 409,
            detail={
                "code": error.code,
                "message": str(error),
                "currentStatus": error.current_status,
            },
        ) from error
    return with_evidence_availability(store.case_payload(case_id), store.available_file_checksums())
