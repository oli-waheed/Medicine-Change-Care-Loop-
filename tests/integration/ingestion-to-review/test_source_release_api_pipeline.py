
"""Integration tests for the source-release API and review workflow."""

import asyncio
import json
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from src.api.open_review_cases import get_open_review_cases
from src.api.source_release_ingestion import ingest_uploaded_source_release
from src.config import ApplicationConfig
from src.main import app
from starlette.requests import Request

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "fimea-basic-register"


def _request():
    return Request(
        {
            "type": "http",
            "app": app,
            "headers": [],
            "method": "POST",
            "path": "/api/source-releases/ingest",
            "query_string": b"",
        }
    )


def _review_request():
    return Request(
        {
            "type": "http",
            "app": app,
            "headers": [],
            "method": "GET",
            "path": "/api/open-review-cases",
            "query_string": b"",
        }
    )


def _upload_release(filename, order, retrieved_at):
    content = (FIXTURE_DIR / filename).read_bytes()
    upload = UploadFile(filename=filename, file=BytesIO(content))

    return asyncio.run(
        ingest_uploaded_source_release(
            _request(),
            upload,
            "Fimea Basic Register",
            json.dumps(
                {
                    "value": f"SIM-{filename}",
                    "evidenceClass": "VERIFIED",
                }
            ),
            json.dumps(order),
            retrieved_at.isoformat(),
        )
    )


def _prepare_app(tmp_path, medication_record):
    app.state.source_release_config = ApplicationConfig(
        tmp_path / "captures", 250 * 1024 * 1024
    )
    app.state.open_review_cases = []
    app.state.medication_records = (medication_record,)
    app.state.source_release_history = []
    app.state.source_release_comparison_baseline = None


def _restore_app(
    previous_config,
    previous_cases,
    previous_records,
    previous_history,
    previous_baseline,
):
    app.state.source_release_config = previous_config
    app.state.open_review_cases = previous_cases

    if previous_records is None:
        delattr(app.state, "medication_records")
    else:
        app.state.medication_records = previous_records

    if previous_history is None:
        delattr(app.state, "source_release_history")
    else:
        app.state.source_release_history = previous_history

    if previous_baseline is None:
        if hasattr(app.state, "source_release_comparison_baseline"):
            delattr(app.state, "source_release_comparison_baseline")
    else:
        app.state.source_release_comparison_baseline = previous_baseline


def test_sequential_api_releases_create_visible_cases_and_replay_is_idempotent(
    tmp_path, medication_record
):
    previous_config = app.state.source_release_config
    previous_cases = app.state.open_review_cases
    previous_records = getattr(app.state, "medication_records", None)
    previous_history = getattr(app.state, "source_release_history", None)
    previous_baseline = getattr(
        app.state, "source_release_comparison_baseline", None
    )

    _prepare_app(tmp_path, medication_record)

    try:
        prior_time = datetime(2099, 1, 3, tzinfo=UTC)
        current_time = datetime(2099, 1, 4, tzinfo=UTC)

        baseline = _upload_release(
            "prior-release.xml",
            {"value": "1", "evidenceClass": "VERIFIED"},
            prior_time,
        )

        assert baseline["processingStatus"] == "VALIDATED"
        assert app.state.open_review_cases == []

        current = _upload_release(
            "current-release.xml",
            {"value": "2", "evidenceClass": "VERIFIED"},
            current_time,
        )

        assert current["processingStatus"] == "VALIDATED"

        cases_after_current = get_open_review_cases(_review_request())

        assert cases_after_current
        assert all(case["status"] == "NEW" for case in cases_after_current)
        assert all(
            case["matchedRecord"]["recordId"] == "SIM-MED-100"
            for case in cases_after_current
        )

        replay = _upload_release(
            "current-release.xml",
            {"value": "2", "evidenceClass": "VERIFIED"},
            current_time,
        )

        assert replay["processingStatus"] == "VALIDATED"
        assert get_open_review_cases(_review_request()) == cases_after_current

    finally:
        _restore_app(
            previous_config,
            previous_cases,
            previous_records,
            previous_history,
            previous_baseline,
        )


def test_conflicting_release_does_not_advance_comparison_history(
    tmp_path, medication_record
):
    previous_config = app.state.source_release_config
    previous_cases = app.state.open_review_cases
    previous_records = getattr(app.state, "medication_records", None)
    previous_history = getattr(app.state, "source_release_history", None)
    previous_baseline = getattr(
        app.state, "source_release_comparison_baseline", None
    )

    _prepare_app(tmp_path, medication_record)

    try:
        first = _upload_release(
            "prior-release.xml",
            {"value": "2", "evidenceClass": "VERIFIED"},
            datetime(2099, 1, 3, tzinfo=UTC),
        )

        assert first["processingStatus"] == "VALIDATED"
        assert len(app.state.source_release_history) == 1

        original_baseline = app.state.source_release_comparison_baseline

        conflicting = _upload_release(
            "current-release.xml",
            {"value": "1", "evidenceClass": "VERIFIED"},
            datetime(2099, 1, 4, tzinfo=UTC),
        )

        assert conflicting["processingStatus"] == "VALIDATED"

        # Both releases are retained for traceability.
        assert len(app.state.source_release_history) == 2

        # The conflicting release must not replace the baseline.
        assert (
            app.state.source_release_comparison_baseline
            is original_baseline
        )

        assert app.state.open_review_cases == []

    finally:
        _restore_app(
            previous_config,
            previous_cases,
            previous_records,
            previous_history,
            previous_baseline,
        )


def test_verified_release_after_unknown_release_becomes_baseline(
    tmp_path, medication_record
):
    previous_config = app.state.source_release_config
    previous_cases = app.state.open_review_cases
    previous_records = getattr(app.state, "medication_records", None)
    previous_history = getattr(app.state, "source_release_history", None)
    previous_baseline = getattr(
        app.state, "source_release_comparison_baseline", None
    )

    _prepare_app(tmp_path, medication_record)

    try:
        unknown = _upload_release(
            "prior-release.xml",
            {"value": None, "evidenceClass": "UNKNOWN"},
            datetime(2099, 1, 3, tzinfo=UTC),
        )

        assert unknown["processingStatus"] == "VALIDATED"
        assert app.state.source_release_comparison_baseline is None
        assert app.state.open_review_cases == []

        verified = _upload_release(
            "current-release.xml",
            {"value": "2", "evidenceClass": "VERIFIED"},
            datetime(2099, 1, 4, tzinfo=UTC),
        )

        assert verified["processingStatus"] == "VALIDATED"
        assert (
            app.state.source_release_comparison_baseline.captured_release.release_id
            == verified["capturedReleaseReference"]
        )

        # Both releases are retained, but no comparison was made
        # between the UNKNOWN release and the verified release.
        assert len(app.state.source_release_history) == 2
        assert app.state.open_review_cases == []

    finally:
        _restore_app(
            previous_config,
            previous_cases,
            previous_records,
            previous_history,
            previous_baseline,
        )
