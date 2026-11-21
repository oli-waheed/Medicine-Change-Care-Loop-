"""Feature 007 (1a): review cases from changes in Fimea's shortage data.

Downloads are replaced by the synthetic files in tests/fixtures/fimea-shortages;
comparison, matching through the catalogue, storage and the case view are the
real code.
"""

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.config import DEFAULT_FIMEA_SHORTAGES_URL
from src.domain.review_case import SimulatedMedicationRecord
from src.services.latest_release_check import LatestReleaseCheck
from src.services.medicine_shortages import ShortageUpdate

ROOT = Path(__file__).parents[3]
SHORTAGES = ROOT / "tests" / "fixtures" / "fimea-shortages"
RELEASES = ROOT / "tests" / "fixtures" / "fimea-basic-register"
CASES = "/api/open-review-cases"
OUTCOMES = "/api/change-processing-outcomes"
CLINICAL_WORDS = re.compile(
    r"\b(urgen\w*|priorit\w*|severity|risk\w*|recommend\w*|diagnos\w*|substitut\w*|"
    r"treatment|dos(e|es|ing|age)|contraindicat\w*|interaction\w*|should)\b",
    re.IGNORECASE,
)
RECORDS = (
    SimulatedMedicationRecord("SIM-MED-S100", "SIM-PERSON-S100", "Fictional Amber", "SIM-PKG-100"),
    SimulatedMedicationRecord("SIM-MED-S500", "SIM-PERSON-S500", "Fictional Blue", "SIM-PKG-500"),
    SimulatedMedicationRecord("SIM-MED-S201", "SIM-PERSON-S201", "Fictional Blue", "SIM-PKG-200"),
    SimulatedMedicationRecord("SIM-MED-S202", "SIM-PERSON-S202", "Fictional Blue", "SIM-PKG-200"),
)


class Downloads:
    def __init__(self) -> None:
        self.files: dict[str, list[bytes]] = {}

    def add(self, url: str, name: str, folder: Path = SHORTAGES) -> None:
        self.files.setdefault(url, []).append((folder / name).read_bytes())

    def __call__(self, url, max_bytes, target) -> int:
        data = self.files[url].pop(0)
        target.write(data)
        return len(data)


@pytest.fixture
def app(isolated_app):
    downloads = Downloads()
    clock = {"now": datetime(2099, 1, 5, 6, 0, tzinfo=UTC)}
    isolated_app.state.medication_records = RECORDS
    isolated_app.state.shortage_update = ShortageUpdate(
        download=downloads, now=lambda: clock["now"]
    )
    isolated_app.state.latest_release_check = LatestReleaseCheck(download=downloads)
    isolated_app.state.shortage_reader = None
    isolated_app.state.downloads = downloads
    isolated_app.state.clock = clock
    yield isolated_app
    isolated_app.state.shortage_update = None
    isolated_app.state.latest_release_check = None
    isolated_app.state.shortage_reader = None


def _catalogue(client, app) -> None:
    app.state.downloads.add(
        app.state.source_release_config.fimea_release_url, "current-release.xml", RELEASES
    )
    client.post("/api/source-releases/latest-check")
    app.state.latest_release_check.wait(30)


def _update(client, app, name: str, day: int) -> dict:
    app.state.downloads.add(DEFAULT_FIMEA_SHORTAGES_URL, name)
    app.state.clock["now"] = datetime(2099, 1, day, 6, 0, tzinfo=UTC)
    assert client.post("/api/shortages/update").status_code == 202
    status = app.state.shortage_update.wait(30)
    assert status.phase.value == "SUCCEEDED", status
    return status.result


def _shortage_cases(client) -> list[dict]:
    cases = client.get(CASES, params={"includeReviewed": "true"}).json()
    return [case for case in cases if case["caseType"] == "SHORTAGE"]


def test_the_first_file_is_a_baseline_only(app):
    with TestClient(app) as client:
        _catalogue(client, app)
        result = _update(client, app, "shortages.txt", 5)
        assert "review" not in result
        assert _shortage_cases(client) == []


def test_changes_create_cases_and_outcomes_by_the_release_rules(app):
    with TestClient(app) as client:
        _catalogue(client, app)
        _update(client, app, "shortages.txt", 5)
        result = _update(client, app, "shortages-later.txt", 6)
        cases = _shortage_cases(client)
        outcomes = [o for o in client.get(OUTCOMES).json() if o.get("source") == "SHORTAGES"]

    assert result["review"]["changes"] == 3
    assert result["review"]["reviewCasesCreated"] == 1
    summary = sorted((o["vnr"], o["changeKind"], o["result"], o["reason"]) for o in outcomes)
    assert summary == [
        ("SIM-VNR-200", "SHORTAGE_CHANGED", "AMBIGUOUS", "MULTIPLE_SIMULATED_RECORDS"),
        ("SIM-VNR-500", "SHORTAGE_CHANGED", "MATCHED", "UNIQUE_EXACT_PACKAGE_MATCH"),
        ("SIM-VNR-900", "SHORTAGE_ENDED", "NO_MATCH", "NO_CATALOGUE_PACKAGE"),
    ]

    (case,) = cases
    assert case["status"] == "NEW"
    assert case["medicineIdentifier"] == "SIM-PKG-500"
    assert case["matchedRecord"]["recordId"] == "SIM-MED-S500"
    change = case["shortageChange"]
    assert change["kind"] == "SHORTAGE_CHANGED"
    assert change["vnr"] == "SIM-VNR-500"
    assert change["changedColumns"] == ["Valid"]
    assert change["before"] == {
        "line": 4,
        "valid": "E",
        "unavailableFrom": "2099-01-10",
        "endingDate": "2099-01-31",
        "notificationDate": "2099-01-02",
        "updated": "2099-01-02",
        "company": "Fictional Pharma Oy",
    }
    assert change["after"]["valid"] == "K"
    assert change["after"]["line"] == 3
    assert change["package"]["pakkaustunnus"] == "SIM-PKG-500"
    assert change["catalogue"]["releaseDate"] == "2099-01-02"
    assert "the end date is an estimate" in change["notice"]
    assert case["sources"]["prior"]["lineNumber"] == 4
    assert case["sources"]["prior"]["retrievedAt"] == "2099-01-05T06:00:00+00:00"
    assert case["sources"]["current"]["retrievedAt"] == "2099-01-06T06:00:00+00:00"
    assert case["sources"]["prior"]["licence"] == "CC BY 4.0"
    assert case["evidenceAvailability"] == "AVAILABLE"
    assert [(e["fromStatus"], e["toStatus"]) for e in case["statusHistory"]] == [(None, "NEW")]
    assert not CLINICAL_WORDS.search(str(case) + str(outcomes))


