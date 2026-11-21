"""Case statuses and their recorded events.

The system only ever creates a case in NEW. Every later status is set by a
person (feature 007) and recorded as an event; nothing changes a status
automatically, and no event is ever edited or removed.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class CaseStatus(StrEnum):
    NEW = "NEW"
    # Feature 007: set only by a pharmacist reviewer.
    IN_PROGRESS = "IN_PROGRESS"
    REVIEWED_NO_ACTION = "REVIEWED_NO_ACTION"
    REVIEWED_FOLLOW_UP = "REVIEWED_FOLLOW_UP"


OPEN_STATUSES = frozenset({CaseStatus.NEW, CaseStatus.IN_PROGRESS})
REVIEWED_STATUSES = frozenset({CaseStatus.REVIEWED_NO_ACTION, CaseStatus.REVIEWED_FOLLOW_UP})

# FR-002: the only transitions a person can make.
HUMAN_TRANSITIONS: dict[CaseStatus, frozenset[CaseStatus]] = {
    CaseStatus.NEW: frozenset({CaseStatus.IN_PROGRESS, *REVIEWED_STATUSES}),
    CaseStatus.IN_PROGRESS: REVIEWED_STATUSES,
    CaseStatus.REVIEWED_NO_ACTION: frozenset({CaseStatus.IN_PROGRESS}),
    CaseStatus.REVIEWED_FOLLOW_UP: frozenset({CaseStatus.IN_PROGRESS}),
}

MAX_NOTE_LENGTH = 1000
_INITIALS = re.compile(r"[^\W\d_]{1,10}")


def note_required(from_status: CaseStatus, to_status: CaseStatus) -> bool:
    """A note is required for a Reviewed outcome and for reopening (FR-003)."""
    return to_status in REVIEWED_STATUSES or from_status in REVIEWED_STATUSES


@dataclass(frozen=True, slots=True)
class CaseStatusEvent:
    event_id: str
    case_id: str
    from_status: CaseStatus | None
    to_status: CaseStatus
    occurred_at: datetime
    reviewer_initials: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.event_id or not self.case_id:
            raise ValueError("Event and case identities are required.")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("Event time must include a timezone.")
        if self.from_status is None:
            # Created by the system: only the initial NEW event, without a reviewer.
            if self.to_status is not CaseStatus.NEW or self.reviewer_initials or self.note:
                raise ValueError("The system only creates an initial NEW event.")
            return
        if self.to_status not in HUMAN_TRANSITIONS[self.from_status]:
            raise ValueError(
                f"A case cannot move from {self.from_status.value} to {self.to_status.value}."
            )
        if not self.reviewer_initials or not _INITIALS.fullmatch(self.reviewer_initials):
            raise ValueError("Reviewer initials must be 1 to 10 letters.")
        note = (self.note or "").strip()
        if note_required(self.from_status, self.to_status) and not note:
            raise ValueError("A note is required for this review step.")
        if len(note) > MAX_NOTE_LENGTH:
            raise ValueError(f"The note can be at most {MAX_NOTE_LENGTH} characters.")
