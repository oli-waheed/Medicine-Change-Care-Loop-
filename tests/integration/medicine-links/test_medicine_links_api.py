"""Feature 015: records linked to a package or product.

The synthetic links release goes through the real ingestion, the synthetic
shortage file through the real update; links are the real code.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.services.medicine_shortages import update_shortages

ROOT = Path(__file__).parents[3]
RELEASES = ROOT / "tests" / "fixtures" / "fimea-basic-register"
SHORTAGES = ROOT / "tests" / "fixtures" / "fimea-shortages"
API = "/api/medicine-catalogue"


def _upload(client, name: str) -> None:
    response = client.post(
        "/api/source-releases/ingest",
        files={"file": ("Perusrekisteri.xml", (RELEASES / name).read_bytes(), "application/xml")},
        data={
            "sourceName": "Fimea Basic Register",
            "sourceReleaseReference": json.dumps({"value": name, "evidenceClass": "VERIFIED"}),
            "retrievedAt": "2099-02-01T06:00:00+00:00",
        },
    )
    assert response.status_code == 200, response.text


def _store_shortages(app) -> None:
    def download(url, max_bytes, target):
        data = (SHORTAGES / "shortages.txt").read_bytes()
        target.write(data)
        return len(data)

    update_shortages(
        store=app.state.store,
        config=app.state.source_release_config,
        download=download,
        now=lambda: datetime(2099, 2, 1, 7, 0, tzinfo=UTC),
    )


@pytest.fixture
def client(isolated_app):
    isolated_app.state.shortage_reader = None
    isolated_app.state.link_index_cache = None
    with TestClient(isolated_app) as client:
        _upload(client, "links-release.xml")
        yield client


def _groups(response) -> dict[str, dict]:
    assert response.status_code == 200, response.text
    return {group["id"]: group for group in response.json()["groups"]}


def _products(group) -> list[str]:
    return [item["productReference"] for item in group["items"]]


def _packages(group) -> list[str]:
    return [item["pakkaustunnus"] for item in group["items"]]


def test_package_links_with_their_certainty(client, isolated_app):
    _store_shortages(isolated_app)
    groups = _groups(client.get(f"{API}/packages/SIM-PKG-L11/links"))

    assert groups["SAME_PRODUCT"]["certainty"] == "VERIFIED"
    assert _packages(groups["SAME_PRODUCT"]) == ["SIM-PKG-L12"]
    assert _packages(groups["SAME_VNR"]) == ["SIM-PKG-L21"]
    assert groups["SAME_VNR"]["certainty"] == "VERIFIED"
    # Other strengths of the same substance set, and products sharing one substance.
    assert _products(groups["SAME_SUBSTANCES"]) == ["SYN-PROD-L2"]
    assert _products(groups["SHARES_SUBSTANCE"]) == ["SYN-PROD-L3"]
    assert _products(groups["SAME_HOLDER"]) == ["SYN-PROD-L2"]
    assert groups["SIMILAR_HOLDER"]["certainty"] == "POSSIBLE"
    assert _products(groups["SIMILAR_HOLDER"]) == ["SYN-PROD-L3"]
    assert groups["SAME_NAME"]["certainty"] == "POSSIBLE"
    assert _products(groups["SAME_NAME"]) == ["SYN-PROD-L2"]
    shortages = groups["SHORTAGES"]
    assert shortages["certainty"] == "VERIFIED"
    assert [(row["vnr"], row["valid"]) for row in shortages["items"]] == [("SIM-VNR-200", "K")]
    assert shortages["note"] is None


def test_missing_identifiers_are_named_not_guessed(client, isolated_app):
    _store_shortages(isolated_app)
    groups = _groups(client.get(f"{API}/packages/SIM-PKG-L41/links"))
    assert groups["SAME_VNR"]["certainty"] == "MISSING"
    assert groups["SAME_HOLDER"]["certainty"] == "MISSING"
    assert groups["SHORTAGES"]["certainty"] == "MISSING"
    assert "No VNR" in groups["SHORTAGES"]["basis"]
    # A substance without a code links only by name, as a possible link.
    assert "SAME_SUBSTANCES" not in groups
    assert groups["SUBSTANCE_BY_NAME"]["certainty"] == "POSSIBLE"
    assert _products(groups["SUBSTANCE_BY_NAME"]) == ["SYN-PROD-L5"]


def test_absence_from_the_shortage_file_is_not_availability(client, isolated_app):
    groups = _groups(client.get(f"{API}/packages/SIM-PKG-L12/links"))
    assert groups["SHORTAGES"]["certainty"] == "MISSING"
    assert "No shortage file" in groups["SHORTAGES"]["basis"]

    _store_shortages(isolated_app)
    groups = _groups(client.get(f"{API}/packages/SIM-PKG-L12/links"))
    shortages = groups["SHORTAGES"]
    assert shortages["items"] == [] and shortages["total"] == 0
    assert shortages["note"] == (
        "Not listed in the shortage file. This does not show that it is available."
    )


def test_product_links_cover_all_its_packages(client):
    response = client.get(f"{API}/products/SYN-PROD-L1/links")
    body = response.json()
    assert body["anchorPackages"] == ["SIM-PKG-L11", "SIM-PKG-L12"]
    assert "used in place of another" in body["notice"]
    groups = _groups(response)
    assert _packages(groups["SAME_PRODUCT"]) == []
    assert _packages(groups["SAME_VNR"]) == ["SIM-PKG-L21"]


def test_unknown_records_and_read_only(client):
    assert client.get(f"{API}/packages/SIM-PKG-NONE/links").status_code == 404
    assert client.get(f"{API}/products/SYN-PROD-NONE/links").status_code == 404
    first = client.get(f"{API}/packages/SIM-PKG-L11/links").json()
    assert client.get(f"{API}/packages/SIM-PKG-L11/links").json() == first


def test_holder_is_read_but_not_compared():
    """A holder change alone creates no detected change (until the team decides)."""
    from src.services.detect_relevant_changes import project_snapshot_fields
    from src.services.normalize_basic_register_release import normalize_basic_register_release

    content = (RELEASES / "links-release.xml").read_bytes()
    _, snapshots = normalize_basic_register_release(content, file_name="x", checksum="c")
    snapshot = next(s for s in snapshots if s.pakkaustunnus == "SIM-PKG-L11")
    assert snapshot.authorizations[0].haltija.value == "Fictional Pharma Oy"
    assert not any("Haltija" in path for path in project_snapshot_fields(snapshot))
