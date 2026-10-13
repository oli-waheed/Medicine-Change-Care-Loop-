"""Exact package matching and initial NEW case creation for simulated records."""

import hashlib
from datetime import UTC, datetime

from ..domain.case_status_event import CaseStatus, CaseStatusEvent
from ..domain.detected_change import DetectedChange
from ..domain.evidence import EvidenceClassification
from ..domain.review_case import ReviewCase, SimulatedMedicationRecord


def create_review_cases(
    changes: tuple[DetectedChange, ...],
    records: tuple[SimulatedMedicationRecord, ...],
    *,
    created_at: datetime | None = None,
) -> tuple[ReviewCase, ...]:
    timestamp = created_at or datetime.now(UTC)
    cases = []
    seen_pairs = set()
    for change in changes:
        if change.change_evidence_class is not EvidenceClassification.VERIFIED:
            continue
        matches = [r for r in records if r.package_identifier == change.medicine_key]
        if len(matches) != 1:
            continue
        record = matches[0]
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
