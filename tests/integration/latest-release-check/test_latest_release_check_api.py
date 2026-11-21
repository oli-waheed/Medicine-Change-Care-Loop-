"""Feature 005: check Fimea for the latest release from the app.

The download is replaced by local fixture files; everything after it (capture,
duplicate detection, chronology, comparison and review cases) is the real code.
"""

import re
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.config import DEFAULT_FIMEA_RELEASE_URL
from src.services.latest_release_check import (
    DownloadError,
    LatestReleaseCheck,
    download_release,
)
from src.services.simulated_medication_records import load_simulated_medication_records

ROOT = Path(__file__).parents[3]
RELEASES = ROOT / "tests" / "fixtures" / "fimea-basic-register"
RECORDS_FILE = (
    ROOT / "tests" / "fixtures" / "simulated-medication-records" / "medication-records.json"
)
API = "/api/source-releases/latest-check"
CLINICAL_WORDS = re.compile(
    r"\b(urgen\w*|priorit\w*|severity|risk\w*|recommend\w*|diagnos\w*|substitut\w*|"
    r"treatment|dos(e|es|ing|age)|contraindicat\w*|interaction\w*|should)\b",
    re.IGNORECASE,
)


class FakeFimea:
    """Serves fixture files in place of the Fimea download, recording each call."""

    def __init__(self) -> None:
        self.files: list[bytes] = []
        self.calls: list[tuple[str, int]] = []
        self.error: str | None = None

    def __call__(self, url: str, max_bytes: int, target) -> int:
        self.calls.append((url, max_bytes))
        if self.error:
            raise DownloadError(self.error)
        data = self.files.pop(0)
        target.write(data)
        return len(data)


@pytest.fixture
def fimea(isolated_app):
    fake = FakeFimea()
    isolated_app.state.latest_release_check = LatestReleaseCheck(
        download=fake, now=lambda: datetime(2099, 1, 5, 6, 0, tzinfo=UTC)
    )
    isolated_app.state.medication_records = load_simulated_medication_records(RECORDS_FILE)
    yield fake
    isolated_app.state.latest_release_check = None


def _run_check(client, app) -> dict:
    response = client.post(API)
    assert response.status_code == 202
    app.state.latest_release_check.wait(30)
    return client.get(API).json()


def test_status_is_idle_before_any_check(isolated_app, fimea):
    with TestClient(isolated_app) as client:
        assert client.get(API).json() == {
            "phase": "IDLE",
            "running": False,
            "sourceUrl": None,
            "startedAt": None,
            "finishedAt": None,
            "downloadedBytes": None,
            "result": None,
            "error": None,
        }
    assert fimea.calls == []


def test_a_new_release_is_downloaded_ingested_and_prepared(isolated_app, fimea):
    data = (RELEASES / "prior-release.xml").read_bytes()
    fimea.files.append(data)
    with TestClient(isolated_app) as client:
        started = client.post(API)
        assert started.status_code == 202
        assert started.json()["started"] is True
        assert started.json()["running"] is True
        isolated_app.state.latest_release_check.wait(30)
        status = client.get(API).json()

        assert status["phase"] == "SUCCEEDED"
        assert status["running"] is False
        assert status["sourceUrl"] == DEFAULT_FIMEA_RELEASE_URL
        assert status["startedAt"] == "2099-01-05T06:00:00+00:00"
        assert status["finishedAt"] == "2099-01-05T06:00:00+00:00"
        assert status["downloadedBytes"] == len(data)
        assert status["error"] is None
        result = status["result"]
        assert result["processingStatus"] == "VALIDATED"
        assert result["chronologyStatus"] == "AVAILABLE"
        assert result["alreadyCaptured"] is False
        assert result["releaseDate"] == "2099-01-01"
        assert result["reviewCasesCreated"] == 0
        assert result["capturedReleaseReference"].startswith("sha256-")

        # The catalogue was prepared during the check and shows the new release.
        service = isolated_app.state.medicine_catalogue
        assert service._cached_release_id == result["capturedReleaseReference"]
        source = client.get("/api/medicine-catalogue/source").json()
        assert source["release"]["releaseId"] == result["capturedReleaseReference"]
        assert source["release"]["releaseDate"]["value"] == "2099-01-01"

    # Same URL and size limit as the configuration, like the n8n workflow.
    config = isolated_app.state.source_release_config
    assert fimea.calls == [(config.fimea_release_url, config.max_source_release_upload_bytes)]


