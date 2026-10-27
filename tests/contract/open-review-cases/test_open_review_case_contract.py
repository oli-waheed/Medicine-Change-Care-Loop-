import json

from src.schemas.open_review_cases import open_review_case_payload
from src.services.create_review_cases import create_review_cases


def test_case_payload_preserves_required_status_match_change_and_sources(
    detected_change, medication_record
):
    case = create_review_cases((detected_change,), (medication_record,))[0]
    payload = open_review_case_payload(case)
    assert payload["caseId"] == case.case_id
    assert payload["status"] == "NEW" and payload["createdAt"]
    assert payload["medicineIdentifier"] == "SIM-PKG-100"
    assert payload["identifierGranularity"] == "package"
    assert payload["matchedRecord"]["recordId"] == "SIM-MED-100"
    assert payload["matchedRecord"]["personReference"].startswith("SIM-")
    assert payload["change"]["before"][0]["value"] == "Fictional Alpha"
    assert payload["change"]["after"][0]["value"] == "Fictional Alpha Updated"
    assert payload["change"]["field"] == "Laakevalmiste/Kauppanimi"
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
    change = detect_relevant_changes((old,), (new,), order=order).changes[0]
    case = create_review_cases((change,), (medication_record,))[0]
    payload = open_review_case_payload(case)
    assert payload["change"]["before"][0]["state"] == "empty"
    assert payload["change"]["after"][0]["state"] == "missing"
    assert payload["sourceOrder"]["prior"] == 1
    assert payload["sourceOrder"]["current"] == 2
    assert payload["sourceOrder"]["basis"]
    assert payload["sources"]["prior"]["retrievedAt"] is None
