"""T028: replay a release through the public ingestion and review endpoints."""

import hashlib
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.open_review_cases import router as review_router
from src.api.source_release_ingestion import router as ingestion_router
from src.config import ApplicationConfig

FIXTURES = Path(__file__).parents[2] / "fixtures" / "fimea-basic-register"


def _upload(client, filename, order):
    content = (FIXTURES / filename).read_bytes()
    response = client.post(
        "/api/source-releases/ingest",
        files={"file": (filename, content, "application/xml")},
        data={
            "sourceName": "Fimea Basic Register",
            "sourceReleaseReference": json.dumps(
                {"value": f"SIM-{filename}", "evidenceClass": "VERIFIED"}
            ),
            "sourceOrder": json.dumps({"value": str(order), "evidenceClass": "VERIFIED"}),
            "retrievedAt": f"2099-01-0{order + 2}T00:00:00+00:00",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["processingStatus"] == "VALIDATED", response.text


def _read_cases(client):
    response = client.get("/api/open-review-cases")
    assert response.status_code == 200, response.text
    return response.json()


def test_repeated_ingestion_preserves_original_case_evidence(tmp_path, medication_record):
    app = FastAPI()
    app.include_router(ingestion_router)
    app.include_router(review_router)
    app.state.source_release_config = ApplicationConfig(tmp_path / "captures", 1024 * 1024)
    app.state.open_review_cases = []
    app.state.medication_records = (medication_record,)

    with TestClient(app) as client:
        _upload(client, "prior-release.xml", 1)
        assert _read_cases(client) == []

        _upload(client, "current-release.xml", 2)
        original_cases = _read_cases(client)
        name_changes = [
            case for case in original_cases if case["change"]["field"] == "Laakevalmiste/Kauppanimi"
        ]
        assert len(name_changes) == 1
        original_case = name_changes[0]
        assert original_case["status"] == "NEW"
        assert original_case["medicineIdentifier"] == "SIM-PKG-100"
        assert original_case["matchedRecord"]["recordId"] == medication_record.record_id
        assert original_case["change"]["field"] == "Laakevalmiste/Kauppanimi"
        assert original_case["change"]["before"][0]["value"] == "Fictional Product Amber"
        assert original_case["change"]["after"][0]["value"] == ("Fictional Product Amber Revised")

        for case in original_cases:
            assert case["matchedRecord"]["recordId"] == medication_record.record_id
            for side, filename in (
                ("prior", "prior-release.xml"),
                ("current", "current-release.xml"),
            ):
                source = case["sources"][side]
                assert source["fileName"] == filename
                assert (
                    source["checksum"]
                    == hashlib.sha256((FIXTURES / filename).read_bytes()).hexdigest()
                )
                assert source["recordLocator"] == "/Perusrekisteri/Pakkaus[1]"
                assert source["recordIdentifier"] == case["medicineIdentifier"]
                assert source["fieldReference"] == case["change"]["field"]
                assert source["evidenceClass"] == "VERIFIED"

        _upload(client, "current-release.xml", 2)
        replayed_cases = _read_cases(client)
        assert len(replayed_cases) == len(original_cases)
        assert {case["caseId"]: case for case in replayed_cases} == {
            case["caseId"]: case for case in original_cases
        }
