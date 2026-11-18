"""Record what happened to every detected package change set during matching.

Each change set gets exactly one outcome. Only a unique exact package match may
lead to a review case; NO_MATCH and AMBIGUOUS outcomes are kept so the
uncertainty stays visible instead of disappearing silently (FR-008, FR-015).
"""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from ..domain.detected_change import PackageChangeSet
from ..domain.review_case import ReviewCase, SimulatedMedicationRecord
from .match_detected_changes import MatchResult, MatchStatus, match_detected_changes


class OutcomeReason(StrEnum):
    UNIQUE_EXACT_PACKAGE_MATCH = "UNIQUE_EXACT_PACKAGE_MATCH"
    NO_SIMULATED_RECORD = "NO_SIMULATED_RECORD"
    MULTIPLE_SIMULATED_RECORDS = "MULTIPLE_SIMULATED_RECORDS"


_REASONS = {
    MatchStatus.MATCHED: OutcomeReason.UNIQUE_EXACT_PACKAGE_MATCH,
    MatchStatus.NO_MATCH: OutcomeReason.NO_SIMULATED_RECORD,
    MatchStatus.AMBIGUOUS: OutcomeReason.MULTIPLE_SIMULATED_RECORDS,
}


@dataclass(frozen=True, slots=True)
class ChangeProcessingOutcome:
    """The matching outcome for one package change set, and any case it led to."""

    outcome_id: str
    match: MatchResult
    reason: OutcomeReason
    case_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.outcome_id != self.match.change_set.change_set_id:
            raise ValueError("An outcome is identified by its change set.")
        if self.reason is not _REASONS[self.match.result]:
            raise ValueError("The outcome reason must agree with the match result.")
        if self.match.result is not MatchStatus.MATCHED and self.case_ids:
            raise ValueError("NO_MATCH and AMBIGUOUS outcomes never create a case.")
        if len(self.case_ids) > 1:
            raise ValueError("A change set yields at most one case per matched record.")

    @property
    def change_set(self) -> PackageChangeSet:
        return self.match.change_set

    @property
    def result(self) -> MatchStatus:
        return self.match.result


def build_change_processing_outcomes(
    change_sets: tuple[PackageChangeSet, ...],
    records: tuple[SimulatedMedicationRecord, ...],
    cases: Iterable[ReviewCase] = (),
) -> tuple[ChangeProcessingOutcome, ...]:
    """Return one outcome per change set, linking a MATCHED outcome to its case if any.

    ``cases`` are the review cases known after case creation (new and existing);
    a MATCHED outcome without a case (for example unverified evidence) keeps an
    empty ``case_ids`` rather than pretending a case exists.
    """
    case_ids_by_pair = {
        (case.change_set.change_set_id, case.medication_record.record_id): case.case_id
        for case in cases
    }
    outcomes = []
    for match in match_detected_changes(change_sets, records):
        case_ids: tuple[str, ...] = ()
        if match.result is MatchStatus.MATCHED:
            (record,) = match.simulated_record_references
            pair = (match.change_set.change_set_id, record.record_id)
            if pair in case_ids_by_pair:
                case_ids = (case_ids_by_pair[pair],)
        outcomes.append(
            ChangeProcessingOutcome(
                outcome_id=match.change_set.change_set_id,
                match=match,
                reason=_REASONS[match.result],
                case_ids=case_ids,
            )
        )
    return tuple(outcomes)
