import json
from dataclasses import replace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.change_processing_outcomes import router
from src.schemas.change_processing_outcomes import change_processing_outcome_payload
from src.services.change_processing_outcomes import build_change_processing_outcomes
from src.services.create_review_cases import create_review_cases
from src.services.detect_relevant_changes import detect_relevant_changes
from src.services.pipeline_store import PipelineStore


@pytest.fixture
def three_outcomes(snapshot_pair, medication_record):
    """One MATCHED, one NO_MATCH and one AMBIGUOUS outcome from distinct packages."""
    old, new, order = snapshot_pair
    prior = (
        old,
        replace(old, pakkaustunnus="SIM-PKG-NOMATCH"),
        replace(old, pakkaustunnus="SIM-PKG-AMBIG"),
    )
    current = (
        new,
        replace(new, pakkaustunnus="SIM-PKG-NOMATCH"),
        replace(new, pakkaustunnus="SIM-PKG-AMBIG"),
    )
    records = (
        medication_record,
        replace(medication_record, record_id="SIM-MED-A1", package_identifier="SIM-PKG-AMBIG"),
        replace(medication_record, record_id="SIM-MED-A2", package_identifier="SIM-PKG-AMBIG"),
    )
    change_sets = detect_relevant_changes(prior, current, order=order).change_sets
    cases = create_review_cases(change_sets, records)
    return build_change_processing_outcomes(change_sets, records, cases), cases


@pytest.fixture
def client(tmp_path, three_outcomes):
    outcomes, cases = three_outcomes
    app = FastAPI()
    app.include_router(router)
    app.state.store = PipelineStore(f"sqlite:///{tmp_path / 'outcomes.sqlite3'}")
    app.state.store.add_cases(cases)
    app.state.store.add_processing_outcomes(outcomes)
    with TestClient(app) as test_client:
        yield test_client


def test_payload_has_required_match_result_fields(three_outcomes):
    outcomes, cases = three_outcomes
    payloads = {
        p["medicineIdentifier"]: p for p in map(change_processing_outcome_payload, outcomes)
    }

    matched = payloads["SIM-PKG-100"]
    assert matched["result"] == "MATCHED"
    assert matched["reason"] == "UNIQUE_EXACT_PACKAGE_MATCH"
    assert matched["comparedIdentifier"] == "SIM-PKG-100"
    assert matched["identifierGranularity"] == "package"
    assert matched["changeKind"] == "FIELDS_CHANGED"
    assert matched["changedFields"] == ["Laakevalmiste/Kauppanimi"]
    assert [r["recordId"] for r in matched["simulatedRecords"]] == ["SIM-MED-100"]
    assert matched["caseIds"] == [cases[0].case_id]
    assert matched["evidenceClass"] == "VERIFIED"
    assert matched["sources"]["prior"]["fileName"] == "prior.xml"
    assert matched["sources"]["current"]["checksum"] == "new-checksum"

    no_match = payloads["SIM-PKG-NOMATCH"]
    assert (no_match["result"], no_match["simulatedRecords"], no_match["caseIds"]) == (
        "NO_MATCH",
        [],
        [],
    )
    assert "no review case was created" in no_match["note"]

    ambiguous = payloads["SIM-PKG-AMBIG"]
    assert ambiguous["result"] == "AMBIGUOUS"
    assert [r["recordId"] for r in ambiguous["simulatedRecords"]] == ["SIM-MED-A1", "SIM-MED-A2"]
    assert ambiguous["caseIds"] == []
    for payload in payloads.values():
        assert json.loads(json.dumps(payload)) == payload


def test_api_returns_every_outcome_by_default(client):
    response = client.get("/api/change-processing-outcomes")

    assert response.status_code == 200
    assert sorted(p["result"] for p in response.json()) == ["AMBIGUOUS", "MATCHED", "NO_MATCH"]


def test_api_filters_to_unmatched_and_ambiguous(client):
    response = client.get(
        "/api/change-processing-outcomes", params=[("result", "NO_MATCH"), ("result", "AMBIGUOUS")]
    )

    assert response.status_code == 200
    payload = response.json()
    assert sorted(p["result"] for p in payload) == ["AMBIGUOUS", "NO_MATCH"]
    assert all(p["caseIds"] == [] for p in payload)


def test_api_rejects_an_unknown_result_filter(client):
    response = client.get("/api/change-processing-outcomes", params={"result": "MAYBE"})

    assert response.status_code == 422
    assert "MAYBE" in response.json()["detail"]


def test_outcomes_are_stored_once_per_change_set(tmp_path, three_outcomes):
    outcomes, _ = three_outcomes
    store = PipelineStore(f"sqlite:///{tmp_path / 'once.sqlite3'}")

    assert store.add_processing_outcomes(outcomes) == 3
    assert store.add_processing_outcomes(outcomes) == 0
    assert len(store.processing_outcome_payloads()) == 3
