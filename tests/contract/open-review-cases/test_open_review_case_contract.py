import json

from src.schemas.open_review_cases import open_review_case_payload
from src.services.create_review_cases import create_review_cases


def test_case_payload_preserves_required_status_match_change_and_sources(
    change_set, medication_record
):
    case = create_review_cases((change_set,), (medication_record,))[0]
    payload = open_review_case_payload(case)
    assert payload["caseId"] == case.case_id
    assert payload["status"] == "NEW" and payload["createdAt"]
    assert payload["medicineIdentifier"] == "SIM-PKG-100"
    assert payload["identifierGranularity"] == "package"
    assert payload["matchedRecord"]["recordId"] == "SIM-MED-100"
    assert payload["matchedRecord"]["personReference"].startswith("SIM-")
    assert payload["changeSet"]["changeSetId"] == change_set.change_set_id
    assert payload["changeSet"]["kind"] == "FIELDS_CHANGED"
    assert payload["changeSet"]["lastKnownFields"] is None
    (change,) = payload["changeSet"]["changes"]
    assert change["before"][0]["value"] == "Fictional Alpha"
    assert change["after"][0]["value"] == "Fictional Alpha Updated"
    assert change["field"] == "Laakevalmiste/Kauppanimi"
    assert payload["sources"]["current"]["fieldReference"] is None
    assert payload["sources"]["prior"]["fileName"] == "prior.xml"
    assert payload["sources"]["current"]["checksum"] == "new-checksum"
    assert payload["sources"]["current"]["recordLocator"]
    assert payload["sources"]["current"]["releaseReference"]["value"] == "SIM-002"
    assert payload["sources"]["current"]["evidenceClass"] == "VERIFIED"
    assert payload["sources"]["current"]["retrievedAt"] is None
    assert payload["initialStatusEvent"]["toStatus"] == "NEW"
    assert payload["initialStatusEvent"]["fromStatus"] is None
    assert json.loads(json.dumps(payload)) == payload


def test_missing_empty_attributes_and_unknown_provenance_are_explicit(
    snapshot_pair, medication_record
):
    from dataclasses import replace

    from src.domain.source_field import SourceField
    from src.services.detect_relevant_changes import detect_relevant_changes

    old, new, order = snapshot_pair
    new = replace(
        new,
        product=old.product,
        package=replace(old.package, julkinen_tarkenne=SourceField.missing()),
    )
    change_sets = detect_relevant_changes((old,), (new,), order=order).change_sets
    case = create_review_cases(change_sets, (medication_record,))[0]
    payload = open_review_case_payload(case)
    (change,) = payload["changeSet"]["changes"]
    assert change["before"][0]["state"] == "empty"
    assert change["after"][0]["state"] == "missing"
    assert payload["sourceOrder"]["prior"] == 1
    assert payload["sourceOrder"]["current"] == 2
    assert payload["sourceOrder"]["basis"]
    assert payload["sources"]["prior"]["retrievedAt"] is None


def test_no_longer_present_payload_shows_last_known_values_and_no_current_record(
    snapshot_pair, medication_record
):
    from dataclasses import replace

    from src.services.detect_relevant_changes import detect_relevant_changes

    old, new, order = snapshot_pair
    change_sets = detect_relevant_changes(
        (old,), (replace(new, pakkaustunnus="SIM-PKG-OTHER"),), order=order
    ).change_sets
    payload = open_review_case_payload(create_review_cases(change_sets, (medication_record,))[0])

    assert payload["changeSet"]["kind"] == "NO_LONGER_PRESENT"
    assert payload["changeSet"]["changes"] == []
    last_known = {item["field"]: item["values"] for item in payload["changeSet"]["lastKnownFields"]}
    assert last_known["Laakevalmiste/Kauppanimi"][0]["value"] == "Fictional Alpha"
    assert payload["sources"]["prior"]["recordLocator"]
    assert payload["sources"]["current"]["recordLocator"] is None
    assert payload["sources"]["current"]["checksum"] == "new-checksum"
    assert "does not state why" in payload["sources"]["current"]["note"]
    assert json.loads(json.dumps(payload)) == payload
