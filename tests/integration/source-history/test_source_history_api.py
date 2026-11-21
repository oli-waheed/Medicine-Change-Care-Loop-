"""Feature 010: Source History and automatic release quality checks.

Synthetic releases go through the real ingestion; the history, the checks and
the backfill are the real code.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.workflows.release_quality import backfill_quality_checks

ROOT = Path(__file__).parents[3]
RELEASES = ROOT / "tests" / "fixtures" / "fimea-basic-register"
HISTORY = "/api/source-history"


def _upload(client, name: str, day: int, content: bytes | None = None) -> dict:
    response = client.post(
        "/api/source-releases/ingest",
        files={
            "file": (
                "Perusrekisteri.xml",
                content if content is not None else (RELEASES / name).read_bytes(),
                "application/xml",
            )
        },
        data={
            "sourceName": "Fimea Basic Register",
            "sourceReleaseReference": json.dumps({"value": name, "evidenceClass": "VERIFIED"}),
            "retrievedAt": f"2099-01-{day:02d}T06:00:00+00:00",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def client(isolated_app):
    with TestClient(isolated_app) as client:
        yield client


def _checks(payload: dict) -> dict[str, str]:
    return {check["id"]: check["status"] for check in payload["checks"]}


def test_empty_history(client):
    assert client.get(HISTORY).json() == {
        "basicRegister": [],
        "qualityChecks": [],
        "uncheckedPairs": [],
        "shortageFiles": [],
    }


def test_releases_newest_first_with_retrievals(client):
    _upload(client, "prior-release.xml", 3)
    _upload(client, "current-release.xml", 4)
    _upload(client, "current-release.xml", 5)  # the same content downloaded again
    releases = client.get(HISTORY).json()["basicRegister"]
    assert [r["releaseDate"] for r in releases] == ["2099-01-02", "2099-01-01"]
    newest, older = releases
    assert newest["isCatalogueRelease"] is True and older["isCatalogueRelease"] is False
    assert newest["retrievalCount"] == 2 and older["retrievalCount"] == 1
    assert newest["firstRetrievedAt"].startswith("2099-01-04T06:00")
    assert newest["lastRetrievedAt"].startswith("2099-01-05T06:00")
    assert newest["processingStatus"] == "VALIDATED"
    assert newest["dateEvidence"] == "VERIFIED"
    assert newest["fileName"] == "Perusrekisteri.xml"
    assert len(newest["checksum"]) == 64
    assert newest["sizeBytes"] == len((RELEASES / "current-release.xml").read_bytes())
    assert newest["evidenceAvailable"] is True


def test_a_compared_pair_is_checked_automatically(client):
    _upload(client, "prior-release.xml", 3)
    history = client.get(HISTORY).json()
    assert history["qualityChecks"] == [] and history["uncheckedPairs"] == []

    _upload(client, "current-release.xml", 4)
    (check,) = client.get(HISTORY).json()["qualityChecks"]
    assert (check["priorReleaseDate"], check["currentReleaseDate"]) == (
        "2099-01-01",
        "2099-01-02",
    )
    counts = check["counts"]
    assert counts["priorPackages"] == 4 and counts["currentPackages"] == 4
    assert counts["inBoth"] == 3 and counts["noLongerPresent"] == 1 and counts["new"] == 1
    assert counts["changed"] == 2
    assert _checks(check)["RELEASE_ORDER"] == "PASSED"
    assert _checks(check)["UNIQUE_PACKAGE_IDS"] == "PASSED"
    # One of four packages removed is far above the 1 % limit: a person may look.
    assert _checks(check)["PACKAGES_REMOVED"] == "ATTENTION"
    assert check["overall"] == "ATTENTION"
    # Checks only report: the release is still the catalogue release and cases exist.
    assert client.get(HISTORY).json()["basicRegister"][0]["isCatalogueRelease"] is True
    assert client.get("/api/open-review-cases").status_code == 200


def test_an_unchanged_pair_passes(client):
    current = (RELEASES / "current-release.xml").read_bytes()
    _upload(client, "current-release.xml", 4)
    later = current.replace(b"<Ajopvm>2099-01-02</Ajopvm>", b"<Ajopvm>2099-01-09</Ajopvm>")
    _upload(client, "same-content-later-date.xml", 9, later)
    (check,) = client.get(HISTORY).json()["qualityChecks"]
    assert check["overall"] == "PASSED"
    assert check["counts"]["changed"] == 0 and check["counts"]["inBoth"] == 4
    assert {c["status"] for c in check["checks"]} <= {"PASSED", "INFO"}


def test_clean_up_labels_are_counted(client):
    _upload(client, "current-release.xml", 4)
    _upload(client, "cleanup-release.xml", 5)
    (check,) = client.get(HISTORY).json()["qualityChecks"]
    counts = check["counts"]
    assert (counts["formattingOnly"], counts["activeSubstanceOnly"], counts["unlabelled"]) == (
        1,
        1,
        1,
    )
    assert "2 of 3 changed packages" in next(
        c["detail"] for c in check["checks"] if c["id"] == "SOURCE_CLEANUPS"
    )


def test_pairs_without_a_check_are_listed_and_backfilled_once(client, isolated_app):
    # Loaded newest first: the older release is stored but never compared.
    _upload(client, "current-release.xml", 4)
    _upload(client, "prior-release.xml", 5)
    history = client.get(HISTORY).json()
    assert history["qualityChecks"] == []
    assert history["uncheckedPairs"] == [
        {"priorReleaseDate": "2099-01-01", "currentReleaseDate": "2099-01-02"}
    ]

    store = isolated_app.state.store
    assert backfill_quality_checks(store) == 1
    assert backfill_quality_checks(store) == 0
    history = client.get(HISTORY).json()
    assert len(history["qualityChecks"]) == 1 and history["uncheckedPairs"] == []


def test_history_never_changes_anything(client):
    _upload(client, "prior-release.xml", 3)
    _upload(client, "current-release.xml", 4)
    cases = client.get("/api/open-review-cases").json()
    first = client.get(HISTORY).json()
    assert client.get(HISTORY).json() == first
    assert client.get("/api/open-review-cases").json() == cases


def test_shortage_files_are_listed_newest_first(client, isolated_app):
    from datetime import UTC, datetime

    from src.services.medicine_shortages import update_shortages

    shortages = ROOT / "tests" / "fixtures" / "fimea-shortages"
    files = [shortages / "shortages.txt", shortages / "shortages.txt"]
    files.append(shortages / "shortages-later.txt")
    times = iter(datetime(2099, 1, day, 6, 0, tzinfo=UTC) for day in (3, 4, 5))

    def download(url, max_bytes, target):
        data = files.pop(0).read_bytes()
        target.write(data)
        return len(data)

    for _ in range(3):
        update_shortages(
            store=isolated_app.state.store,
            config=isolated_app.state.source_release_config,
            download=download,
            now=lambda: next(times),
        )
    newest, first = client.get(HISTORY).json()["shortageFiles"]
    assert newest["isActive"] is True and first["isActive"] is False
    assert first["retrievalCount"] == 2 and newest["retrievalCount"] == 1
    assert first["firstRetrievedAt"].startswith("2099-01-03T06:00")
    assert first["lastRetrievedAt"].startswith("2099-01-04T06:00")
    assert newest["processingStatus"] == "VALIDATED" and newest["evidenceAvailable"] is True
    assert newest["recordCount"] > 0 and newest["sizeBytes"] > 0


# --- Feature 014: field completeness, source structure, check versions -----------


def test_completeness_and_structure_are_checked(client):
    current = (RELEASES / "current-release.xml").read_bytes()
    _upload(client, "current-release.xml", 4)
    later = current.replace(b"<Ajopvm>2099-01-02</Ajopvm>", b"<Ajopvm>2099-01-09</Ajopvm>")
    _upload(client, "same-content-later-date.xml", 9, later)
    (check,) = client.get(HISTORY).json()["qualityChecks"]
    assert check["version"] == 2 and check["upToDate"] is True
    statuses = _checks(check)
    assert statuses["FIELD_COMPLETENESS"] == "PASSED"
    assert statuses["SOURCE_STRUCTURE"] == "PASSED"
    structure = next(c for c in check["checks"] if c["id"] == "SOURCE_STRUCTURE")
    assert "same as the prior release" in structure["detail"]
    vnr = next(row for row in check["completeness"] if row["field"] == "VNR-numero")
    assert vnr == {"field": "VNR-numero", "prior": 100.0, "current": 100.0}


def test_a_new_element_and_lost_values_need_attention(client):
    current = (RELEASES / "current-release.xml").read_bytes()
    _upload(client, "current-release.xml", 4)
    changed = (
        current.replace(b"<Ajopvm>2099-01-02</Ajopvm>", b"<Ajopvm>2099-01-09</Ajopvm>")
        .replace(b"<VNR-numero>SIM-VNR-100</VNR-numero>", b"")
        .replace(b"<VNR-numero>SIM-VNR-200</VNR-numero>", b"")
        .replace(
            b"<Pakkaustunnus>SIM-PKG-400</Pakkaustunnus>",
            b"<Pakkaustunnus>SIM-PKG-400</Pakkaustunnus><UusiKentta>x</UusiKentta>",
        )
    )
    _upload(client, "changed-structure.xml", 9, changed)
    (check,) = client.get(HISTORY).json()["qualityChecks"]
    statuses = _checks(check)
    assert statuses["FIELD_COMPLETENESS"] == "ATTENTION"
    assert statuses["SOURCE_STRUCTURE"] == "ATTENTION"
    details = {c["id"]: c["detail"] for c in check["checks"]}
    assert (
        "VNR-numero is present in 50.00% of packages, down from 100.00%"
        in details["FIELD_COMPLETENESS"]
    )
    assert "new: Perusrekisteri/Pakkaus/UusiKentta" in details["SOURCE_STRUCTURE"]
    assert "gone:" not in details["SOURCE_STRUCTURE"]
    assert check["overall"] == "ATTENTION"


def test_checks_of_an_older_version_are_made_again(client, isolated_app):
    _upload(client, "prior-release.xml", 3)
    _upload(client, "current-release.xml", 4)
    store = isolated_app.state.store
    (check,) = client.get(HISTORY).json()["qualityChecks"]
    old = {key: value for key, value in check.items() if key not in {"version", "upToDate"}}
    old["checks"] = [c for c in old["checks"] if c["id"] != "SOURCE_STRUCTURE"]
    old.pop("completeness")
    from src.models import ReleaseQualityCheckRow

    with store._session() as session, session.begin():
        session.get(ReleaseQualityCheckRow, check["checkId"]).payload = old
    (stale,) = client.get(HISTORY).json()["qualityChecks"]
    assert stale["upToDate"] is False

    assert backfill_quality_checks(store) == 1
    assert backfill_quality_checks(store) == 0
    (fresh,) = client.get(HISTORY).json()["qualityChecks"]
    assert fresh["upToDate"] is True and "SOURCE_STRUCTURE" in _checks(fresh)
