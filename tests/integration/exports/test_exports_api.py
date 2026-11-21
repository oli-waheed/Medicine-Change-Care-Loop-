"""Feature 011: CSV exports of review cases and their history.

Cases come from the synthetic fixtures through the real ingestion and review API.
"""

import csv
import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.services.simulated_medication_records import load_simulated_medication_records

ROOT = Path(__file__).parents[3]
RELEASES = ROOT / "tests" / "fixtures" / "fimea-basic-register"
RECORDS = ROOT / "tests" / "fixtures" / "simulated-medication-records" / "medication-records.json"
CASES_CSV = "/api/exports/review-cases.csv"
HISTORY_CSV = "/api/exports/review-history.csv"


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
def client(isolated_app):
    isolated_app.state.medication_records = load_simulated_medication_records(RECORDS)
    with TestClient(isolated_app) as client:
        _upload(client, "prior-release.xml", 3)
        _upload(client, "current-release.xml", 4)
        yield client


def _rows(response) -> list[dict]:
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")
    raw = response.content
    assert raw.startswith("﻿".encode())  # BOM: Excel reads UTF-8
    text = raw.decode("utf-8-sig")
    assert "\r\n" in text
    return list(csv.DictReader(io.StringIO(text, newline=""), delimiter=";"))


def _step(client, case_id, expected, to, note=None, initials="AB"):
    response = client.post(
        f"/api/review-cases/{case_id}/status-events",
        json={
            "expectedStatus": expected,
            "toStatus": to,
            "reviewerInitials": initials,
            "note": note,
        },
    )
    assert response.status_code == 201, response.text


def test_cases_export_lists_every_case_with_its_change_and_source(client):
    response = client.get(CASES_CSV)
    assert response.headers["content-disposition"].startswith('attachment; filename="review-cases-')
    rows = _rows(response)
    cases = client.get("/api/open-review-cases").json()
    assert sorted(row["Case ID"] for row in rows) == sorted(c["caseId"] for c in cases)
    updated = next(row for row in rows if row["Package ID (Pakkaustunnus)"] == "SIM-PKG-100")
    assert updated["Case type"] == "Release"
    assert updated["Status"] == "New"
    assert updated["Change"] == "Updated package"
    assert "Laakevalmiste/Kauppanimi" in updated["Changed fields"]
    assert updated["Prior source"] == "Basic Register Ajopvm 2099-01-01"
    assert updated["Current source"] == "Basic Register Ajopvm 2099-01-02"
    assert updated["Source evidence"] == "Available"
    assert updated["Review steps"] == "0" and updated["Last reviewer"] == ""


def test_reviewed_cases_and_their_history_are_exported(client):
    case_id = client.get("/api/open-review-cases").json()[0]["caseId"]
    _step(client, case_id, "NEW", "IN_PROGRESS")
    _step(client, case_id, "IN_PROGRESS", "REVIEWED_FOLLOW_UP", "Ask; then call.\nLine two", "CD")

    row = next(r for r in _rows(client.get(CASES_CSV)) if r["Case ID"] == case_id)
    assert row["Status"] == "Reviewed – follow-up needed"
    assert row["Last reviewer"] == "CD"
    assert row["Last note"] == "Ask; then call.\nLine two"  # quoted, kept as typed
    assert row["Review steps"] == "2"

    history = [r for r in _rows(client.get(HISTORY_CSV)) if r["Case ID"] == case_id]
    assert [(r["From status"], r["To status"], r["Reviewer"]) for r in history] == [
        ("", "New", "System"),
        ("New", "In progress", "AB"),
        ("In progress", "Reviewed – follow-up needed", "CD"),
    ]


@pytest.mark.parametrize("note", ["=1+1", "+SUM(A1)", "-2", "@cmd"])
def test_text_that_looks_like_a_formula_is_kept_as_text(client, note):
    case_id = client.get("/api/open-review-cases").json()[0]["caseId"]
    _step(client, case_id, "NEW", "REVIEWED_NO_ACTION", note)
    row = next(r for r in _rows(client.get(CASES_CSV)) if r["Case ID"] == case_id)
    assert row["Last note"] == "'" + note


def test_exports_change_nothing(client):
    before = client.get("/api/open-review-cases?includeReviewed=true").json()
    client.get(CASES_CSV)
    client.get(HISTORY_CSV)
    assert client.get("/api/open-review-cases?includeReviewed=true").json() == before


def test_empty_exports_have_headers_only(isolated_app):
    with TestClient(isolated_app) as client:
        for url in (CASES_CSV, HISTORY_CSV):
            assert _rows(client.get(url)) == []
            text = client.get(url).content.decode("utf-8-sig")
            assert text.startswith("Case ID;")


def test_shortage_cases_describe_the_shortage_and_its_files():
    from src.api.exports import _change, _source

    captured = json.loads(
        (ROOT / "frontend" / "src" / "test" / "caseReviewResponses.json").read_text("utf-8")
    )
    shortage = next(case for case in captured if case.get("caseType") == "SHORTAGE")
    change, columns, label = _change(shortage)
    assert change.startswith("Shortage ") and f"(VNR {shortage['shortageChange']['vnr']})" in change
    assert columns == ", ".join(shortage["shortageChange"]["changedColumns"])
    assert label == ""
    prior = shortage["sources"]["prior"]
    assert _source(shortage, "prior") == (
        f"Shortages.txt downloaded {prior['retrievedAt']}, line {prior['lineNumber']}"
    )
