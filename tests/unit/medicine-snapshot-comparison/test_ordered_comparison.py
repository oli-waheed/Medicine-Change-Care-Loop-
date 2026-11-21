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
    new = replace(new, product=old.product, product_reference=SourceField.of("OTHER"))
    assert detect_relevant_changes((old,), (new,), order=order).changes == ()


@pytest.mark.parametrize(
    ("before", "after"),
    [("072811", "192152"), (None, "192152"), ("072811", None)],
)
def test_vnr_change_is_detected(snapshot_pair, before, after):
    """Decision T018 (2026-11-21): VNR changed, gained or lost is a change."""
    old, new, order = snapshot_pair

    def vnr(value):
        return SourceField.missing() if value is None else SourceField.of(value)

    old = replace(old, vnr_numero=vnr(before))
    new = replace(new, product=old.product, vnr_numero=vnr(after))
    (change,) = detect_relevant_changes((old,), (new,), order=order).changes
    assert change.field_name == "Pakkaus/VNR-numero"
    assert change.prior_value == (vnr(before),)
    assert change.current_value == (vnr(after),)


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


def _substance(code, amount, *, cas=None):
    from src.domain.medicine_snapshot import ActiveSubstanceFields

    return ActiveSubstanceFields(
        SourceField.empty(attributes=(("listname", "SIM-SUBSTANCE"), ("id", code))),
        SourceField.of(cas or f"SIM-CAS-{code}"),
        SourceField.of(amount),
        SourceField.empty(attributes=(("id", "mg"),)),
        SourceField.of(f"{amount} mg"),
    )


def _with_substances(snapshot, *substances):
    return replace(snapshot, active_substances=substances)


def test_reordered_substances_are_paired_by_aine_code_not_position(snapshot_pair):
    old, new, order = snapshot_pair
    new = replace(new, product=old.product)
    a, b = _substance("SIM-SA", "10"), _substance("SIM-SB", "20")

    result = detect_relevant_changes(
        (_with_substances(old, a, b),), (_with_substances(new, b, a),), order=order
    )

    assert result.changes == ()


def test_changed_substance_amount_is_reported_against_the_same_substance(snapshot_pair):
    old, new, order = snapshot_pair
    new = replace(new, product=old.product)

    changes = detect_relevant_changes(
        (_with_substances(old, _substance("SIM-SA", "10"), _substance("SIM-SB", "20")),),
        (_with_substances(new, _substance("SIM-SB", "20"), _substance("SIM-SA", "15")),),
        order=order,
    ).changes

    assert {change.field_name for change in changes} == {
        "Laakeaine/VaikuttavaAine[Aine=SIM-SA]/Maara",
        "Laakeaine/VaikuttavaAine[Aine=SIM-SA]/JakamatonVahvuus",
    }
    amount = next(c for c in changes if c.field_name.endswith("/Maara"))
    assert (amount.prior_value[0].value, amount.current_value[0].value) == ("10", "15")


def test_added_substance_is_reported_as_newly_present(snapshot_pair):
    old, new, order = snapshot_pair
    new = replace(new, product=old.product)

    changes = detect_relevant_changes(
        (_with_substances(old, _substance("SIM-SA", "10")),),
        (_with_substances(new, _substance("SIM-SA", "10"), _substance("SIM-SB", "5")),),
        order=order,
    ).changes

    assert changes
    assert all(c.field_name.startswith("Laakeaine/VaikuttavaAine[Aine=SIM-SB]/") for c in changes)
    assert all(c.prior_value[0].state.value == "missing" for c in changes)


def test_substance_without_aine_code_falls_back_to_cas_number(snapshot_pair):
    from src.domain.medicine_snapshot import ActiveSubstanceFields

    old, new, order = snapshot_pair
    new = replace(new, product=old.product)
    uncoded = ActiveSubstanceFields(
        SourceField.missing(),
        SourceField.of("SIM-CAS-9"),
        SourceField.of("1"),
        SourceField.missing(),
        SourceField.missing(),
    )
    changed = replace(uncoded, maara=SourceField.of("2"))

    changes = detect_relevant_changes(
        (_with_substances(old, uncoded, _substance("SIM-SA", "10")),),
        (_with_substances(new, _substance("SIM-SA", "10"), changed),),
        order=order,
    ).changes

    assert [c.field_name for c in changes] == ["Laakeaine/VaikuttavaAine[CAS=SIM-CAS-9]/Maara"]


def test_authorizations_are_numbered_within_their_branch(snapshot_pair):
    from src.domain.medicine_snapshot import (
        AuthorizationBranch,
        AuthorizationRegistrationFields,
    )

    old, new, order = snapshot_pair
    new = replace(new, product=old.product, active_substances=old.active_substances)

    def authorization(branch, status):
        return AuthorizationRegistrationFields(
            branch,
            SourceField.empty(attributes=(("id", status),)),
            SourceField.of("2099-01-01"),
            SourceField.missing(),
        )

    marketing = authorization(AuthorizationBranch.MYYNTILUPA, "SIM-ACTIVE")
    registration = authorization(AuthorizationBranch.REKISTEROINTI, "SIM-ACTIVE")

    result = detect_relevant_changes(
        (replace(old, authorizations=(marketing, registration)),),
        (replace(new, authorizations=(registration, marketing)),),
        order=order,
    )

    assert result.changes == ()
