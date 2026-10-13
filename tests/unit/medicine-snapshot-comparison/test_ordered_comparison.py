from dataclasses import replace

import pytest
from src.domain.evidence import EvidenceClassification
from src.domain.source_field import SourceField
from src.services.detect_relevant_changes import detect_relevant_changes


def test_changed_name_retains_both_snapshots_and_source_evidence(snapshot_pair):
    old, new, order = snapshot_pair
    change = detect_relevant_changes((old,), (new,), order=order).changes[0]
    assert change.field_name == "Laakevalmiste/Kauppanimi"
    assert change.prior_value[0].value == "Fictional Alpha"
    assert change.current_value[0].value == "Fictional Alpha Updated"
    assert change.prior_snapshot == old and change.current_snapshot == new
    assert change.current_evidence.source_release == new.source_release
    assert change.current_evidence.source_record_locator == new.source_record_locator
    assert (
        change.change_id
        == detect_relevant_changes((old,), (new,), order=order).changes[0].change_id
    )


def test_unchanged_fields_and_metadata_do_not_trigger(snapshot_pair):
    old, new, order = snapshot_pair
    new = replace(new, product=old.product, vnr_numero=SourceField.of("OTHER"))
    assert detect_relevant_changes((old,), (new,), order=order).changes == ()


@pytest.mark.parametrize("kind", ["missing", "unknown", "conflicting", "reversed", "same"])
def test_unsupported_order_produces_no_verified_changes(snapshot_pair, kind):
    old, new, order = snapshot_pair
    if kind == "missing":
        order = None
    elif kind == "unknown":
        order = replace(order, classification=EvidenceClassification.UNKNOWN)
    elif kind == "conflicting":
        order = replace(order, classification=EvidenceClassification.CONFLICTING)
    elif kind == "reversed":
        order = replace(order, current_order=0)
    else:
        order = replace(order, current_order=1)
    result = detect_relevant_changes((old,), (new,), order=order)
    assert result.changes == ()
    assert result.classification is not EvidenceClassification.VERIFIED


def test_baseline_and_unpaired_packages_do_not_create_changes(snapshot_pair):
    old, new, order = snapshot_pair
    assert detect_relevant_changes((), (new,), order=None).changes == ()
    assert (
        detect_relevant_changes((old,), (replace(new, pakkaustunnus="OTHER"),), order=order).changes
        == ()
    )
    assert detect_relevant_changes((old, old), (new,), order=order).changes == ()


def test_empty_missing_and_attributes_are_preserved(snapshot_pair):
    old, new, order = snapshot_pair
    new = replace(
        new,
        product=old.product,
        package=replace(new.package, julkinen_tarkenne=SourceField.missing()),
    )
    change = detect_relevant_changes((old,), (new,), order=order).changes[0]
    assert change.prior_value == (SourceField.empty(),)
    assert change.current_value == (SourceField.missing(),)
    new = replace(
        new,
        product=replace(
            old.product, laakemuoto=SourceField.of("tablet", attributes=(("id", "2"),))
        ),
        package=old.package,
    )
    assert (
        detect_relevant_changes((old,), (new,), order=order).changes[0].field_name
        == "Laakevalmiste/Laakemuoto"
    )


def test_repeated_source_order_is_preserved(snapshot_pair):
    old, new, order = snapshot_pair
    old = replace(
        old,
        product=replace(old.product, antoreitti=(SourceField.of("a"), SourceField.of("b"))),
    )
    new = replace(
        new,
        product=replace(old.product, antoreitti=(SourceField.of("b"), SourceField.of("a"))),
    )
    assert (
        detect_relevant_changes((old,), (new,), order=order).changes[0].field_name
        == "Laakevalmiste/Antoreitti"
    )


def test_snapshot_release_mismatch_is_not_verified(snapshot_pair):
    old, new, order = snapshot_pair
    result = detect_relevant_changes(
        (old,), (replace(new, source_release=old.source_release),), order=order
    )
    assert result.changes == () and result.classification is EvidenceClassification.CONFLICTING


@pytest.mark.parametrize("area", ["active", "availability", "authorization", "package"])
def test_all_relevant_groups_are_compared(snapshot_pair, area):
    old, new, order = snapshot_pair
    new = replace(new, product=old.product)
    if area == "active":
        new = replace(
            new,
            active_substances=(replace(old.active_substances[0], maara=SourceField.of("20")),),
        )
    elif area == "availability":
        new = replace(
            new,
            package=replace(
                old.package,
                availability=replace(old.package.availability, kaupan=SourceField.of("0")),
            ),
        )
    elif area == "authorization":
        new = replace(
            new,
            authorizations=(replace(old.authorizations[0], tila=SourceField.of("ended")),),
        )
    else:
        new = replace(new, package=replace(old.package, pakkauskoko=SourceField.of("30")))
    assert len(detect_relevant_changes((old,), (new,), order=order).changes) == 1
