"""Feature 007 (1b): a pharmacist records review steps on a case.

Cases come from the synthetic fixtures through the real ingestion; the review
API, its rules and the stored history are the real code.
"""

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.services.simulated_medication_records import load_simulated_medication_records

ROOT = Path(__file__).parents[3]
RELEASES = ROOT / "tests" / "fixtures" / "fimea-basic-register"
RECORDS = ROOT / "tests" / "fixtures" / "simulated-medication-records" / "medication-records.json"
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
def client(isolated_app):
    isolated_app.state.medication_records = load_simulated_medication_records(RECORDS)
    with TestClient(isolated_app) as client:
        _upload(client, "prior-release.xml", 3)
        _upload(client, "current-release.xml", 4)
        yield client


def _first_case(client) -> dict:
    return client.get(CASES).json()[0]


def _step(client, case_id, expected, to, initials="AB", note=None):
    return client.post(
        f"/api/review-cases/{case_id}/status-events",
        json={
            "expectedStatus": expected,
            "toStatus": to,
            "reviewerInitials": initials,
            "note": note,
        },
    )


def test_new_cases_start_with_one_system_event(client):
    case = _first_case(client)
    assert case["status"] == "NEW"
    assert case["caseType"] == "RELEASE"
    assert [
        (e["fromStatus"], e["toStatus"], e["reviewerInitials"], e["note"])
        for e in case["statusHistory"]
    ] == [(None, "NEW", None, None)]


def test_in_progress_then_reviewed_with_history(client):
    case = _first_case(client)
    started = _step(client, case["caseId"], "NEW", "IN_PROGRESS", "ab")
    assert started.status_code == 201, started.text
    assert started.json()["status"] == "IN_PROGRESS"

    reviewed = _step(
        client, case["caseId"], "IN_PROGRESS", "REVIEWED_NO_ACTION", "AB", "  Checked the label.  "
    )
    assert reviewed.status_code == 201, reviewed.text
    body = reviewed.json()
    assert body["status"] == "REVIEWED_NO_ACTION"
    history = [
        (e["fromStatus"], e["toStatus"], e["reviewerInitials"], e["note"])
        for e in body["statusHistory"]
    ]
    assert history == [
        (None, "NEW", None, None),
        ("NEW", "IN_PROGRESS", "ab", None),
        ("IN_PROGRESS", "REVIEWED_NO_ACTION", "AB", "Checked the label."),
    ]
    assert all(re.fullmatch(r".+\+00:00", e["occurredAt"]) for e in body["statusHistory"])

    # It leaves the open list and is found with reviewed cases (FR-006).
    open_ids = [c["caseId"] for c in client.get(CASES).json()]
    all_cases = client.get(CASES, params={"includeReviewed": "true"}).json()
    assert case["caseId"] not in open_ids
    assert [c["status"] for c in all_cases if c["caseId"] == case["caseId"]] == [
        "REVIEWED_NO_ACTION"
    ]


def test_a_case_can_be_reviewed_straight_from_new_and_reopened_with_a_note(client):
    case_id = _first_case(client)["caseId"]
    assert (
        _step(client, case_id, "NEW", "REVIEWED_FOLLOW_UP", "CD", "Ask the team.").status_code
        == 201
    )
    assert _step(client, case_id, "REVIEWED_FOLLOW_UP", "IN_PROGRESS", "CD").status_code == 422
    reopened = _step(client, case_id, "REVIEWED_FOLLOW_UP", "IN_PROGRESS", "CD", "Wrong case.")
    assert reopened.status_code == 201
    assert case_id in [c["caseId"] for c in client.get(CASES).json()]


