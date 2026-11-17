from dataclasses import replace

import pytest

from src.domain.case_status_event import CaseStatus
from src.domain.evidence import EvidenceClassification
from src.services.create_review_cases import create_review_cases


def test_unique_exact_match_creates_new_case_with_initial_event(change_set, medication_record):
    cases = create_review_cases((change_set,), (medication_record,))
    assert len(cases) == 1
    case = cases[0]
    assert case.status is CaseStatus.NEW
    assert case.change_set == change_set
    assert case.medication_record == medication_record
    assert case.initial_event.from_status is None
    assert case.initial_event.to_status is CaseStatus.NEW
    assert case.initial_event.case_id == case.case_id
    assert case.initial_event.occurred_at == case.created_at


@pytest.mark.parametrize("key", [None, "SIM-PKG-OTHER"])
def test_missing_or_different_primary_key_never_falls_back_to_vnr(
    change_set, medication_record, key
):
    assert (
        create_review_cases(
            (change_set,), (replace(medication_record, package_identifier=key),)
        )
        == ()
    )


def test_ambiguous_match_creates_no_case(change_set, medication_record):
    other = replace(medication_record, record_id="SIM-MED-101")
    assert create_review_cases((change_set,), (medication_record, other)) == ()


@pytest.mark.parametrize(
    "classification",
    [
        EvidenceClassification.UNKNOWN,
        EvidenceClassification.CONFLICTING,
        EvidenceClassification.INFERRED,
    ],
)
def test_unsupported_change_creates_no_case(change_set, medication_record, classification):
    # A change set may only hold field changes of its own classification.
    change = replace(
        change_set,
        change_evidence_class=classification,
        field_changes=tuple(
            replace(c, change_evidence_class=classification) for c in change_set.field_changes
        ),
    )
    assert create_review_cases((change,), (medication_record,)) == ()


def test_identity_is_deterministic(change_set, medication_record):
    a = create_review_cases((change_set,), (medication_record,))[0]
    b = create_review_cases((change_set,), (medication_record,))[0]
    assert a.case_id == b.case_id
    assert a.idempotency_key == b.idempotency_key


def test_duplicate_record_identity_is_rejected(change_set, medication_record):
    other = replace(medication_record, package_identifier="SIM-PKG-OTHER")
    assert create_review_cases((change_set,), (medication_record, other)) == ()


def test_replay_skips_existing_pair_but_creates_new_pair(change_set, medication_record):
    original = create_review_cases((change_set,), (medication_record,))[0]
    existing_cases = [original]
    new_change = replace(change_set, change_set_id=f"{change_set.change_set_id}-next")

    created = create_review_cases(
        (change_set, new_change, new_change),
        (medication_record,),
        existing_cases=existing_cases,
    )

    assert [case.change_set for case in created] == [new_change]
    assert existing_cases == [original]


def test_invalid_case_event_or_classification_is_rejected(change_set, medication_record):
    case = create_review_cases((change_set,), (medication_record,))[0]
    with pytest.raises(ValueError):
        replace(case, initial_event=replace(case.initial_event, case_id="OTHER"))
    with pytest.raises(ValueError):
        replace(case, evidence_class=EvidenceClassification.UNKNOWN)


def test_one_package_update_with_several_fields_creates_one_case(
    snapshot_pair, medication_record
):
    from src.domain.source_field import SourceField
    from src.services.detect_relevant_changes import detect_relevant_changes

    old, new, order = snapshot_pair
    new = replace(
        new,
        package=replace(new.package, julkinen_tarkenne=SourceField.of("SIM changed")),
    )
    comparison = detect_relevant_changes((old,), (new,), order=order)

    cases = create_review_cases(comparison.change_sets, (medication_record,))

    assert len(comparison.changes) >= 2
    assert len(cases) == 1
    assert {c.field_name for c in cases[0].change_set.field_changes} == {
        c.field_name for c in comparison.changes
    }


def test_no_longer_present_package_creates_a_case_with_prior_evidence(
    snapshot_pair, medication_record
):
    from src.domain.detected_change import PackageChangeKind
    from src.services.detect_relevant_changes import detect_relevant_changes

    old, new, order = snapshot_pair
    other = replace(new, pakkaustunnus="SIM-PKG-OTHER")
    comparison = detect_relevant_changes((old,), (other,), order=order)

    (case,) = create_review_cases(comparison.change_sets, (medication_record,))

    assert case.change_set.kind is PackageChangeKind.NO_LONGER_PRESENT
    assert case.change_set.field_changes == ()
    assert case.change_set.prior_snapshot == old
    assert case.change_set.current_snapshot is None
    assert case.change_set.current_evidence.source_release == order.current_release
    assert case.change_set.current_evidence.source_record_locator is None
    assert "SIM-PKG-OTHER: newly present" in " ".join(comparison.notes)
