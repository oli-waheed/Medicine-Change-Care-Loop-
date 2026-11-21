"""Feature 016: supply signals — shortage and register facts side by side.

Synthetic releases and shortage files go through the real ingestion and update;
the signals are the real code.
"""

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.services.medicine_shortages import update_shortages

ROOT = Path(__file__).parents[3]
RELEASES = ROOT / "tests" / "fixtures" / "fimea-basic-register"
SHORTAGES = ROOT / "tests" / "fixtures" / "fimea-shortages"
API = "/api/medicine-catalogue"
CLINICAL = ("risk", "recommend", "should", "substitut", "urgent", "forecast is")


def _upload(client, name: str, day: int, content: bytes | None = None) -> None:
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


def _download(app, names: list[str]) -> None:
    for day, name in enumerate(names, start=1):

        def download(url, max_bytes, target, name=name):
            data = (SHORTAGES / name).read_bytes()
            target.write(data)
            return len(data)

        update_shortages(
            store=app.state.store,
            config=app.state.source_release_config,
            download=download,
            now=lambda day=day: datetime(2099, 1, day, 5, 0, tzinfo=UTC),
        )


@pytest.fixture
def app(isolated_app):
    for name in ("shortage_reader", "link_index_cache", "stored_shortage_files"):
        setattr(isolated_app.state, name, None)
    return isolated_app


def _signals(client, path: str) -> dict:
    response = client.get(f"{API}/{path}/supply-signals")
    assert response.status_code == 200, response.text
    return response.json()


def test_a_listed_package_with_days_and_earlier_listings(app):
    with TestClient(app) as client:
        _upload(client, "current-release.xml", 4)
        _download(app, ["shortages.txt", "shortages-later.txt", "shortages-third.txt"])
        signals = _signals(client, "packages/SIM-PKG-500")
    assert signals["status"] == "LISTED"
    assert signals["vnrs"] == ["SIM-VNR-500"]
    (row,) = signals["current"]
    assert (row["valid"], row["unavailableFrom"], row["endingDate"]) == (
        "K",
        "2099-01-10",
        "2099-01-31",
    )
    today = date.fromisoformat(signals["asOf"])
    assert row["daysSinceUnavailableFrom"] == (today - date(2099, 1, 10)).days
    assert row["daysUntilEstimatedEnd"] == (date(2099, 1, 31) - today).days
    (listing,) = signals["listings"]
    assert listing["downloads"] == 3 and listing["listedNow"] is True
    assert listing["firstSeen"].startswith("2099-01-01T05:00")
    assert listing["lastSeen"].startswith("2099-01-03T05:00")
    assert signals["downloadsChecked"] == 3 and signals["unreadableDownloads"] == 0
    text = json.dumps(signals).casefold()
    assert not any(word in text for word in CLINICAL)


def test_a_listing_that_ended_and_a_package_not_listed(app):
    with TestClient(app) as client:
        _upload(client, "current-release.xml", 4)
        _download(app, ["shortages-third.txt", "shortages.txt"])
        signals = _signals(client, "packages/SIM-PKG-100")
    assert signals["status"] == "NOT_LISTED" and signals["current"] == []
    (listing,) = signals["listings"]
    assert listing["downloads"] == 1 and listing["listedNow"] is False
    assert listing["firstSeen"] == listing["lastSeen"]
    assert "not shown to be available" in signals["notice"]


def test_listings_reopen_after_a_gap(app):
    # SIM-PKG-200 is given VNR SIM-VNR-900, which the first file lists, the
    # second does not, and the third (the first file again) lists again.
    current = (RELEASES / "current-release.xml").read_bytes()
    relabelled = current.replace(
        b"<VNR-numero>SIM-VNR-200</VNR-numero>", b"<VNR-numero>SIM-VNR-900</VNR-numero>"
    )
    assert relabelled != current
    with TestClient(app) as client:
        _upload(client, "relabelled.xml", 4, relabelled)
        _download(app, ["shortages.txt", "shortages-later.txt", "shortages.txt"])
        signals = _signals(client, "packages/SIM-PKG-200")
    first, second = signals["listings"]
    assert (first["downloads"], first["listedNow"]) == (1, False)
    assert first["lastSeen"].startswith("2099-01-01T05:00")
    assert (second["downloads"], second["listedNow"]) == (1, True)
    assert second["firstSeen"].startswith("2099-01-03T05:00")
    assert signals["status"] == "LISTED"


def test_without_vnr_or_without_a_file(app):
    with TestClient(app) as client:
        _upload(client, "links-release.xml", 5)
        no_vnr = _signals(client, "packages/SIM-PKG-L41")
        no_file = _signals(client, "packages/SIM-PKG-L11")
    assert no_vnr["status"] == "NO_VNR" and no_vnr["listings"] == []
    assert no_file["status"] == "NO_FILE" and no_file["shortageFile"] is None
    assert no_file["related"]["available"] is False


def test_other_strengths_listed_now_and_product_view(app):
    with TestClient(app) as client:
        _upload(client, "links-release.xml", 5)
        _download(app, ["shortages.txt"])
        package = _signals(client, "packages/SIM-PKG-L11")
        product = _signals(client, "products/SYN-PROD-L1")
    related = package["related"]
    assert related["sameSubstanceProducts"] == 1 and related["listedNow"] == 1
    assert related["items"][0]["productReference"] == "SYN-PROD-L2"
    assert related["items"][0]["listedVnrs"] == ["SIM-VNR-200"]
    assert product["anchorPackages"] == ["SIM-PKG-L11", "SIM-PKG-L12"]
    assert product["vnrs"] == ["SIM-VNR-200", "SIM-VNR-L12"]
    assert product["status"] == "LISTED"
    assert [r["pakkaustunnus"] for r in product["register"]] == ["SIM-PKG-L11", "SIM-PKG-L12"]
    onmarket = product["register"][0]["onMarket"]
    assert onmarket["value"] == "1"


def test_register_changes_from_package_history(app):
    current = (RELEASES / "current-release.xml").read_bytes()
    withdrawn = current.replace(
        b"<Ajopvm>2099-01-02</Ajopvm>", b"<Ajopvm>2099-01-09</Ajopvm>"
    ).replace(
        b"<Kaupan>1</Kaupan>\n      <Kauppaantulopaiva>2098-12-01</Kauppaantulopaiva>",
        b"<Kaupan>0</Kaupan>\n      <Kauppaantulopaiva>2098-12-01</Kauppaantulopaiva>",
    )
    assert withdrawn != current
    with TestClient(app) as client:
        _upload(client, "current-release.xml", 4)
        _upload(client, "withdrawn.xml", 9, withdrawn)
        signals = _signals(client, "packages/SIM-PKG-100")
    (change,) = signals["registerChanges"]
    assert change["field"] == "Pakkaus/Kaupanolo/Kaupan"
    assert (change["before"][0]["value"], change["after"][0]["value"]) == ("1", "0")
    assert change["currentReleaseDate"] == "2099-01-09"


def test_unknown_records(app):
    with TestClient(app) as client:
        _upload(client, "links-release.xml", 5)
        assert client.get(f"{API}/packages/SIM-PKG-NONE/supply-signals").status_code == 404
        assert client.get(f"{API}/products/SYN-PROD-NONE/supply-signals").status_code == 404
