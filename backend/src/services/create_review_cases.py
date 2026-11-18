"""One NEW case per package change set and exactly matching simulated record."""

import hashlib
from collections.abc import Iterable
from datetime import UTC, datetime

from ..domain.case_status_event import CaseStatus, CaseStatusEvent
from ..domain.detected_change import PackageChangeSet
from ..domain.evidence import EvidenceClassification
from ..domain.review_case import ReviewCase, SimulatedMedicationRecord
from .match_detected_changes import MatchStatus, match_detected_changes


def create_review_cases(
    change_sets: tuple[PackageChangeSet, ...],
    records: tuple[SimulatedMedicationRecord, ...],
    *,
    created_at: datetime | None = None,
    existing_cases: Iterable[ReviewCase] = (),
) -> tuple[ReviewCase, ...]:
    """Create cases only for verified, unique (change set, record) pairs not yet stored.

    A change set covers every detected difference for one package between one
    ordered release pair, so a package update yields one case per matched record.
    """
    timestamp = created_at or datetime.now(UTC)
    cases = []

    seen_pairs = {
        (case.change_set.change_set_id, case.medication_record.record_id) for case in existing_cases
    }

    match_results = match_detected_changes(change_sets, records)

    for match_result in match_results:
        if (
            match_result.result is not MatchStatus.MATCHED
            or match_result.evidence_classification is not EvidenceClassification.VERIFIED
        ):
            continue

        change_set = match_result.change_set
        record = match_result.simulated_record_references[0]

        if sum(r.record_id == record.record_id for r in records) != 1:
            continue

        pair = (change_set.change_set_id, record.record_id)

        if pair in seen_pairs:
            continue

        seen_pairs.add(pair)

        key = hashlib.sha256(f"{change_set.change_set_id}:{record.record_id}".encode()).hexdigest()

        case_id = f"CASE-{key}"
        event = CaseStatusEvent(
            f"EVENT-{key}",
            case_id,
            None,
            CaseStatus.NEW,
            timestamp,
        )

        cases.append(
            ReviewCase(
                case_id,
                change_set,
                record,
                CaseStatus.NEW,
                timestamp,
                change_set.change_evidence_class,
                key,
                event,
            )
        )

    return tuple(cases)
