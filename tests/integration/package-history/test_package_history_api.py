"""Feature 013: a package's history across compared releases.

Synthetic releases go through the real ingestion; recording, the backfill and
the history endpoint are the real code.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.workflows.release_quality import backfill_release_pairs

ROOT = Path(__file__).parents[3]
RELEASES = ROOT / "tests" / "fixtures" / "fimea-basic-register"


def _upload(client, name: str, day: int) -> None:
    response = client.post(
        "/api/source-releases/ingest",
        files={"file": ("Perusrekisteri.xml", (RELEASES / name).read_bytes(), "application/xml")},
        data={
            "sourceName": "Fimea Basic Register",
            "sourceReleaseReference": json.dumps({"value": name, "evidenceClass": "VERIFIED"}),
            "retrievedAt": f"2099-01-{day:02d}T06:00:00+00:00",
        },
    )
    assert response.status_code == 200, response.text


def _history(client, package: str) -> dict:
    response = client.get(f"/api/medicine-catalogue/packages/{package}/history")
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def client(isolated_app):
    with TestClient(isolated_app) as client:
        yield client


def test_no_history_before_a_comparison(client):
    _upload(client, "prior-release.xml", 3)
    assert _history(client, "SIM-PKG-100") == {
        "pakkaustunnus": "SIM-PKG-100",
        "comparedPairs": [],
        "events": [],
    }


def test_changed_removed_and_new_packages_are_recorded_with_values(client):
    _upload(client, "prior-release.xml", 3)
    _upload(client, "current-release.xml", 4)
    history = _history(client, "SIM-PKG-100")
    assert history["comparedPairs"] == [
        {"priorReleaseDate": "2099-01-01", "currentReleaseDate": "2099-01-02"}
    ]
    (event,) = history["events"]
    assert event["kind"] == "FIELDS_CHANGED"
    assert (event["priorReleaseDate"], event["currentReleaseDate"]) == ("2099-01-01", "2099-01-02")
    name = next(c for c in event["changes"] if c["field"] == "Laakevalmiste/Kauppanimi")
    assert name["before"][0]["value"] == "Fictional Product Amber"
    assert name["after"][0]["value"] == "Fictional Product Amber Revised"
    assert name["formattingOnly"] is False

    assert [e["kind"] for e in _history(client, "SIM-PKG-300")["events"]] == ["NO_LONGER_PRESENT"]
    (new,) = _history(client, "SIM-PKG-400")["events"]
    assert new["kind"] == "NEWLY_PRESENT" and new["changes"] == []
    # A package without changes: the compared pair is listed, with no events.
    unchanged = _history(client, "SIM-PKG-UNKNOWN")
    assert unchanged["events"] == [] and len(unchanged["comparedPairs"]) == 1


def test_events_are_newest_first_with_clean_up_labels(client):
    _upload(client, "prior-release.xml", 3)
    _upload(client, "current-release.xml", 4)
    _upload(client, "cleanup-release.xml", 5)
    events = _history(client, "SIM-PKG-100")["events"]
    assert [(e["currentReleaseDate"], e["cleanupLabel"]) for e in events] == [
        ("2099-01-03", "FORMATTING_ONLY"),
        ("2099-01-02", None),
    ]
    assert events[0]["changes"][0]["formattingOnly"] is True


def test_pairs_without_history_are_backfilled_once(client, isolated_app):
    _upload(client, "current-release.xml", 4)
    _upload(client, "prior-release.xml", 5)  # older, loaded later: never compared
    assert _history(client, "SIM-PKG-100")["events"] == []

    store = isolated_app.state.store
    assert backfill_release_pairs(store) == {"qualityChecks": 1, "packageHistories": 1}
    assert backfill_release_pairs(store) == {"qualityChecks": 0, "packageHistories": 0}
    assert [e["kind"] for e in _history(client, "SIM-PKG-100")["events"]] == ["FIELDS_CHANGED"]


def test_history_does_not_need_the_catalogue_and_changes_nothing(client, isolated_app):
    _upload(client, "prior-release.xml", 3)
    _upload(client, "current-release.xml", 4)
    cases = client.get("/api/open-review-cases").json()
    first = _history(client, "SIM-PKG-100")
    assert _history(client, "SIM-PKG-100") == first
    assert client.get("/api/open-review-cases").json() == cases
