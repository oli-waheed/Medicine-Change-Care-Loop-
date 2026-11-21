"""Feature 006: Fimea shortage data, the Update button and the daily update.

Downloads are replaced by the synthetic files in tests/fixtures/fimea-shortages;
storing, parsing, matching by VNR and the schedule are the real code.
"""

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.daily_updates import run_daily_jobs, utc_offset
from src.config import DEFAULT_FIMEA_SHORTAGES_URL, ApplicationConfig, parse_daily_update_time
from src.services.daily_updates import DailyUpdateScheduler
from src.services.latest_release_check import DownloadError, LatestReleaseCheck
from src.services.medicine_shortages import ShortageUpdate, parse_shortage_file

ROOT = Path(__file__).parents[3]
SHORTAGES = ROOT / "tests" / "fixtures" / "fimea-shortages"
RELEASES = ROOT / "tests" / "fixtures" / "fimea-basic-register"
API = "/api/shortages"
CLINICAL_WORDS = re.compile(
    r"\b(urgen\w*|priorit\w*|severity|risk\w*|recommend\w*|diagnos\w*|substitut\w*|"
    r"treatment|dos(e|es|ing|age)|contraindicat\w*|interaction\w*|should)\b",
    re.IGNORECASE,
)


class FakeDownloads:
    """Serves fixture files in place of Fimea, by URL."""

    def __init__(self) -> None:
        self.files: dict[str, list[bytes]] = {}
        self.calls: list[str] = []
        self.error: str | None = None

    def add(self, url: str, data: bytes) -> None:
        self.files.setdefault(url, []).append(data)

    def __call__(self, url: str, max_bytes: int, target) -> int:
        self.calls.append(url)
        if self.error:
            raise DownloadError(self.error)
        data = self.files[url].pop(0)
        target.write(data)
        return len(data)


@pytest.fixture
def fimea(isolated_app):
    fake = FakeDownloads()
    clock = {"now": datetime(2099, 1, 5, 6, 0, tzinfo=UTC)}
    isolated_app.state.shortage_update = ShortageUpdate(download=fake, now=lambda: clock["now"])
    isolated_app.state.latest_release_check = LatestReleaseCheck(download=fake)
    isolated_app.state.shortage_reader = None
    fake.clock = clock
    yield fake
    isolated_app.state.shortage_update = None
    isolated_app.state.latest_release_check = None
    isolated_app.state.shortage_reader = None


def _update(client, app) -> dict:
    response = client.post(f"{API}/update")
    assert response.status_code == 202
    app.state.shortage_update.wait(30)
    return client.get(f"{API}/update").json()


def _load_catalogue(client, app, fimea) -> None:
    fimea.add(
        app.state.source_release_config.fimea_release_url,
        (RELEASES / "current-release.xml").read_bytes(),
    )
    client.post("/api/source-releases/latest-check")
    app.state.latest_release_check.wait(30)


def test_the_real_file_format_is_parsed_as_published():
    records = parse_shortage_file((SHORTAGES / "shortages.txt").read_bytes())
    assert [(r.line, r.vnr, r.valid) for r in records] == [
        (2, "SIM-VNR-200", "K"),
        (3, "SIM-VNR-900", "K"),
        (4, "SIM-VNR-500", "E"),
    ]
    assert records[0].unavailable_from == "2099-01-01"
    assert records[0].ending_date == "2099-02-15"
    assert records[0].notification_date == "2098-12-01"
    assert records[0].updated == "2099-01-02"
    assert records[0].company == "Fictional Pharma Oy"


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"", "empty"),
        ((SHORTAGES / "shortages-wrong-columns.txt").read_bytes(), "expected columns"),
        (
            b'"NordicArticleNumber";"Valid";"UnavailableFrom";"EndingDate";'
            b'"DateOfTheNotification";"Updated";"Company"\r\n"SIM-1";"K";"2099-01-01"\r\n',
            "Line 2 has 3 values",
        ),
        (
            b'"NordicArticleNumber";"Valid";"UnavailableFrom";"EndingDate";'
            b'"DateOfTheNotification";"Updated";"Company"\r\n'
            b'"SIM-1";"K";"1.1.2099";"";"";"";"X"\r\n',
            "is not a YYYY-MM-DD date",
        ),
        (
            b'"NordicArticleNumber";"Valid";"UnavailableFrom";"EndingDate";'
            b'"DateOfTheNotification";"Updated";"Company"\r\n'
            b'"SIM-1";"K";"";"";"";"";"X"\r\n"SIM-1";"E";"";"";"";"";"X"\r\n',
            "repeats VNR SIM-1 from line 2",
        ),
        (b"\xff\xfe", "not UTF-8"),
    ],
)
def test_files_that_do_not_match_the_format_are_rejected(data, message):
    with pytest.raises(ValueError, match=message):
        parse_shortage_file(data)


