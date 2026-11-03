import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from src.api import source_release_ingestion
from src.config import ApplicationConfig
from src.main import app

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "fimea-basic-register"


@pytest.fixture
def api(tmp_path):
    previous_config = app.state.source_release_config
    app.state.source_release_config = ApplicationConfig(tmp_path / "captures", 250 * 1024 * 1024)
    yield
    app.state.source_release_config = previous_config


def _form_data(*, order=None, reference=None, retrieved_at=None):
    return {
        "sourceName": "Fimea Basic Register",
        "sourceReleaseReference": json.dumps(
            reference or {"value": "SIM-2099-001", "evidenceClass": "VERIFIED"}
        ),
        "sourceOrder": json.dumps(order or {"value": "1", "evidenceClass": "VERIFIED"}),
        "retrievedAt": retrieved_at or datetime(2099, 1, 4, tzinfo=UTC).isoformat(),
    }


def _post_file(filename="prior-release.xml", *, content=None, data=None):
    content = content if content is not None else (FIXTURE_DIR / filename).read_bytes()
    fields = data or _form_data()
    boundary = "source-release-test-boundary"
    parts = []
    for field_name, value in fields.items():
        parts.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{field_name}"\r\n\r\n'.encode(),
                value.encode(),
                b"\r\n",
            ]
        )
    parts.extend(
        [
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                "Content-Type: application/xml\r\n\r\n"
            ).encode(),
            content,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    body = b"".join(parts)
    sent = False
    messages = []

    async def receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/source-releases/ingest",
        "raw_path": b"/api/source-releases/ingest",
        "query_string": b"",
        "headers": [
            (b"content-type", f"multipart/form-data; boundary={boundary}".encode()),
            (b"content-length", str(len(body)).encode()),
        ],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    asyncio.run(app(scope, receive, send))
    response_status = next(
        message["status"] for message in messages if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )

    class ApiResponse:
        status_code = response_status

        @staticmethod
        def json():
            return json.loads(response_body)

    return ApiResponse()


def test_successful_upload_returns_capture_reference_and_preserves_capture(
    api, monkeypatch
):
    content = (FIXTURE_DIR / "prior-release.xml").read_bytes()
    temporary_paths = []
    real_named_temporary_file = source_release_ingestion.tempfile.NamedTemporaryFile

    def record_temporary_file(*args, **kwargs):
        temporary_file = real_named_temporary_file(*args, **kwargs)
        temporary_paths.append(Path(temporary_file.name))
        return temporary_file

    monkeypatch.setattr(
        source_release_ingestion.tempfile, "NamedTemporaryFile", record_temporary_file
    )

    response = _post_file(content=content)

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "processingStatus",
        "chronologyStatus",
        "capturedReleaseReference",
        "failureDetail",
    }
    assert payload["processingStatus"] == "VALIDATED"
    assert payload["chronologyStatus"] == "AVAILABLE"
    assert payload["failureDetail"] is None
    assert payload["capturedReleaseReference"].startswith("sha256-")
    assert app.state.open_review_cases == []
    capture_dir = app.state.source_release_config.source_release_storage_dir
    captured_file = next(capture_dir.glob("*/files/0001/prior-release.xml"))
    assert captured_file.read_bytes() == content
    manifest = json.loads((captured_file.parents[2] / "manifest.json").read_text())
    assert manifest["files"][0]["checksum"] == hashlib.sha256(content).hexdigest()
    assert temporary_paths
    assert all(not path.exists() for path in temporary_paths)


def test_validation_failure_is_reported_as_ingestion_outcome(api):
    response = _post_file("malformed-release.xml")

    assert response.status_code == 200
    assert response.json()["processingStatus"] == "FAILED"
    assert response.json()["capturedReleaseReference"].startswith("sha256-")
    assert response.json()["failureDetail"]


def test_unknown_source_order_reports_unavailable_chronology(api):
    response = _post_file(
        data=_form_data(order={"value": None, "evidenceClass": "UNKNOWN"}),
    )

    assert response.status_code == 200
    assert response.json()["processingStatus"] == "VALIDATED"
    assert response.json()["chronologyStatus"] == "UNAVAILABLE"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sourceReleaseReference", "{invalid json"),
        ("sourceOrder", '{"value":"1","evidenceClass":"NOT_A_CLASS"}'),
        ("retrievedAt", "not-a-timestamp"),
        ("sourceName", "Unsupported source"),
    ],
)
def test_invalid_metadata_returns_http_422(api, field, value):
    data = _form_data()
    data[field] = value

    response = _post_file(data=data)

    assert response.status_code == 422


def test_oversized_upload_returns_http_413_and_cleans_temporary_file(api, monkeypatch):
    config = app.state.source_release_config
    app.state.source_release_config = ApplicationConfig(config.source_release_storage_dir, 4)
    created_paths = []
    real_named_temporary_file = source_release_ingestion.tempfile.NamedTemporaryFile

    def record_temporary_file(*args, **kwargs):
        temporary_file = real_named_temporary_file(*args, **kwargs)
        created_paths.append(Path(temporary_file.name))
        return temporary_file

    monkeypatch.setattr(
        source_release_ingestion.tempfile, "NamedTemporaryFile", record_temporary_file
    )

    response = _post_file(content=b"12345")

    assert response.status_code == 413
    assert created_paths
    assert all(not path.exists() for path in created_paths)
    assert not list(config.source_release_storage_dir.glob("**/manifest.json"))


def test_temporary_file_is_removed_after_ingestion_exception(api, monkeypatch):
    created_paths = []
    real_named_temporary_file = source_release_ingestion.tempfile.NamedTemporaryFile

    def record_temporary_file(*args, **kwargs):
        temporary_file = real_named_temporary_file(*args, **kwargs)
        created_paths.append(Path(temporary_file.name))
        return temporary_file

    def raise_ingestion_error(*args, **kwargs):
        raise RuntimeError("unexpected ingestion error")

    monkeypatch.setattr(
        source_release_ingestion.tempfile, "NamedTemporaryFile", record_temporary_file
    )
    monkeypatch.setattr(source_release_ingestion, "ingest_source_release", raise_ingestion_error)

    with pytest.raises(RuntimeError, match="unexpected ingestion error"):
        _post_file()

    assert created_paths
    assert all(not path.exists() for path in created_paths)
