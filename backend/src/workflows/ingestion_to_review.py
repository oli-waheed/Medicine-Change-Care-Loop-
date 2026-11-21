"""Connect complete source-release ingestion to the pharmacist review workflow."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..domain.evidence import EvidenceClassification
from ..domain.medicine_snapshot import MedicineSnapshot
from ..domain.review_case import ReviewCase, SimulatedMedicationRecord
from ..services.change_processing_outcomes import (
    ChangeProcessingOutcome,
    build_change_processing_outcomes,
)
from ..services.create_review_cases import create_review_cases
from ..services.detect_relevant_changes import (
    ComparisonResult,
    SourceOrderEvidence,
    detect_relevant_changes,
)
from ..services.ingest_source_release import (
    SOURCE_ORDER_BASIS,
    IngestionOutcome,
    ProcessingStatus,
    ingest_source_release,
    source_order_key,
)


@dataclass(frozen=True, slots=True)
class IngestionToReviewResult:
    comparison: ComparisonResult
    created_cases: tuple[ReviewCase, ...]
    # One matching outcome per detected change set (MATCHED, NO_MATCH, AMBIGUOUS).
    outcomes: tuple[ChangeProcessingOutcome, ...] = ()


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
    created = create_review_cases(
        comparison.change_sets,
        medication_records,
        created_at=created_at,
        existing_cases=open_cases,
    )
    open_cases.extend(created)
    outcomes = build_change_processing_outcomes(
        comparison.change_sets, medication_records, open_cases
    )

    return IngestionToReviewResult(comparison, created, outcomes)


def source_order_evidence(
    prior: IngestionOutcome, current: IngestionOutcome
) -> SourceOrderEvidence | None:
    """Verified order of two releases from their own Ajopvm, or None when unknown."""
    prior_key = source_order_key(prior.source_order)
    current_key = source_order_key(current.source_order)
    if prior_key is None or current_key is None:
        return None
    return SourceOrderEvidence(
        prior_release=prior.source_release,
        current_release=current.source_release,
        prior_order=prior_key,
        current_order=current_key,
        classification=EvidenceClassification.VERIFIED,
        basis=(
            f"{SOURCE_ORDER_BASIS} Prior Ajopvm {prior.source_order.value}; "
            f"current Ajopvm {current.source_order.value}."
        ),
    )


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
            raise ValueError(f"{label} source release ingestion failed: {outcome.failure_detail}")

    if prior.source_release is None or current.source_release is None:
        raise ValueError("Comparison requires exactly one normalized source file per release.")

    return run_ingestion_to_review(
        prior.snapshots,
        current.snapshots,
        medication_records,
        order=source_order_evidence(prior, current),
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