def test_no_data_before_the_first_download(isolated_app, fimea):
    with TestClient(isolated_app) as client:
        response = client.get(API)
        status = client.get(f"{API}/update").json()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "SHORTAGES_UNAVAILABLE"
    assert status["phase"] == "IDLE"
    assert fimea.calls == []


def test_the_update_button_downloads_stores_and_lists_the_file(isolated_app, fimea):
    data = (SHORTAGES / "shortages.txt").read_bytes()
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, data)
    with TestClient(isolated_app) as client:
        status = _update(client, isolated_app)
        listing = client.get(API).json()

    assert fimea.calls == [DEFAULT_FIMEA_SHORTAGES_URL]
    assert status["phase"] == "SUCCEEDED"
    assert status["trigger"] == "BUTTON"
    assert status["result"]["processingStatus"] == "VALIDATED"
    assert status["result"]["alreadyCaptured"] is False
    assert status["result"]["recordCount"] == 3
    assert status["result"]["downloadedBytes"] == len(data)

    source = listing["source"]
    assert source["sourceUrl"] == DEFAULT_FIMEA_SHORTAGES_URL
    assert source["captureReference"] == status["result"]["captureReference"]
    assert source["recordCount"] == 3
    assert source["sizeBytes"] == len(data)
    assert source["lastRetrievedAt"] == "2099-01-05T06:00:00+00:00"
    assert source["latestUpdated"] == "2099-01-02"
    assert source["licence"] == "CC BY 4.0"
    assert listing["validCounts"] == {"E": 1, "K": 2}
    # Without a catalogue release the shortages are still shown, without packages.
    assert listing["catalogue"]["status"] == "UNAVAILABLE"
    assert [item["vnr"] for item in listing["items"]] == [
        "SIM-VNR-200",
        "SIM-VNR-900",
        "SIM-VNR-500",
    ]
    assert listing["items"][0] == {
        "line": 2,
        "vnr": "SIM-VNR-200",
        "valid": "K",
        "unavailableFrom": "2099-01-01",
        "endingDate": "2099-02-15",
        "notificationDate": "2098-12-01",
        "updated": "2099-01-02",
        "company": "Fictional Pharma Oy",
        "packages": None,
    }

    # The raw file is kept once, named by its checksum.
    stored = list(isolated_app.state.source_release_config.shortage_storage_dir.iterdir())
    assert [path.read_bytes() for path in stored] == [data]


def test_shortages_are_matched_to_catalogue_packages_by_vnr(isolated_app, fimea):
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, (SHORTAGES / "shortages.txt").read_bytes())
    with TestClient(isolated_app) as client:
        _load_catalogue(client, isolated_app, fimea)
        _update(client, isolated_app)
        listing = client.get(API).json()
        by_name = client.get(API, params={"q": "product blue"}).json()
        not_short = client.get(API, params={"q": "amber"}).json()
        by_company = client.get(API, params={"q": "synthetic medicines"}).json()
        by_vnr = client.get(API, params={"q": "vnr-500"}).json()
        upcoming = client.get(API, params={"valid": "E"}).json()

    assert listing["catalogue"]["status"] == "READY"
    assert listing["catalogue"]["releaseDate"] == "2099-01-02"
    packages = {item["vnr"]: item["packages"] for item in listing["items"]}
    assert [p["pakkaustunnus"] for p in packages["SIM-VNR-200"]] == ["SIM-PKG-200"]
    assert packages["SIM-VNR-200"][0]["productName"]["value"] == "Fictional Product Blue"
    assert packages["SIM-VNR-900"] == []  # in the shortage file, not in the catalogue
    assert [p["pakkaustunnus"] for p in packages["SIM-VNR-500"]] == ["SIM-PKG-500"]
    assert [item["vnr"] for item in by_name["items"]] == ["SIM-VNR-200", "SIM-VNR-500"]
    assert not_short["items"] == []  # Amber's VNR is not in the shortage file
    assert [item["vnr"] for item in by_company["items"]] == ["SIM-VNR-900"]
    assert [item["vnr"] for item in by_vnr["items"]] == ["SIM-VNR-500"]
    assert [item["vnr"] for item in upcoming["items"]] == ["SIM-VNR-500"]


