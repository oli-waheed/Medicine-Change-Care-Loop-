"""Feature 008: the rules for source clean-up labels (pure functions)."""

import pytest

from src.services.source_cleanup_labels import (
    CleanupLabel,
    cleanup_label,
    formatting_only,
    with_cleanup_labels,
)


def value(text, attributes=None):
    return {"state": "value", "value": text, "attributes": attributes or {}}


EMPTY = {"state": "empty", "value": "", "attributes": {}}
MISSING = {"state": "missing", "value": None, "attributes": {}}


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ([value("Firekol ")], [value("Firekol")]),
        ([value("Ibuprofen Stada")], [value("Ibuprofen STADA")]),
        ([value("10 mg  tablet")], [value("10 mg tablet")]),
        ([value("a"), value("B ")], [value("A"), value("b")]),
    ],
)
def test_spacing_or_letter_case_only(before, after):
    assert formatting_only(before, after)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ([value("Firekol")], [value("Firekol")]),  # no difference at all
        ([value("2.0")], [value("2.00")]),  # a different value
        ([value("10mg")], [value("10 mg")]),  # a space added inside a word
        ([value("x", {"id": "1"})], [value("X", {"id": "2"})]),  # attributes differ
        ([EMPTY], [value(" ")]),  # state differs
        ([MISSING], [EMPTY]),
        ([value("a")], [value("a"), value("b")]),  # occurrence count differs
    ],
)
def test_other_differences_are_not_formatting(before, after):
    assert not formatting_only(before, after)


def change(field, before, after):
    return {"changeId": field, "field": field, "before": before, "after": after}


SUBSTANCE = "Laakeaine/VaikuttavaAine[Aine=SIM-SA01]/JakamatonVahvuus"


def test_case_labels():
    spacing = change("Laakevalmiste/Kauppanimi", [value("A ")], [value("a")])
    substance = change(SUBSTANCE, [value("1 mg (resp 1mg)")], [value("1 mg")])
    package = change("Pakkaus/Pakkauskoko", [value("10")], [value("20")])

    assert cleanup_label([spacing]) is CleanupLabel.FORMATTING_ONLY
    assert cleanup_label([substance]) is CleanupLabel.ACTIVE_SUBSTANCE_ONLY
    # A spacing change in a substance field is still formatting only.
    assert cleanup_label([change(SUBSTANCE, [value("x ")], [value("X")])]) is (
        CleanupLabel.FORMATTING_ONLY
    )
    assert cleanup_label([spacing, substance]) is None
    assert cleanup_label([substance, package]) is None
    assert cleanup_label([package]) is None
    assert cleanup_label([]) is None


def test_payload_labels_leave_values_and_other_cases_alone():
    spacing = change("Laakevalmiste/Kauppanimi", [value("A ")], [value("a")])
    package = change("Pakkaus/Pakkauskoko", [value("10")], [value("20")])
    payload = {
        "caseType": "RELEASE",
        "changeSet": {"kind": "FIELDS_CHANGED", "changes": [spacing, package]},
    }
    labelled = with_cleanup_labels(payload)
    assert labelled["changeSet"]["cleanupLabel"] is None
    assert [c["formattingOnly"] for c in labelled["changeSet"]["changes"]] == [True, False]
    assert [c["before"] for c in labelled["changeSet"]["changes"]] == [
        spacing["before"],
        package["before"],
    ]
    assert payload["changeSet"]["changes"][0] == spacing  # the input is not changed

    removed = {"caseType": "RELEASE", "changeSet": {"kind": "NO_LONGER_PRESENT", "changes": []}}
    assert with_cleanup_labels(removed)["changeSet"]["cleanupLabel"] is None

    shortage = {"caseType": "SHORTAGE", "shortageChange": {}}
    assert with_cleanup_labels(shortage) is shortage
