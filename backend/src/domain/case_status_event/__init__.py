"""Initial human-review status; no automated clinical transitions."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class CaseStatus(StrEnum):
    NEW = "NEW"


@dataclass(frozen=True, slots=True)
class CaseStatusEvent:
    event_id: str
    case_id: str
    from_status: CaseStatus | None
    to_status: CaseStatus
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not self.event_id or not self.case_id:
            raise ValueError("Event and case identities are required.")
        if self.from_status is not None or self.to_status is not CaseStatus.NEW:
            raise ValueError("This feature only creates an initial NEW event.")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("Event time must include a timezone.")
