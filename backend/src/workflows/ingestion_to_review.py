"""Connect complete source-release ingestion to the pharmacist review workflow."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..domain.evidence import EvidenceClassification
from ..domain.medicine_snapshot import MedicineSnapshot
from ..domain.review_case import ReviewCase, SimulatedMedicationRecord
from ..services.create_review_cases import create_review_cases
from ..services.detect_relevant_changes import (
    ComparisonResult,
    SourceOrderEvidence,
    detect_relevant_changes,
)
from ..services.ingest_source_release import (
    IngestionOutcome,
    ProcessingStatus,
    ingest_source_release,
)


@dataclass(frozen=True, slots=True)
class IngestionToReviewResult:
    comparison: ComparisonResult
    created_cases: tuple[ReviewCase, ...]


@dataclass(frozen=True, slots=True)
class ReleaseIngestionToReviewResult:
    prior_ingestion: IngestionOutcome
    current_ingestion: IngestionOutcome
    workflow_result: IngestionToReviewResult


def run_ingestion_to_review(
    prior_snapshots: tuple[MedicineSnapshot, ...],
    current_snapshots: tuple[MedicineSnapshot, ...],
    medication_records: tuple[SimulatedMedicationRecord, ...],
    *,
    order: SourceOrderEvidence | None,
    open_cases: list[ReviewCase],
    created_at: datetime | None = None,
) -> IngestionToReviewResult:
    """Compare snapshots and add only newly created exact-match cases."""
    comparison = detect_relevant_changes(
        prior_snapshots,
        current_snapshots,
        order=order,
    )
    candidates = create_review_cases(
        comparison.changes,
        medication_records,
        created_at=created_at,
    )

    known_ids = {case.case_id for case in open_cases}
    created = tuple(
        case for case in candidates if case.case_id not in known_ids
    )
    open_cases.extend(created)

    return IngestionToReviewResult(comparison, created)


def run_ingested_release_to_review(
    prior: IngestionOutcome,
    current: IngestionOutcome,
    medication_records: tuple[SimulatedMedicationRecord, ...],
    *,
    open_cases: list[ReviewCase],
    created_at: datetime | None = None,
) -> IngestionToReviewResult:
    """Compare two already captured and normalized releases."""
    for label, outcome in (("Prior", prior), ("Current", current)):
        if outcome.processing_status is not ProcessingStatus.VALIDATED:
            raise ValueError(
                f"{label} source release ingestion failed: {outcome.failure_detail}"
            )

    if prior.source_release is None or current.source_release is None:
        raise ValueError(
            "Comparison requires exactly one normalized source file per release."
        )

    order = None
    prior_order = prior.source_order
    current_order = current.source_order

    if (
        prior_order.evidence_class is EvidenceClassification.VERIFIED
        and current_order.evidence_class is EvidenceClassification.VERIFIED
        and prior_order.value is not None
        and current_order.value is not None
    ):
        try:
            prior_number = int(prior_order.value.strip())
            current_number = int(current_order.value.strip())
        except ValueError:
            pass
        else:
            order = SourceOrderEvidence(
                prior_release=prior.source_release,
                current_release=current.source_release,
                prior_order=prior_number,
                current_order=current_number,
                classification=EvidenceClassification.VERIFIED,
                basis=(
                    "Explicit VERIFIED sourceOrder values supplied with the release "
                    "payloads. Retrieval timestamps were not used."
                ),
            )

    return run_ingestion_to_review(
        prior.snapshots,
        current.snapshots,
        medication_records,
        order=order,
        open_cases=open_cases,
        created_at=created_at,
    )


def run_release_ingestion_to_review(
    prior_payload: dict,
    current_payload: dict,
    medication_records: tuple[SimulatedMedicationRecord, ...],
    *,
    storage_dir: str | Path,
    open_cases: list[ReviewCase],
    created_at: datetime | None = None,
) -> ReleaseIngestionToReviewResult:
    """Capture, normalize, compare and create supported human-review cases."""
    prior = ingest_source_release(
        prior_payload,
        storage_dir=storage_dir,
    )
    current = ingest_source_release(
        current_payload,
        storage_dir=storage_dir,
    )

    workflow_result = run_ingested_release_to_review(
        prior,
        current,
        medication_records,
        open_cases=open_cases,
        created_at=created_at,
    )

    return ReleaseIngestionToReviewResult(
        prior_ingestion=prior,
        current_ingestion=current,
        workflow_result=workflow_result,
    )