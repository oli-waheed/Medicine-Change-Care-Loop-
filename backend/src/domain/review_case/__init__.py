"""Fictional medication record and supported human-review case."""

from dataclasses import dataclass
from datetime import datetime

from ..case_status_event import CaseStatus, CaseStatusEvent
from ..detected_change import DetectedChange
from ..evidence import EvidenceClassification


@dataclass(frozen=True, slots=True)
class SimulatedMedicationRecord:
    record_id: str
    person_reference: str
    medicine_display: str
    package_identifier: str | None = None
    supporting_package_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.record_id.startswith("SIM-") or not self.person_reference.startswith("SIM-"):
            raise ValueError("Only clearly simulated identifiers are supported.")
        if not self.medicine_display:
            raise ValueError("Fictional display information is required.")
        if self.package_identifier is not None and (
            not isinstance(self.package_identifier, str) or not self.package_identifier
        ):
            raise ValueError("Package identifier must be a non-empty string or None.")


@dataclass(frozen=True, slots=True)
class ReviewCase:
    case_id: str
    change: DetectedChange
    medication_record: SimulatedMedicationRecord
    status: CaseStatus
    created_at: datetime
    evidence_class: EvidenceClassification
    idempotency_key: str
    initial_event: CaseStatusEvent

    def __post_init__(self) -> None:
        if not self.case_id or not self.idempotency_key:
            raise ValueError("Case identity and pair identity are required.")
        if self.status is not CaseStatus.NEW:
            raise ValueError("New cases must begin in NEW.")
        if self.medication_record.package_identifier != self.change.medicine_key:
            raise ValueError("Case requires an exact package-level match.")
        if self.evidence_class is not self.change.change_evidence_class:
            raise ValueError("Case must preserve change evidence classification.")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("Creation time must include a timezone.")
        if (
            self.initial_event.case_id != self.case_id
            or self.initial_event.occurred_at != self.created_at
        ):
            raise ValueError("Initial event must refer to this case and creation time.")
