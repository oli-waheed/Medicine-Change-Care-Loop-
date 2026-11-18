from dataclasses import replace

import pytest

from src.domain.evidence import EvidenceClassification
from src.services.change_processing_outcomes import (
    ChangeProcessingOutcome,
    OutcomeReason,
    build_change_processing_outcomes,
)
from src.services.create_review_cases import create_review_cases
from src.services.match_detected_changes import MatchStatus


def test_unique_match_outcome_links_the_created_case(change_set, medication_record):
    cases = create_review_cases((change_set,), (medication_record,))

    (outcome,) = build_change_processing_outcomes((change_set,), (medication_record,), cases)

    assert outcome.result is MatchStatus.MATCHED
    assert outcome.reason is OutcomeReason.UNIQUE_EXACT_PACKAGE_MATCH
    assert outcome.outcome_id == change_set.change_set_id
    assert outcome.case_ids == (cases[0].case_id,)


def test_no_match_outcome_is_kept_without_a_case(change_set, medication_record):
    other = replace(medication_record, package_identifier="SIM-PKG-OTHER")

    (outcome,) = build_change_processing_outcomes((change_set,), (other,))

    assert outcome.result is MatchStatus.NO_MATCH
    assert outcome.reason is OutcomeReason.NO_SIMULATED_RECORD
    assert outcome.match.simulated_record_references == ()
    assert outcome.case_ids == ()


def test_ambiguous_outcome_lists_every_candidate_record_without_a_case(
    change_set, medication_record
):
    second = replace(medication_record, record_id="SIM-MED-101")
    records = (medication_record, second)

    (outcome,) = build_change_processing_outcomes(
        (change_set,), records, create_review_cases((change_set,), records)
    )

    assert outcome.result is MatchStatus.AMBIGUOUS
    assert outcome.reason is OutcomeReason.MULTIPLE_SIMULATED_RECORDS
    assert outcome.match.simulated_record_references == records
    assert outcome.case_ids == ()


def test_matched_outcome_without_a_case_does_not_invent_one(change_set, medication_record):
    (outcome,) = build_change_processing_outcomes((change_set,), (medication_record,), ())

    assert outcome.result is MatchStatus.MATCHED
    assert outcome.case_ids == ()


def test_outcomes_keep_the_change_evidence_classification(change_set, medication_record):
    (outcome,) = build_change_processing_outcomes((change_set,), (medication_record,))

    assert outcome.match.evidence_classification is EvidenceClassification.VERIFIED
    assert outcome.match.source_references == (
        change_set.prior_evidence,
        change_set.current_evidence,
    )


def test_outcome_identity_is_deterministic(change_set, medication_record):
    first = build_change_processing_outcomes((change_set,), (medication_record,))
    second = build_change_processing_outcomes((change_set,), (medication_record,))

    assert first == second


def test_no_match_or_ambiguous_outcome_cannot_claim_a_case(change_set, medication_record):
    other = replace(medication_record, package_identifier="SIM-PKG-OTHER")
    (outcome,) = build_change_processing_outcomes((change_set,), (other,))

    with pytest.raises(ValueError):
        replace(outcome, case_ids=("CASE-X",))
    with pytest.raises(ValueError):
        replace(outcome, reason=OutcomeReason.UNIQUE_EXACT_PACKAGE_MATCH)
    with pytest.raises(ValueError):
        ChangeProcessingOutcome("OTHER-ID", outcome.match, outcome.reason, ())
