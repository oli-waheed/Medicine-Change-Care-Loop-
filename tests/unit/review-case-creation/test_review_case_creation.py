from dataclasses import replace

import pytest
from src.domain.case_status_event import CaseStatus
from src.domain.evidence import EvidenceClassification
from src.services.create_review_cases import create_review_cases


def test_unique_exact_match_creates_new_case_with_initial_event(detected_change, medication_record):
    cases = create_review_cases((detected_change,), (medication_record,))
    assert len(cases) == 1
    case = cases[0]
    assert case.status is CaseStatus.NEW
    assert case.change == detected_change
    assert case.medication_record == medication_record
    assert case.initial_event.from_status is None
    assert case.initial_event.to_status is CaseStatus.NEW
    assert case.initial_event.case_id == case.case_id
    assert case.initial_event.occurred_at == case.created_at


@pytest.mark.parametrize("key", [None, "SIM-PKG-OTHER"])
def test_missing_or_different_primary_key_never_falls_back_to_vnr(
    detected_change, medication_record, key
):
    assert (
        create_review_cases(
            (detected_change,), (replace(medication_record, package_identifier=key),)
        )
        == ()
    )


def test_ambiguous_match_creates_no_case(detected_change, medication_record):
    other = replace(medication_record, record_id="SIM-MED-101")
    assert create_review_cases((detected_change,), (medication_record, other)) == ()


@pytest.mark.parametrize(
    "classification",
    [
        EvidenceClassification.UNKNOWN,
        EvidenceClassification.CONFLICTING,
        EvidenceClassification.INFERRED,
    ],
)
def test_unsupported_change_creates_no_case(detected_change, medication_record, classification):
    change = replace(detected_change, change_evidence_class=classification)
    assert create_review_cases((change,), (medication_record,)) == ()


def test_identity_is_deterministic(detected_change, medication_record):
    a = create_review_cases((detected_change,), (medication_record,))[0]
    b = create_review_cases((detected_change,), (medication_record,))[0]
    assert a.case_id == b.case_id
    assert a.idempotency_key == b.idempotency_key


def test_duplicate_record_identity_is_rejected(detected_change, medication_record):
    other = replace(medication_record, package_identifier="SIM-PKG-OTHER")
    assert create_review_cases((detected_change,), (medication_record, other)) == ()


def test_invalid_case_event_or_classification_is_rejected(detected_change, medication_record):
    case = create_review_cases((detected_change,), (medication_record,))[0]
    with pytest.raises(ValueError):
        replace(case, initial_event=replace(case.initial_event, case_id="OTHER"))
    with pytest.raises(ValueError):
        replace(case, evidence_class=EvidenceClassification.UNKNOWN)