def test_started_and_ended_shortages_and_a_file_that_returns(app):
    with TestClient(app) as client:
        _catalogue(client, app)
        _update(client, app, "shortages.txt", 5)
        _update(client, app, "shortages-later.txt", 6)
        started = _update(client, app, "shortages-third.txt", 7)
        # The previous file comes back: it becomes active again and is compared too.
        returned = _update(client, app, "shortages-later.txt", 8)
        cases = _shortage_cases(client)

    assert started["review"]["reviewCasesCreated"] == 1
    assert returned["alreadyCaptured"] is True
    assert returned["review"]["reviewCasesCreated"] == 1
    kinds = sorted((c["shortageChange"]["kind"], c["matchedRecord"]["recordId"]) for c in cases)
    assert kinds == [
        ("SHORTAGE_CHANGED", "SIM-MED-S500"),
        ("SHORTAGE_ENDED", "SIM-MED-S100"),
        ("SHORTAGE_STARTED", "SIM-MED-S100"),
    ]
    ended = next(c for c in cases if c["shortageChange"]["kind"] == "SHORTAGE_ENDED")
    assert ended["shortageChange"]["after"] is None
    assert ended["sources"]["current"]["lineNumber"] is None
    assert ended["sources"]["current"]["note"] == "No row with this VNR in this file."


def test_processing_the_same_pair_again_adds_nothing(app):
    from src.api.medicine_shortages import shortage_review

    with TestClient(app) as client:
        _catalogue(client, app)
        first = _update(client, app, "shortages.txt", 5)
        _update(client, app, "shortages-later.txt", 6)
        before_cases = _shortage_cases(client)
        before_outcomes = client.get(OUTCOMES).json()
        store = app.state.store
        prior = store.shortage_capture_by_checksum(first["captureReference"])
        current = store.active_shortage_capture()
        again = shortage_review(app)(prior, current)
        assert again["reviewCasesCreated"] == 0
        assert _shortage_cases(client) == before_cases
        assert client.get(OUTCOMES).json() == before_outcomes


def test_without_a_catalogue_release_changes_are_recorded_without_cases(app):
    with TestClient(app) as client:
        _update(client, app, "shortages.txt", 5)
        result = _update(client, app, "shortages-later.txt", 6)
        outcomes = [o for o in client.get(OUTCOMES).json() if o.get("source") == "SHORTAGES"]
    assert result["review"]["reviewCasesCreated"] == 0
    assert {o["reason"] for o in outcomes} == {"NO_CATALOGUE_RELEASE"}
    assert len(outcomes) == 3


def test_a_shortage_case_is_reviewed_like_any_case(app):
    with TestClient(app) as client:
        _catalogue(client, app)
        _update(client, app, "shortages.txt", 5)
        _update(client, app, "shortages-later.txt", 6)
        (case,) = _shortage_cases(client)
        response = client.post(
            f"/api/review-cases/{case['caseId']}/status-events",
            json={
                "expectedStatus": "NEW",
                "toStatus": "REVIEWED_FOLLOW_UP",
                "reviewerInitials": "OW",
                "note": "Inform the care team about the new dates.",
            },
        )
        assert response.status_code == 201
        assert response.json()["caseType"] == "SHORTAGE"
        assert case["caseId"] not in [c["caseId"] for c in client.get(CASES).json()]


def test_a_removed_shortage_file_makes_the_case_evidence_unavailable(app):
    with TestClient(app) as client:
        _catalogue(client, app)
        _update(client, app, "shortages.txt", 5)
        _update(client, app, "shortages-later.txt", 6)
        (case,) = _shortage_cases(client)
        prior_file = next(
            path
            for path in app.state.source_release_config.shortage_storage_dir.iterdir()
            if path.stem == case["sources"]["prior"]["checksum"]
        )
        prior_file.unlink()
        (after,) = _shortage_cases(client)
    assert after["evidenceAvailability"] == "UNAVAILABLE"
    assert after["sources"]["prior"]["evidenceAvailable"] is False
    assert after["sources"]["current"]["evidenceAvailable"] is True