def test_the_list_does_not_wait_for_the_catalogue(isolated_app, fimea):
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, (SHORTAGES / "shortages.txt").read_bytes())
    with TestClient(isolated_app) as client:
        _load_catalogue(client, isolated_app, fimea)
        _update(client, isolated_app)
        isolated_app.state.medicine_catalogue = None  # as after a backend restart
        first = client.get(API).json()
        isolated_app.state.medicine_catalogue._warming.join(30)
        second = client.get(API).json()
    assert first["catalogue"]["status"] == "LOADING"
    assert all(item["packages"] is None for item in first["items"])
    assert second["catalogue"]["status"] == "READY"


def test_an_unchanged_file_is_recorded_but_not_stored_twice(isolated_app, fimea):
    data = (SHORTAGES / "shortages.txt").read_bytes()
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, data)
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, data)
    with TestClient(isolated_app) as client:
        first = _update(client, isolated_app)
        fimea.clock["now"] = datetime(2099, 1, 6, 6, 0, tzinfo=UTC)
        second = _update(client, isolated_app)
        listing = client.get(API).json()
    assert second["result"]["alreadyCaptured"] is True
    assert second["result"]["captureReference"] == first["result"]["captureReference"]
    assert listing["source"]["retrievalCount"] == 2
    assert listing["source"]["firstRetrievedAt"] == "2099-01-05T06:00:00+00:00"
    assert listing["source"]["lastRetrievedAt"] == "2099-01-06T06:00:00+00:00"
    assert len(list(isolated_app.state.source_release_config.shortage_storage_dir.iterdir())) == 1


def test_a_later_file_replaces_the_list(isolated_app, fimea):
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, (SHORTAGES / "shortages.txt").read_bytes())
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, (SHORTAGES / "shortages-later.txt").read_bytes())
    with TestClient(isolated_app) as client:
        _update(client, isolated_app)
        fimea.clock["now"] = datetime(2099, 1, 6, 6, 0, tzinfo=UTC)
        _update(client, isolated_app)
        listing = client.get(API).json()
    assert [(i["vnr"], i["valid"], i["endingDate"]) for i in listing["items"]] == [
        ("SIM-VNR-200", "K", "2099-03-31"),
        ("SIM-VNR-500", "K", "2099-01-31"),
    ]


def test_a_rejected_file_or_failed_download_keeps_the_previous_list(isolated_app, fimea):
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, (SHORTAGES / "shortages.txt").read_bytes())
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, (SHORTAGES / "shortages-wrong-columns.txt").read_bytes())
    with TestClient(isolated_app) as client:
        _update(client, isolated_app)
        fimea.clock["now"] = datetime(2099, 1, 6, 6, 0, tzinfo=UTC)
        rejected = _update(client, isolated_app)
        fimea.error = "Could not reach Fimea: timed out."
        failed = _update(client, isolated_app)
        listing = client.get(API).json()
    assert rejected["phase"] == "FAILED"
    assert rejected["error"].startswith("The shortage file was not accepted:")
    assert rejected["result"]["processingStatus"] == "FAILED"
    assert failed["phase"] == "FAILED"
    assert failed["error"] == "Could not reach Fimea: timed out."
    assert listing["source"]["recordCount"] == 3


def test_a_tampered_stored_file_is_reported_not_shown(isolated_app, fimea):
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, (SHORTAGES / "shortages.txt").read_bytes())
    with TestClient(isolated_app) as client:
        _update(client, isolated_app)
        (stored,) = isolated_app.state.source_release_config.shortage_storage_dir.iterdir()
        stored.write_bytes(stored.read_bytes().replace(b"2099-02-15", b"2099-02-16"))
        isolated_app.state.shortage_reader = None
        response = client.get(API)
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "SHORTAGES_SOURCE_UNREADABLE"


def test_listing_parameters_are_checked(isolated_app, fimea):
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, (SHORTAGES / "shortages.txt").read_bytes())
    with TestClient(isolated_app) as client:
        _update(client, isolated_app)
        assert client.get(API, params={"page": 0}).status_code == 422
        assert client.get(API, params={"pageSize": 201}).status_code == 422
        paged = client.get(API, params={"pageSize": 2, "page": 2}).json()
    assert paged["total"] == 3
    assert [item["vnr"] for item in paged["items"]] == ["SIM-VNR-500"]


def test_shortage_data_never_changes_review_cases(isolated_app, fimea):
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, (SHORTAGES / "shortages.txt").read_bytes())
    with TestClient(isolated_app) as client:
        before = client.get("/api/open-review-cases").json()
        status = _update(client, isolated_app)
        listing = client.get(API).json()
        after = client.get("/api/open-review-cases").json()
    assert before == after
    assert not CLINICAL_WORDS.search(str(status) + str(listing))