def test_an_unchanged_file_is_recognised_and_not_stored_twice(isolated_app, fimea):
    data = (RELEASES / "prior-release.xml").read_bytes()
    fimea.files.extend([data, data])
    with TestClient(isolated_app) as client:
        first = _run_check(client, isolated_app)
        second = _run_check(client, isolated_app)
    assert second["phase"] == "SUCCEEDED"
    assert second["result"]["alreadyCaptured"] is True
    assert (
        second["result"]["capturedReleaseReference"] == first["result"]["capturedReleaseReference"]
    )
    assert second["result"]["reviewCasesCreated"] == 0
    captures = list((isolated_app.state.source_release_config.source_release_storage_dir).iterdir())
    assert len(captures) == 1


def test_a_newer_release_creates_review_cases_like_an_upload(isolated_app, fimea):
    fimea.files.extend(
        [
            (RELEASES / "prior-release.xml").read_bytes(),
            (RELEASES / "current-release.xml").read_bytes(),
        ]
    )
    with TestClient(isolated_app) as client:
        _run_check(client, isolated_app)
        status = _run_check(client, isolated_app)
        cases = client.get("/api/open-review-cases").json()

    assert status["phase"] == "SUCCEEDED"
    assert status["result"]["releaseDate"] == "2099-01-02"
    assert status["result"]["reviewCasesCreated"] == len(cases)
    assert len(cases) > 0
    assert all(case["status"] == "NEW" for case in cases)


def test_a_failed_download_is_reported_and_stores_nothing(isolated_app, fimea):
    fimea.error = "Could not reach Fimea: timed out."
    with TestClient(isolated_app) as client:
        status = _run_check(client, isolated_app)
        assert client.get("/api/open-review-cases").json() == []
    assert status["phase"] == "FAILED"
    assert status["error"] == "Could not reach Fimea: timed out."
    assert status["result"] is None
    storage = isolated_app.state.source_release_config.source_release_storage_dir
    assert not storage.exists() or list(storage.iterdir()) == []


def test_a_file_that_does_not_validate_is_reported_as_not_accepted(isolated_app, fimea):
    fimea.files.append((RELEASES / "malformed-release.xml").read_bytes())
    with TestClient(isolated_app) as client:
        status = _run_check(client, isolated_app)
        unavailable = client.get("/api/medicine-catalogue/source")
    assert status["phase"] == "FAILED"
    assert status["error"].startswith("The release was not accepted:")
    assert status["result"]["processingStatus"] == "FAILED"
    # A rejected release never becomes the catalogue baseline.
    assert unavailable.status_code == 503


def test_only_one_check_runs_at_a_time(isolated_app, fimea):
    release = threading.Event()
    data = (RELEASES / "prior-release.xml").read_bytes()

    def slow_download(url, max_bytes, target):
        fimea.calls.append((url, max_bytes))
        release.wait(30)
        target.write(data)
        return len(data)

    isolated_app.state.latest_release_check = LatestReleaseCheck(download=slow_download)
    with TestClient(isolated_app) as client:
        first = client.post(API).json()
        second = client.post(API).json()
        during = client.get(API).json()
        release.set()
        isolated_app.state.latest_release_check.wait(30)
        after = client.get(API).json()

    assert first["started"] is True
    assert second["started"] is False
    assert second["phase"] == "DOWNLOADING"
    assert during["running"] is True
    assert len(fimea.calls) == 1
    assert after["phase"] == "SUCCEEDED"


def test_responses_use_no_clinical_wording(isolated_app, fimea):
    fimea.files.append((RELEASES / "malformed-release.xml").read_bytes())
    with TestClient(isolated_app) as client:
        status = _run_check(client, isolated_app)
    assert not CLINICAL_WORDS.search(str(status))


def test_download_streams_the_file_and_enforces_the_size_limit(tmp_path):
    source = tmp_path / "Perusrekisteri.xml"
    source.write_bytes(b"<x>" + b"a" * 5000 + b"</x>")
    target = tmp_path / "copy.xml"
    with target.open("wb") as handle:
        assert download_release(source.as_uri(), 10_000, handle) == source.stat().st_size
    assert target.read_bytes() == source.read_bytes()

    with (
        (tmp_path / "too-big.xml").open("wb") as handle,
        pytest.raises(DownloadError, match="larger than the configured maximum of 100 bytes"),
    ):
        download_release(source.as_uri(), 100, handle)

    empty = tmp_path / "empty.xml"
    empty.write_bytes(b"")
    with (tmp_path / "copy2.xml").open("wb") as handle, pytest.raises(DownloadError, match="empty"):
        download_release(empty.as_uri(), 100, handle)

    with (
        (tmp_path / "copy3.xml").open("wb") as handle,
        pytest.raises(DownloadError, match="Could not reach Fimea"),
    ):
        download_release((tmp_path / "missing.xml").as_uri(), 100, handle)
