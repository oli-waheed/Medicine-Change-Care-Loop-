"""Deterministic matching outcomes for detected package changes."""

from dataclasses import dataclass
from enum import StrEnum

from ..domain.detected_change import DetectedChange
from ..domain.evidence import EvidenceClassification, EvidenceProvenance
from ..domain.review_case import SimulatedMedicationRecord


class MatchStatus(StrEnum):
    MATCHED = "MATCHED"
    NO_MATCH = "NO_MATCH"
    AMBIGUOUS = "AMBIGUOUS"


class MatchGranularity(StrEnum):
    PACKAGE = "PACKAGE"


@dataclass(frozen=True, slots=True)
class MatchResult:
    change: DetectedChange
    simulated_record_references: tuple[SimulatedMedicationRecord, ...]
    compared_identifier: str
    identifier_granularity: MatchGranularity
    result: MatchStatus
    evidence_classification: EvidenceClassification
    source_references: tuple[EvidenceProvenance, EvidenceProvenance]

    def __post_init__(self) -> None:
        if not self.compared_identifier:
            raise ValueError("A compared identifier is required.")
        if self.result is MatchStatus.MATCHED and len(self.simulated_record_references) != 1:
            raise ValueError("A matched result requires exactly one simulated record.")
        if self.result is MatchStatus.NO_MATCH and self.simulated_record_references:
            raise ValueError("A no-match result cannot reference matching records.")
        if self.result is MatchStatus.AMBIGUOUS and len(self.simulated_record_references) < 2:
            raise ValueError("An ambiguous result requires multiple simulated records.")


def match_detected_changes(
    changes: tuple[DetectedChange, ...],
    records: tuple[SimulatedMedicationRecord, ...],
) -> tuple[MatchResult, ...]:
    """Match changes only against the exact package identifier."""
    results = []
    for change in changes:
        matching_records = tuple(
            record for record in records if record.package_identifier == change.medicine_key
        )
        if not matching_records:
            status = MatchStatus.NO_MATCH
        elif len(matching_records) == 1:
            status = MatchStatus.MATCHED
        else:
            status = MatchStatus.AMBIGUOUS
        results.append(
            MatchResult(
                change=change,
                simulated_record_references=matching_records,
                compared_identifier=change.medicine_key,
                identifier_granularity=MatchGranularity.PACKAGE,
                result=status,
                evidence_classification=change.change_evidence_class,
                source_references=(change.prior_evidence, change.current_evidence),
            )
        )
    return tuple(results)
