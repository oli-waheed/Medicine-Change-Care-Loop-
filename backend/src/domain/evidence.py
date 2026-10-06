"""Source-linked evidence metadata, separate from clinical interpretation."""

from dataclasses import dataclass
from enum import StrEnum

from .source_field import SourceField
from .source_release import SourceRelease


class EvidenceClassification(StrEnum):
    VERIFIED = "VERIFIED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"


@dataclass(frozen=True, slots=True)
class EvidenceProvenance:
    """Classify evidence and link it to source records without asserting clinical meaning."""

    source_release: SourceRelease
    source_record_identifier: str
    classification: EvidenceClassification
    source_record_locator: str | None = None
    field_reference: str | None = None
    source_value: SourceField | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_release, SourceRelease):
            raise TypeError("Evidence provenance requires a SourceRelease.")
        if (
            not isinstance(self.source_record_identifier, str)
            or not self.source_record_identifier.strip()
        ):
            raise ValueError("A source record or package identifier is required.")
        if not isinstance(self.classification, EvidenceClassification):
            raise TypeError("Classification must be an EvidenceClassification.")
        for name, value in (
            ("source record locator", self.source_record_locator),
            ("field reference", self.field_reference),
            ("note", self.note),
        ):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name.capitalize()} must be non-empty when provided.")
        if self.source_value is not None and not isinstance(self.source_value, SourceField):
            raise TypeError("Source value must be a SourceField when provided.")