@pytest.mark.parametrize(
    ("expected", "to", "initials", "note", "status", "code"),
    [
        ("NEW", "NEW", "AB", None, 409, "TRANSITION_NOT_ALLOWED"),
        ("IN_PROGRESS", "NEW", "AB", None, 409, "TRANSITION_NOT_ALLOWED"),
        ("NEW", "REVIEWED_NO_ACTION", "AB", None, 422, "INVALID_REVIEW_STEP"),
        ("NEW", "REVIEWED_NO_ACTION", "AB", "   ", 422, "INVALID_REVIEW_STEP"),
        ("NEW", "IN_PROGRESS", "", None, 422, "INVALID_REVIEW_STEP"),
        ("NEW", "IN_PROGRESS", "A1", None, 422, "INVALID_REVIEW_STEP"),
        ("NEW", "IN_PROGRESS", "ABCDEFGHIJK", None, 422, "INVALID_REVIEW_STEP"),
        ("NEW", "REVIEWED_NO_ACTION", "AB", "x" * 1001, 422, "INVALID_REVIEW_STEP"),
    ],
)
def test_invalid_steps_are_rejected_and_change_nothing(
    client, expected, to, initials, note, status, code
):
    case = _first_case(client)
    response = _step(client, case["caseId"], expected, to, initials, note)
    assert response.status_code == status
    assert response.json()["detail"]["code"] == code
    after = _first_case(client)
    assert after["status"] == "NEW"
    assert len(after["statusHistory"]) == 1


def test_a_stale_expected_status_is_rejected(client):
    case_id = _first_case(client)["caseId"]
    assert _step(client, case_id, "NEW", "IN_PROGRESS").status_code == 201
    # A second reviewer still sees NEW and tries to record an outcome.
    stale = _step(client, case_id, "NEW", "REVIEWED_NO_ACTION", "EF", "Fine.")
    assert stale.status_code == 409
    assert stale.json()["detail"] == {
        "code": "STALE_STATUS",
        "message": "The case's status has changed since it was loaded; reload and try again.",
        "currentStatus": "IN_PROGRESS",
    }


def test_unknown_case_and_unknown_status(client):
    missing = _step(client, "CASE-unknown", "NEW", "IN_PROGRESS")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "CASE_NOT_FOUND"
    assert _step(client, _first_case(client)["caseId"], "NEW", "CLOSED").status_code == 422


def test_later_releases_never_change_a_reviewed_status(client, isolated_app):
    case_id = _first_case(client)["caseId"]
    _step(client, case_id, "NEW", "REVIEWED_NO_ACTION", "AB", "Done.")
    third = (
        (RELEASES / "current-release.xml")
        .read_bytes()
        .replace(b"<Ajopvm>2099-01-02</Ajopvm>", b"<Ajopvm>2099-01-03</Ajopvm>")
        .replace(b"SIM-2099-002", b"SIM-2099-003")
    )
    response = client.post(
        "/api/source-releases/ingest",
        files={"file": ("third.xml", third, "application/xml")},
        data={
            "sourceName": "Fimea Basic Register",
            "sourceReleaseReference": json.dumps({"value": "third", "evidenceClass": "VERIFIED"}),
            "retrievedAt": "2099-01-05T06:00:00+00:00",
        },
    )
    assert response.status_code == 200
    (case,) = [
        c
        for c in client.get(CASES, params={"includeReviewed": "true"}).json()
        if c["caseId"] == case_id
    ]
    assert case["status"] == "REVIEWED_NO_ACTION"
    assert len(case["statusHistory"]) == 2


def test_only_the_review_endpoint_changes_case_status():
    # FR-005: no ingestion, comparison, shortage or schedule code records a status event.
    callers = sorted(
        str(path.relative_to(ROOT))
        for path in (ROOT / "backend" / "src").rglob("*.py")
        if "record_status_event(" in path.read_text(encoding="utf-8")
    )
    assert callers == ["backend/src/api/review_cases.py", "backend/src/services/pipeline_store.py"]


def test_an_existing_database_gets_the_new_columns(tmp_path):
    import sqlite3

    from src.services.pipeline_store import PipelineStore

    path = tmp_path / "old.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TABLE case_status_events (event_id VARCHAR(80) PRIMARY KEY,"
            " case_id VARCHAR(80), from_status VARCHAR(20), to_status VARCHAR(20),"
            " occurred_at DATETIME)"
        )
    store = PipelineStore(f"sqlite:///{path}")
    store.open_case_payloads()
    store.dispose()
    with sqlite3.connect(path) as db:
        columns = [row[1] for row in db.execute("PRAGMA table_info(case_status_events)")]
    assert columns[-2:] == ["reviewer_initials", "note"]
