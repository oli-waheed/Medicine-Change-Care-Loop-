"""A traceable field difference between an explicitly ordered snapshot pair."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

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


class PackageChangeKind(StrEnum):
    """What happened to one package between two ordered releases."""

    FIELDS_CHANGED = "FIELDS_CHANGED"
    NO_LONGER_PRESENT = "NO_LONGER_PRESENT"


@dataclass(frozen=True, slots=True)
class PackageChangeSet:
    """All detected source differences for one package between two ordered releases.

    FIELDS_CHANGED groups one or more field changes. NO_LONGER_PRESENT means the
    prior release had exactly one Pakkaus with this Pakkaustunnus and the current
    full-coverage release has none; it is a source-data difference only and does
    not say why (withdrawal, renumbering or source error are not distinguished).
    """

    change_set_id: str
    medicine_key: str
    kind: PackageChangeKind
    field_changes: tuple[DetectedChange, ...]
    prior_snapshot: MedicineSnapshot
    current_snapshot: MedicineSnapshot | None
    prior_evidence: EvidenceProvenance
    current_evidence: EvidenceProvenance
    change_evidence_class: EvidenceClassification
    prior_source_order: int
    current_source_order: int
    source_order_basis: str
    detected_at: datetime

    def __post_init__(self) -> None:
        if not self.change_set_id or not self.medicine_key:
            raise ValueError("Change set identity and package key are required.")
        if (
            self.current_source_order <= self.prior_source_order
            or not self.source_order_basis.strip()
        ):
            raise ValueError("Change sets require a supported increasing source order.")
        if self.prior_snapshot.pakkaustunnus != self.medicine_key:
            raise ValueError("The prior snapshot must identify this package.")
        if self.prior_evidence.source_release != self.prior_snapshot.source_release:
            raise ValueError("Prior evidence must trace the prior snapshot's release.")
        for evidence in (self.prior_evidence, self.current_evidence):
            if evidence.source_record_identifier != self.medicine_key:
                raise ValueError("Evidence must trace this package.")
        if self.kind is PackageChangeKind.FIELDS_CHANGED:
            if not self.field_changes or self.current_snapshot is None:
                raise ValueError("A field change set needs field changes and both snapshots.")
            if self.current_snapshot.pakkaustunnus != self.medicine_key:
                raise ValueError("The current snapshot must identify this package.")
            if self.current_evidence.source_release != self.current_snapshot.source_release:
                raise ValueError("Current evidence must trace the current snapshot's release.")
            for change in self.field_changes:
                if (
                    change.medicine_key != self.medicine_key
                    or change.prior_snapshot != self.prior_snapshot
                    or change.current_snapshot != self.current_snapshot
                    or change.change_evidence_class is not self.change_evidence_class
                ):
                    raise ValueError("Every field change must belong to this package pair.")
            if len({change.field_name for change in self.field_changes}) != len(
                self.field_changes
            ):
                raise ValueError("A field may appear only once in a change set.")
        else:
            if self.field_changes or self.current_snapshot is not None:
                raise ValueError("A no-longer-present change set has no current record.")
            if self.current_evidence.source_record_locator is not None:
                raise ValueError("An absent record cannot have a source locator.")
        if self.detected_at.tzinfo is None or self.detected_at.utcoffset() is None:
            raise ValueError("Detection time must include a timezone.")
