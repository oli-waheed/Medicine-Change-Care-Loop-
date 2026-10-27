"""A traceable field difference between an explicitly ordered snapshot pair."""

from dataclasses import dataclass
from datetime import datetime

from ..evidence import EvidenceClassification, EvidenceProvenance
from ..medicine_snapshot import MedicineSnapshot
from ..source_field import SourceField


@dataclass(frozen=True, slots=True)
class DetectedChange:
    change_id: str
    medicine_key: str
    field_name: str
    prior_value: tuple[SourceField, ...]
    current_value: tuple[SourceField, ...]
    prior_snapshot: MedicineSnapshot
    current_snapshot: MedicineSnapshot
    prior_evidence: EvidenceProvenance
    current_evidence: EvidenceProvenance
    change_evidence_class: EvidenceClassification
    prior_source_order: int
    current_source_order: int
    source_order_basis: str
    detected_at: datetime

    def __post_init__(self) -> None:
        if not self.change_id or not self.field_name or not self.medicine_key:
            raise ValueError("Change identity, package key and field are required.")
        if (
            self.current_source_order <= self.prior_source_order
            or not self.source_order_basis.strip()
        ):
            raise ValueError("Changes require a supported increasing source order.")
        for snapshot, evidence in (
            (self.prior_snapshot, self.prior_evidence),
            (self.current_snapshot, self.current_evidence),
        ):
            if (
                evidence.source_release != snapshot.source_release
                or evidence.source_record_identifier != self.medicine_key
                or evidence.field_reference != self.field_name
            ):
                raise ValueError("Evidence must trace this exact snapshot, package and field.")
        if self.prior_value == self.current_value:
            raise ValueError("A detected change must contain different source values.")
        if any(
            s.pakkaustunnus != self.medicine_key
            for s in (self.prior_snapshot, self.current_snapshot)
        ):
            raise ValueError("Both snapshots must identify the same package.")
        if self.detected_at.tzinfo is None or self.detected_at.utcoffset() is None:
            raise ValueError("Detection time must include a timezone.")
