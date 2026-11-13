"""Exact package matching and initial NEW case creation for simulated records."""

import hashlib
from collections.abc import Iterable
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
    existing_cases: Iterable[ReviewCase] = (),
) -> tuple[ReviewCase, ...]:
    """Create cases only for change/record pairs absent from the supplied store."""
    timestamp = created_at or datetime.now(UTC)
    cases = []
    seen_pairs = {
        (case.change.change_id, case.medication_record.record_id) for case in existing_cases
    }
    for change in changes:
        if change.change_evidence_class is not EvidenceClassification.VERIFIED:
            continue
        matches = [r for r in records if r.package_identifier == change.medicine_key]
        if len(matches) != 1:
            continue
        record = matches[0]
        if sum(r.record_id == record.record_id for r in records) != 1:
            continue
        pair = (change.change_id, record.record_id)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        key = hashlib.sha256(f"{change.change_id}:{record.record_id}".encode()).hexdigest()
        case_id = f"CASE-{key}"
        event = CaseStatusEvent(f"EVENT-{key}", case_id, None, CaseStatus.NEW, timestamp)
        cases.append(
            ReviewCase(
                case_id,
                change,
                record,
                CaseStatus.NEW,
                timestamp,
                change.change_evidence_class,
                key,
                event,
            )
        )
    return tuple(cases)
