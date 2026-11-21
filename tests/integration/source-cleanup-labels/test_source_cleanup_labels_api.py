"""Feature 008: clean-up labels on review cases from the real pipeline.

Three synthetic releases go through the real ingestion. The third differs from
the second only in spaces and letter case for SIM-PKG-100, only in
active-substance fields for SIM-PKG-200, and in both kinds of field for
SIM-PKG-500.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.services.simulated_medication_records import load_simulated_medication_records

ROOT = Path(__file__).parents[3]
RELEASES = ROOT / "tests" / "fixtures" / "fimea-basic-register"
CASES = "/api/open-review-cases"


def _upload(client, name: str, day: int) -> None:
    response = client.post(
        "/api/source-releases/ingest",
        files={"file": (name, (RELEASES / name).read_bytes(), "application/xml")},
        data={
            "sourceName": "Fimea Basic Register",
            "sourceReleaseReference": json.dumps({"value": name, "evidenceClass": "VERIFIED"}),
            "retrievedAt": f"2099-01-0{day}T06:00:00+00:00",
        },
    )
    assert response.status_code == 200, response.text


@pytest.fixture
def client(isolated_app, tmp_path):
    records = tmp_path / "records.json"
    records.write_text(
        json.dumps(
            {
                "dataset": "SIMULATED - fictional records for feature 008 tests",
                "records": [
                    {
                        "record_id": f"SIM-MED-8{n}",
                        "person_reference": f"SIM-PERSON-8{n}",
                        "medicine_display": f"Fictional record {n}",
                        "Pakkaustunnus": f"SIM-PKG-{n}",
                    }
                    for n in (100, 200, 500)
                ],
            }
        ),
        encoding="utf-8",
    )
    isolated_app.state.medication_records = load_simulated_medication_records(records)
    with TestClient(isolated_app) as client:
        _upload(client, "current-release.xml", 4)
        _upload(client, "cleanup-release.xml", 5)
        yield client


def _by_package(client) -> dict[str, dict]:
    response = client.get(CASES)
    assert response.status_code == 200, response.text
    return {case["medicineIdentifier"]: case for case in response.json()}


def test_labels_on_cases(client):
    cases = _by_package(client)
    assert sorted(cases) == ["SIM-PKG-100", "SIM-PKG-200", "SIM-PKG-500"]

    spacing = cases["SIM-PKG-100"]["changeSet"]
    assert spacing["cleanupLabel"] == "FORMATTING_ONLY"
    (name,) = spacing["changes"]
    assert name["field"] == "Laakevalmiste/Kauppanimi"
    assert name["formattingOnly"] is True
    # Values stay exactly as published.
    assert name["before"][0]["value"] == "Fictional Product Amber Revised"
    assert name["after"][0]["value"] == "Fictional  product AMBER revised "

    substance = cases["SIM-PKG-200"]["changeSet"]
    assert substance["cleanupLabel"] == "ACTIVE_SUBSTANCE_ONLY"
    assert {c["field"].split("/")[0] for c in substance["changes"]} == {"Laakeaine"}
    assert not any(c["formattingOnly"] for c in substance["changes"])

    mixed = cases["SIM-PKG-500"]["changeSet"]
    assert mixed["cleanupLabel"] is None
    assert "Pakkaus/Pakkauskoko" in {c["field"] for c in mixed["changes"]}


def test_labels_never_change_status_or_hide_cases(client):
    cases = _by_package(client)
    assert {case["status"] for case in cases.values()} == {"NEW"}
    case = cases["SIM-PKG-100"]
    single = client.post(
        f"/api/review-cases/{case['caseId']}/status-events",
        json={
            "expectedStatus": "NEW",
            "toStatus": "IN_PROGRESS",
            "reviewerInitials": "AB",
            "note": None,
        },
    )
    assert single.status_code == 201, single.text
    # The single-case answer carries the same label.
    assert single.json()["changeSet"]["cleanupLabel"] == "FORMATTING_ONLY"
    assert len(_by_package(client)) == 3
