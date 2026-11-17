"""Exact package matching and initial NEW case creation for simulated records."""

import hashlib
from datetime import UTC, datetime

from ..domain.case_status_event import CaseStatus, CaseStatusEvent
from ..domain.detected_change import DetectedChange
from ..domain.evidence import EvidenceClassification
from ..domain.review_case import ReviewCase, SimulatedMedicationRecord
from .match_detected_changes import MatchStatus, match_detected_changes


def create_review_cases(
    changes: tuple[DetectedChange, ...],
    records: tuple[SimulatedMedicationRecord, ...],
    *,
    created_at: datetime | None = None,
) -> tuple[ReviewCase, ...]:
    timestamp = created_at or datetime.now(UTC)
    cases = []
    seen_pairs = set()
    match_results = match_detected_changes(changes, records)
    for match_result in match_results:
        if (
            match_result.result is not MatchStatus.MATCHED
            or match_result.evidence_classification is not EvidenceClassification.VERIFIED
        ):
            continue
        change = match_result.change
        record = match_result.simulated_record_references[0]
        if sum(r.record_id == record.record_id for r in records) != 1:
            continue
        pair = hashlib.sha256(f"{change.change_id}:{record.record_id}".encode()).hexdigest()
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        case_id = f"CASE-{pair}"
        event = CaseStatusEvent(f"EVENT-{pair}", case_id, None, CaseStatus.NEW, timestamp)
        cases.append(
            ReviewCase(
                case_id,
                change,
                record,
                CaseStatus.NEW,
                timestamp,
                change.change_evidence_class,
                pair,
                event,
            )
        )
    return tuple(cases)
