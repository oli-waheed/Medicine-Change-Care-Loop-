"""Identical downloads are stored once, and missing raw evidence is reported, not hidden."""

import json
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

FIXTURES = Path(__file__).parents[2] / "fixtures" / "fimea-basic-register"


def _upload(client, filename, day, *, upload_name=None, retrieved_at=None):
    response = client.post(
        "/api/source-releases/ingest",
        files={"file": (upload_name or filename, (FIXTURES / filename).read_bytes())},
        data={
            "sourceName": "Fimea Basic Register",
            "sourceReleaseReference": json.dumps({"value": "SIM", "evidenceClass": "VERIFIED"}),
            "retrievedAt": retrieved_at or f"2099-01-0{day}T06:00:00+00:00",
        },
    )
    return response


def _capture_dirs(app):
    root = app.state.source_release_config.source_release_storage_dir
    return sorted(path.name for path in Path(root).iterdir() if path.is_dir())


def test_identical_daily_download_is_stored_once_and_each_retrieval_recorded(isolated_app):
    app = isolated_app
    with TestClient(app) as client:
        first = _upload(client, "prior-release.xml", 3).json()
        second = _upload(client, "prior-release.xml", 4).json()
        renamed = _upload(client, "prior-release.xml", 5, upload_name="Perusrekisteri.xml").json()
        replay = _upload(client, "prior-release.xml", 3).json()

    assert first["alreadyCaptured"] is False
    for later in (second, renamed, replay):
        assert later["alreadyCaptured"] is True
        assert later["capturedReleaseReference"] == first["capturedReleaseReference"]
        assert later["processingStatus"] == "VALIDATED"
        assert later["chronologyStatus"] == "AVAILABLE"

    assert len(app.state.store.captures()) == 1
    assert _capture_dirs(app) == [first["capturedReleaseReference"]]
    retrievals = app.state.store.retrievals(first["capturedReleaseReference"])
    assert [r.retrieved_at.day for r in retrievals] == [4, 5]


def test_identical_failed_release_returns_the_same_failure(isolated_app):
    app = isolated_app
    with TestClient(app) as client:
        first = _upload(client, "malformed-release.xml", 3).json()
        again = _upload(client, "malformed-release.xml", 4).json()

    assert first["processingStatus"] == again["processingStatus"] == "FAILED"
    assert again["failureDetail"] == first["failureDetail"]
    assert again["capturedReleaseReference"] == first["capturedReleaseReference"]
    assert again["alreadyCaptured"] is True
    assert len(app.state.store.captures()) == 1


def test_a_repeated_download_is_still_validated(isolated_app):
    with TestClient(isolated_app) as client:
        _upload(client, "prior-release.xml", 3)
        response = _upload(client, "prior-release.xml", 4, retrieved_at="2099-01-04T06:00:00")

    assert response.status_code == 422
    assert "timezone-aware" in response.json()["detail"]


def test_case_reports_unavailable_evidence_when_raw_files_are_gone(isolated_app, medication_record):
    app = isolated_app
    app.state.medication_records = (medication_record,)
    with TestClient(app) as client:
        prior = _upload(client, "prior-release.xml", 3).json()
        current = _upload(client, "current-release.xml", 4).json()
        cases = client.get("/api/open-review-cases").json()
        assert cases
        for case in cases:
            assert case["evidenceAvailability"] == "AVAILABLE"
            assert case["sources"]["prior"]["evidenceAvailable"] is True
            assert case["sources"]["current"]["evidenceAvailable"] is True

        root = Path(app.state.source_release_config.source_release_storage_dir)
        for raw_file in (root / prior["capturedReleaseReference"] / "files").rglob("*.xml"):
            raw_file.unlink()
        cases = client.get("/api/open-review-cases").json()
        for case in cases:
            assert case["evidenceAvailability"] == "UNAVAILABLE"
            assert case["sources"]["prior"]["evidenceAvailable"] is False
            assert case["sources"]["current"]["evidenceAvailable"] is True
            # The recorded evidence itself is unchanged; only its availability is reported.
            assert case["sources"]["prior"]["checksum"]

        shutil.rmtree(root / current["capturedReleaseReference"])
        for case in client.get("/api/open-review-cases").json():
            assert case["sources"]["current"]["evidenceAvailable"] is False
