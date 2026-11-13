from dataclasses import replace
from datetime import UTC, datetime

from src.domain.evidence import EvidenceClassification
from src.services.create_review_cases import create_review_cases
from src.services.match_detected_changes import (
    MatchGranularity,
    MatchStatus,
    match_detected_changes,
)
from src.workflows.ingestion_to_review import run_ingestion_to_review


def test_unique_exact_match_creates_one_case_and_preserves_evidence(
    detected_change, medication_record
):
    (match_result,) = match_detected_changes((detected_change,), (medication_record,))
    cases = create_review_cases((detected_change,), (medication_record,))

    assert match_result.result is MatchStatus.MATCHED
    assert match_result.change == detected_change
    assert match_result.simulated_record_references == (medication_record,)
    assert match_result.compared_identifier == detected_change.medicine_key
    assert match_result.identifier_granularity is MatchGranularity.PACKAGE
    assert match_result.evidence_classification is EvidenceClassification.VERIFIED
    assert match_result.source_references == (
        detected_change.prior_evidence,
        detected_change.current_evidence,
    )
    assert len(cases) == 1
    case = cases[0]
    assert case.change == detected_change
    assert case.medication_record == medication_record
    assert case.evidence_class is detected_change.change_evidence_class
    assert case.evidence_class is EvidenceClassification.VERIFIED
    assert case.change.prior_evidence.classification is EvidenceClassification.VERIFIED
    assert (
        case.change.current_evidence.classification is EvidenceClassification.VERIFIED
    )
    assert (
        case.change.prior_evidence.source_record_identifier
        == detected_change.medicine_key
    )
    assert (
        case.change.current_evidence.source_record_identifier
        == detected_change.medicine_key
    )


def test_no_exact_package_match_creates_no_case(detected_change, medication_record):
    record_with_only_supporting_vnr = replace(
        medication_record,
        package_identifier="000123",
        supporting_package_reference=detected_change.medicine_key,
    )

    (match_result,) = match_detected_changes(
        (detected_change,), (record_with_only_supporting_vnr,)
    )

    assert match_result.result is MatchStatus.NO_MATCH
    assert match_result.simulated_record_references == ()
    assert (
        create_review_cases((detected_change,), (record_with_only_supporting_vnr,))
        == ()
    )


def test_multiple_exact_package_matches_create_no_case(
    detected_change, medication_record
):
    second_match = replace(medication_record, record_id="SIM-MED-101")
    (match_result,) = match_detected_changes(
        (detected_change,), (medication_record, second_match)
    )

    assert match_result.result is MatchStatus.AMBIGUOUS
    assert match_result.simulated_record_references == (medication_record, second_match)
    assert (
        create_review_cases((detected_change,), (medication_record, second_match)) == ()
    )


def test_replaying_change_does_not_duplicate_case_and_keeps_evidence(
    snapshot_pair, medication_record
):
    prior, current, order = snapshot_pair
    open_cases = []
    created_at = datetime(2099, 1, 3, tzinfo=UTC)

    first = run_ingestion_to_review(
        (prior,),
        (current,),
        (medication_record,),
        order=order,
        open_cases=open_cases,
        created_at=created_at,
    )
    replay = run_ingestion_to_review(
        (prior,),
        (current,),
        (medication_record,),
        order=order,
        open_cases=open_cases,
        created_at=created_at,
    )

    assert len(first.created_cases) == 1
    assert replay.created_cases == ()
    assert len(open_cases) == 1
    assert (
        replay.comparison.changes[0].change_id == first.comparison.changes[0].change_id
    )
    assert open_cases[0].case_id == first.created_cases[0].case_id
    assert open_cases[0].idempotency_key == first.created_cases[0].idempotency_key
    assert open_cases[0].evidence_class is EvidenceClassification.VERIFIED
    assert (
        open_cases[0].change.prior_evidence
        == first.comparison.changes[0].prior_evidence
    )
    assert (
        open_cases[0].change.current_evidence
        == first.comparison.changes[0].current_evidence
    )
