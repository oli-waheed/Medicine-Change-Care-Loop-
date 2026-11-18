"""Integration tests for the source-release API, persistence and review workflow."""

import asyncio
import json
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from starlette.requests import Request

from src.api.open_review_cases import get_open_review_cases
from src.api.source_release_ingestion import ingest_uploaded_source_release
from src.services.pipeline_store import PipelineStore

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "fimea-basic-register"

# What the n8n workflow sends: it cannot know the order, so it declares UNKNOWN.
N8N_DECLARED_ORDER = {"value": None, "evidenceClass": "UNKNOWN"}


def _request(app, method="POST", path="/api/source-releases/ingest"):
    return Request(
        {
            "type": "http",
            "app": app,
            "headers": [],
            "method": method,
            "path": path,
            "query_string": b"",
        }
    )


def _upload(app, filename, *, day, declared_order=None):
    content = (FIXTURE_DIR / filename).read_bytes()
    return asyncio.run(
        ingest_uploaded_source_release(
            _request(app),
            UploadFile(filename=filename, file=BytesIO(content)),
            source_name="Fimea Basic Register",
            source_release_reference=json.dumps(
                {"value": f"SIM-{filename}", "evidenceClass": "VERIFIED"}
            ),
            retrieved_at=datetime(2099, 1, day, tzinfo=UTC).isoformat(),
            source_order=json.dumps(declared_order or N8N_DECLARED_ORDER),
        )
    )


def _open_cases(app):
    return get_open_review_cases(_request(app, "GET", "/api/open-review-cases"))


def test_n8n_style_uploads_create_persisted_cases_and_replay_is_idempotent(
    isolated_app, medication_record
):
    app = isolated_app
    app.state.medication_records = (medication_record,)

    baseline = _upload(app, "prior-release.xml", day=3)
    assert baseline["processingStatus"] == "VALIDATED"
    assert baseline["chronologyStatus"] == "AVAILABLE"
    assert _open_cases(app) == []

    current = _upload(app, "current-release.xml", day=4)
    assert current["processingStatus"] == "VALIDATED"

    cases = _open_cases(app)
    assert cases
    assert all(case["status"] == "NEW" for case in cases)
    assert all(case["matchedRecord"]["recordId"] == "SIM-MED-100" for case in cases)
    assert {case["sourceOrder"]["prior"] for case in cases} == {20990101}
    assert {case["sourceOrder"]["current"] for case in cases} == {20990102}
    assert "Ajopvm" in cases[0]["sourceOrder"]["basis"]
    # Retrieval time is evidence of when the prototype fetched each file.
    assert {case["sources"]["prior"]["retrievedAt"] for case in cases} == {
        "2099-01-03T00:00:00+00:00"
    }
    assert {case["sources"]["current"]["retrievedAt"] for case in cases} == {
        "2099-01-04T00:00:00+00:00"
    }

    for case in cases:
        events = app.state.store.status_events(case["caseId"])
        assert [(e.from_status, e.to_status) for e in events] == [(None, "NEW")]

    # Exact replay, and the same file fetched again on a later day.
    _upload(app, "current-release.xml", day=4)
    _upload(app, "current-release.xml", day=5)
    assert _open_cases(app) == cases


def test_cases_and_baseline_survive_a_restart(isolated_app, medication_record, tmp_path):
    app = isolated_app
    app.state.medication_records = (medication_record,)
    database_url = app.state.store.database_url

    _upload(app, "prior-release.xml", day=3)

    # Simulate a backend restart: a brand-new store on the same database file.
    app.state.store.dispose()
    app.state.store = PipelineStore(database_url)

    _upload(app, "current-release.xml", day=4)
    created = _open_cases(app)
    assert created
    # The baseline was reloaded from disk; its retrieval time survives the restart.
    assert created[0]["sources"]["prior"]["retrievedAt"] == "2099-01-03T00:00:00+00:00"

    app.state.store.dispose()
    app.state.store = PipelineStore(database_url)
    assert _open_cases(app) == created


def test_older_release_after_newer_one_is_recorded_but_not_compared(
    isolated_app, medication_record
):
    app = isolated_app
    app.state.medication_records = (medication_record,)

    _upload(app, "current-release.xml", day=3)
    older = _upload(app, "prior-release.xml", day=4)

    assert older["processingStatus"] == "VALIDATED"
    assert len(app.state.store.captures()) == 2
    assert app.state.store.comparison_baseline().source_order_value == "2099-01-02"
    assert _open_cases(app) == []


def test_release_without_ajopvm_never_becomes_baseline(isolated_app, medication_record):
    app = isolated_app
    app.state.medication_records = (medication_record,)

    unknown = _upload(
        app,
        "ordering-unknown-release.xml",
        day=3,
        declared_order={"value": "1", "evidenceClass": "VERIFIED"},
    )
    assert unknown["processingStatus"] == "VALIDATED"
    assert unknown["chronologyStatus"] == "UNAVAILABLE"
    assert app.state.store.comparison_baseline() is None

    verified = _upload(app, "prior-release.xml", day=4)
    baseline = app.state.store.comparison_baseline()
    assert baseline.release_id == verified["capturedReleaseReference"]
    assert len(app.state.store.captures()) == 2
    assert _open_cases(app) == []


def test_without_medication_records_releases_are_captured_but_no_cases_created(
    isolated_app,
):
    app = isolated_app

    _upload(app, "prior-release.xml", day=3)
    _upload(app, "current-release.xml", day=4)

    assert len(app.state.store.captures()) == 2
    assert _open_cases(app) == []


def test_package_missing_from_next_release_opens_a_no_longer_present_case(isolated_app):
    from src.domain.review_case import SimulatedMedicationRecord

    app = isolated_app
    app.state.medication_records = (
        SimulatedMedicationRecord(
            "SIM-MED-300", "SIM-PERSON-300", "Fictional Product Cedar", "SIM-PKG-300"
        ),
        # Only present in the current release: never opens a case.
        SimulatedMedicationRecord(
            "SIM-MED-400", "SIM-PERSON-400", "Fictional new pack", "SIM-PKG-400"
        ),
    )

    _upload(app, "prior-release.xml", day=3)
    _upload(app, "current-release.xml", day=4)

    (case,) = _open_cases(app)
    assert case["matchedRecord"]["recordId"] == "SIM-MED-300"
    assert case["changeSet"]["kind"] == "NO_LONGER_PRESENT"
    assert case["changeSet"]["changes"] == []
    assert case["sources"]["prior"]["fileName"] == "prior-release.xml"
    assert case["sources"]["current"]["fileName"] == "current-release.xml"
    assert case["sources"]["current"]["recordLocator"] is None
    last_known = {f["field"]: f["values"] for f in case["changeSet"]["lastKnownFields"]}
    assert last_known["Pakkaus/Pakkauskokoteksti"][0]["value"] == "synthetic prior-only pack"

    _upload(app, "current-release.xml", day=4)
    assert len(_open_cases(app)) == 1
