"""Connect ordered normalized snapshots to the pharmacist open-case read view."""

from dataclasses import dataclass
from datetime import datetime

from ..domain.medicine_snapshot import MedicineSnapshot
from ..domain.review_case import ReviewCase, SimulatedMedicationRecord
from ..services.create_review_cases import create_review_cases
from ..services.detect_relevant_changes import (
    ComparisonResult,
    SourceOrderEvidence,
    detect_relevant_changes,
)


@dataclass(frozen=True, slots=True)
class IngestionToReviewResult:
    comparison: ComparisonResult
    created_cases: tuple[ReviewCase, ...]


def run_ingestion_to_review(
    prior_snapshots: tuple[MedicineSnapshot, ...],
    current_snapshots: tuple[MedicineSnapshot, ...],
    medication_records: tuple[SimulatedMedicationRecord, ...],
    *,
    order: SourceOrderEvidence | None,
    open_cases: list[ReviewCase],
    created_at: datetime | None = None,
) -> IngestionToReviewResult:
    """Compare snapshots and add only newly created exact-match cases to the read store."""
    comparison = detect_relevant_changes(prior_snapshots, current_snapshots, order=order)
    candidates = create_review_cases(
        comparison.changes, medication_records, created_at=created_at
    )
    known_ids = {case.case_id for case in open_cases}
    created = tuple(case for case in candidates if case.case_id not in known_ids)
    open_cases.extend(created)
    return IngestionToReviewResult(comparison, created)