# --- daily automatic update -----------------------------------------------------------


def test_daily_update_time_setting():
    assert parse_daily_update_time("6:5") == "06:05"
    assert parse_daily_update_time("off") is None
    assert parse_daily_update_time(None) is None
    with pytest.raises(ValueError, match="HH:MM"):
        parse_daily_update_time("25:00")
    # The page shows the machine's offset, not a system-specific zone name (T017).
    assert utc_offset(datetime.fromisoformat("2099-01-05T06:00:00+02:00")) == "UTC+02:00"
    assert utc_offset(datetime.fromisoformat("2099-01-05T06:00:00-05:30")) == "UTC-05:30"
    assert utc_offset(datetime(2099, 1, 5, tzinfo=UTC)) == "UTC+00:00"
    # Built directly (as in tests) there is no daily update.
    assert ApplicationConfig(Path("x"), 1).daily_update_time is None


def test_the_daily_update_runs_once_a_day_from_the_set_time(isolated_app, fimea):
    config = isolated_app.state.source_release_config
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, (SHORTAGES / "shortages.txt").read_bytes())
    fimea.add(config.fimea_release_url, (RELEASES / "prior-release.xml").read_bytes())
    local = {"now": datetime.fromisoformat("2099-01-05T05:59:00+02:00")}
    scheduler = DailyUpdateScheduler(
        store=isolated_app.state.store,
        update_time="06:00",
        run_jobs=lambda: run_daily_jobs(isolated_app),
        now=lambda: local["now"],
    )

    assert scheduler.tick() is False  # before 06:00
    local["now"] = datetime.fromisoformat("2099-01-05T06:00:00+02:00")
    assert scheduler.tick() is True
    assert scheduler.tick() is False  # already ran today
    # A new scheduler (a backend restart) on the same day does not repeat the run.
    again = DailyUpdateScheduler(
        store=isolated_app.state.store,
        update_time="06:00",
        run_jobs=lambda: pytest.fail("ran twice on one day"),
        now=lambda: local["now"],
    )
    assert again.tick() is False

    assert fimea.calls == [DEFAULT_FIMEA_SHORTAGES_URL, config.fimea_release_url]
    with TestClient(isolated_app) as client:
        daily = client.get("/api/daily-updates").json()
        shortages = client.get(API).json()
        source = client.get("/api/medicine-catalogue/source").json()
    assert daily["enabled"] is False  # this test configuration has no schedule of its own
    run = daily["lastRun"]
    assert run["date"] == "2099-01-05"
    assert run["trigger"] == "SCHEDULE"
    assert run["finishedAt"] is not None
    assert run["outcome"]["shortages"]["phase"] == "SUCCEEDED"
    assert run["outcome"]["shortages"]["trigger"] == "SCHEDULE"
    assert run["outcome"]["basicRegister"]["phase"] == "SUCCEEDED"
    assert run["outcome"]["basicRegister"]["result"]["releaseDate"] == "2099-01-01"
    assert shortages["source"]["recordCount"] == 3
    assert source["release"]["releaseDate"]["value"] == "2099-01-01"

    # The next day it runs again.
    fimea.add(DEFAULT_FIMEA_SHORTAGES_URL, (SHORTAGES / "shortages.txt").read_bytes())
    fimea.add(config.fimea_release_url, (RELEASES / "prior-release.xml").read_bytes())
    local["now"] = datetime.fromisoformat("2099-01-06T07:30:00+02:00")
    assert scheduler.tick() is True


def test_a_failed_daily_update_is_recorded_and_not_retried_the_same_day(isolated_app, fimea):
    fimea.error = "Could not reach Fimea: timed out."
    local = {"now": datetime.fromisoformat("2099-01-05T09:00:00+02:00")}
    scheduler = DailyUpdateScheduler(
        store=isolated_app.state.store,
        update_time="06:00",
        run_jobs=lambda: run_daily_jobs(isolated_app),
        now=lambda: local["now"],
    )
    assert scheduler.tick() is True
    assert scheduler.tick() is False
    with TestClient(isolated_app) as client:
        run = client.get("/api/daily-updates").json()["lastRun"]
    assert run["outcome"]["shortages"]["error"] == "Could not reach Fimea: timed out."
    assert run["outcome"]["basicRegister"]["error"] == "Could not reach Fimea: timed out."


def test_the_backend_starts_the_daily_update_only_when_configured(isolated_app, fimea):
    with TestClient(isolated_app):
        assert isolated_app.state.daily_update_scheduler is None
