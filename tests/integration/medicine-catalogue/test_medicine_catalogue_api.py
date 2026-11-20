"""Feature 004 T028–T035: the read-only catalogue API over a stored release.

The synthetic current release is varied in memory so one baseline covers the
interesting cases: a missing VNR (SIM-PKG-400), two packages sharing a VNR
(SIM-PKG-200 and SIM-PKG-500), a present-but-empty administration route
(SYN-PROD-200), no route at all (SYN-PROD-400), and a product with two active
substances in source order (SYN-PROD-100).
"""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.services.detect_relevant_changes import project_snapshot_fields
from src.services.medicine_catalogue import MedicineCatalogueService
from src.services.simulated_medication_records import load_simulated_medication_records

ROOT = Path(__file__).parents[3]
FIXTURES = ROOT / "tests" / "fixtures" / "fimea-basic-register"
RECORDS = ROOT / "backend" / "seed" / "simulated-medication-records.json"
API = "/api/medicine-catalogue"
CLINICAL_WORDS = re.compile(
    r"\b(urgen\w*|priorit\w*|severity|risk\w*|recommend\w*|diagnos\w*|substitut\w*|"
    r"treatment|dos(e|es|ing|age)|contraindicat\w*|interaction\w*|should|stop taking|switch to)\b",
    re.IGNORECASE,
)


def _varied_current_release() -> bytes:
    xml = (FIXTURES / "current-release.xml").read_text(encoding="utf-8")
    # SIM-PKG-400 has no VNR element at all.
    xml = xml.replace("    <VNR-numero>SIM-VNR-400</VNR-numero>\n", "")
    # SIM-PKG-500 shares its VNR with SIM-PKG-200.
    xml = xml.replace(
        "<VNR-numero>SIM-VNR-500</VNR-numero>", "<VNR-numero>SIM-VNR-200</VNR-numero>"
    )
    # SYN-SUB-100 lists a second substance after the first one.
    second = """    <VaikuttavaAine>
      <Aine listname="SIM-SUBSTANCE" id="SIM-SB01" value="fictional substance blue"/>
      <CASnumero>SIM-CAS-200</CASnumero>
      <Maara>0.5</Maara>
      <Maarayksikko listname="SIM-UNIT" id="SIM-MASS" value="synthetic units"/>
      <JakamatonVahvuus>synthetic amount A2</JakamatonVahvuus>
    </VaikuttavaAine>
  </Laakeaine>
  <Laakeaine id="SYN-SUB-200">"""
    xml = xml.replace('  </Laakeaine>\n  <Laakeaine id="SYN-SUB-200">', second, 1)
    return xml.encode("utf-8")


def _ingest(client: TestClient, name: str, content: bytes, day: int):
    response = client.post(
        "/api/source-releases/ingest",
        files={"file": (name, content, "application/xml")},
        data={
            "sourceName": "Fimea Basic Register",
            "sourceReleaseReference": json.dumps(
                {"value": f"SIM-{name}", "evidenceClass": "VERIFIED"}
            ),
            "retrievedAt": datetime(2099, 1, day, tzinfo=UTC).isoformat(),
        },
    )
    assert response.json()["processingStatus"] == "VALIDATED", response.json()
    return response.json()


@pytest.fixture
def catalogue(isolated_app):
    isolated_app.state.medication_records = load_simulated_medication_records(RECORDS)
    with TestClient(isolated_app) as client:
        _ingest(client, "prior-release.xml", (FIXTURES / "prior-release.xml").read_bytes(), 3)
        current = _ingest(client, "current-release.xml", _varied_current_release(), 4)
        yield client, current


def _ids(response):
    return [item["pakkaustunnus"] for item in response.json()["items"]]


def _all_strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_strings(item)
    elif isinstance(value, str):
        yield value


# T028 — search and filters
def test_catalogue_lists_the_active_release_in_source_order(catalogue):
    client, current = catalogue
    response = client.get(API)
    assert response.status_code == 200
    body = response.json()
    assert body["release"]["releaseId"] == current["capturedReleaseReference"]
    assert body["total"] == 4
    assert _ids(response) == ["SIM-PKG-100", "SIM-PKG-200", "SIM-PKG-400", "SIM-PKG-500"]


def test_search_by_name_identifier_and_vnr(catalogue):
    client, _ = catalogue
    assert _ids(client.get(API, params={"q": "amber"})) == ["SIM-PKG-100"]
    assert _ids(client.get(API, params={"q": "sim-pkg-4"})) == ["SIM-PKG-400"]
    assert _ids(client.get(API, params={"q": "SIM-VNR-200"})) == ["SIM-PKG-200", "SIM-PKG-500"]


def test_filters_match_codes_and_display_values(catalogue):
    client, _ = catalogue
    assert _ids(client.get(API, params={"atc": "sim-a"})) == ["SIM-PKG-100"]
    assert _ids(client.get(API, params={"form": "SIM-F02"})) == ["SIM-PKG-200", "SIM-PKG-500"]
    assert _ids(client.get(API, params={"route": "fictional route"})) == ["SIM-PKG-100"]
    assert _ids(client.get(API, params={"activeSubstance": "SIM-SB01"})) == [
        "SIM-PKG-100",
        "SIM-PKG-200",
        "SIM-PKG-500",
    ]
    assert _ids(client.get(API, params={"available": "1", "form": "SIM-F04"})) == ["SIM-PKG-400"]
    assert _ids(client.get(API, params={"vnr": "sim-vnr-100"})) == ["SIM-PKG-100"]


def test_missing_filter_keeps_absent_separate_from_empty(catalogue):
    client, _ = catalogue
    # SYN-PROD-400 has no Antoreitti; SYN-PROD-200 has an empty one, which is present.
    assert _ids(client.get(API, params={"missing": "route"})) == ["SIM-PKG-400"]
    assert _ids(client.get(API, params={"missing": "vnr"})) == ["SIM-PKG-400"]
    assert _ids(client.get(API, params={"missing": "atc"})) == ["SIM-PKG-400"]


def test_paging_and_invalid_parameters(catalogue):
    client, _ = catalogue
    page = client.get(API, params={"page": 2, "pageSize": 3}).json()
    assert (page["total"], page["page"], page["pageSize"]) == (4, 2, 3)
    assert [item["pakkaustunnus"] for item in page["items"]] == ["SIM-PKG-500"]
    assert client.get(API, params={"missing": "colour"}).status_code == 422
    assert client.get(API, params={"available": "yes"}).status_code == 422
    assert client.get(API, params={"pageSize": 500}).status_code == 422
    assert client.get(API, params={"page": 0}).status_code == 422


# T029 — product and package details
def test_product_details_and_its_packages(catalogue):
    client, _ = catalogue
    body = client.get(f"{API}/products/SYN-PROD-200").json()
    product = body["product"]
    assert product["name"]["value"] == "Fictional Product Blue"
    assert product["atcCode"]["attributes"]["id"] == "SIM-B01"
    assert product["administrationRoutes"] == [{"state": "empty", "value": "", "attributes": {}}]
    assert product["authorizations"][0]["branch"] == "Rekisterointi"
    assert [p["pakkaustunnus"] for p in body["packages"]] == ["SIM-PKG-200", "SIM-PKG-500"]
    assert client.get(f"{API}/products/SYN-PROD-300").status_code == 404


def test_package_details(catalogue):
    client, _ = catalogue
    body = client.get(f"{API}/packages/SIM-PKG-100").json()
    package = body["package"]
    assert package["pakkaustunnus"] == "SIM-PKG-100"
    assert package["packageSize"]["value"] == "10"
    assert package["availability"]["available"]["value"] == "1"
    assert package["availability"]["availableUntil"]["state"] == "empty"
    assert body["product"]["productReference"] == "SYN-PROD-100"
    not_found = client.get(f"{API}/packages/SIM-PKG-300")
    assert not_found.status_code == 404
    assert not_found.json()["detail"]["code"] == "PACKAGE_NOT_FOUND"


# T030 — active substances
def test_substances_keep_source_order_and_repeated_occurrences(catalogue):
    client, _ = catalogue
    product = client.get(f"{API}/products/SYN-PROD-100").json()["product"]
    names = [s["name"]["attributes"]["id"] for s in product["activeSubstances"]]
    assert names == ["SIM-SA01", "SIM-SB01"]

    body = client.get(f"{API}/active-substances").json()
    blue = next(item for item in body["items"] if item["identity"] == "Aine=SIM-SB01")
    assert [(o["pakkaustunnus"], o["position"]) for o in blue["occurrences"]] == [
        ("SIM-PKG-100", 2),
        ("SIM-PKG-200", 1),
        ("SIM-PKG-500", 1),
    ]
    assert blue["occurrences"][0]["undividedStrength"]["value"] == "synthetic amount A2"
    assert [
        i["identity"]
        for i in client.get(f"{API}/active-substances", params={"q": "fable"}).json()["items"]
    ] == ["Aine=SIM-SD01"]


# T031 — VNR visibility, search and missing values
def test_vnr_is_explicit_and_never_invented(catalogue):
    client, _ = catalogue
    items = {i["pakkaustunnus"]: i for i in client.get(API).json()["items"]}
    assert items["SIM-PKG-100"]["vnr"] == {
        "state": "value",
        "value": "SIM-VNR-100",
        "attributes": {},
    }
    assert items["SIM-PKG-400"]["vnr"] == {"state": "missing", "value": None, "attributes": {}}
    package = client.get(f"{API}/packages/SIM-PKG-400").json()
    assert package["package"]["vnr"]["state"] == "missing"
    assert package["sameVnrPackages"] == []


# T032 — package identity and VNR are separate
def test_shared_vnr_groups_packages_without_merging_them(catalogue):
    client, _ = catalogue
    body = client.get(f"{API}/packages/SIM-PKG-200").json()
    assert body["package"]["pakkaustunnus"] == "SIM-PKG-200"
    assert body["sameVnrPackages"] == ["SIM-PKG-500"]
    other = client.get(f"{API}/packages/SIM-PKG-500").json()
    assert other["sameVnrPackages"] == ["SIM-PKG-200"]
    # Both records stay separate, each with its own package details.
    assert (
        other["package"]["packageSizeText"]["value"] != body["package"]["packageSizeText"]["value"]
    )
    assert len({i["pakkaustunnus"] for i in client.get(API).json()["items"]}) == 4


# T033 — provenance and source release
def test_package_provenance_is_complete(catalogue):
    client, _ = catalogue
    provenance = client.get(f"{API}/packages/SIM-PKG-100").json()["package"]["provenance"]
    assert provenance["sourceName"] == "Fimea Basic Register"
    assert provenance["releaseDate"]["value"] == "2099-01-02"
    assert provenance["releaseReference"]["value"] == "SIM-2099-002"
    assert provenance["fileName"] == "current-release.xml"
    assert len(provenance["checksum"]) == 64
    assert provenance["recordIdentifier"] == "SIM-PKG-100"
    assert provenance["recordLocator"] == "/Perusrekisteri/Pakkaus[1]"
    assert provenance["retrievedAt"] == "2099-01-04T00:00:00+00:00"


def test_source_summary(catalogue):
    client, current = catalogue
    body = client.get(f"{API}/source").json()
    assert body["release"]["releaseId"] == current["capturedReleaseReference"]
    assert body["release"]["chronologyEvidence"] == "VERIFIED"
    assert body["release"]["retrievedAt"] == "2099-01-04T00:00:00+00:00"
    assert (body["packageCount"], body["productCount"], body["activeSubstanceCount"]) == (4, 3, 3)


# T034 — product comparison
def test_comparison_uses_existing_field_paths_and_makes_no_equivalence_claim(
    catalogue, isolated_app
):
    client, _ = catalogue
    body = client.get(
        f"{API}/compare", params={"productA": "SYN-PROD-100", "productB": "SYN-PROD-200"}
    ).json()
    fields = {f["field"]: f for f in body["fields"]}
    assert fields["Laakevalmiste/Kauppanimi"]["result"] == "DIFFERENT"
    assert fields["Laakevalmiste/Laakemuoto"]["result"] == "DIFFERENT"
    # Present-but-empty route on B is not the same as a value on A.
    assert fields["Laakevalmiste/Antoreitti"]["b"] == [
        {"state": "empty", "value": "", "attributes": {}}
    ]
    assert "therapeutic equivalence" in body["notice"]

    baseline = MedicineCatalogueService(isolated_app.state.store).get_baseline()
    snapshot = next(s for s in baseline.snapshots if s.pakkaustunnus == "SIM-PKG-100")
    expected = {
        p
        for p in project_snapshot_fields(snapshot)
        if p.startswith(("Laakevalmiste/", "Laakeaine/"))
    }
    assert expected <= set(fields)


def test_comparison_parameters(catalogue):
    client, _ = catalogue
    assert client.get(f"{API}/compare", params={"productA": "SYN-PROD-100"}).status_code == 422
    same = {"productA": "SYN-PROD-100", "productB": "SYN-PROD-100"}
    assert client.get(f"{API}/compare", params=same).status_code == 422
    unknown = {"productA": "SYN-PROD-100", "productB": "SYN-PROD-300"}
    assert client.get(f"{API}/compare", params=unknown).status_code == 404


# T035 — source integrity and error handling
def test_catalogue_reads_change_nothing(catalogue, isolated_app):
    client, _ = catalogue
    store = isolated_app.state.store
    before = (
        [c.release_id for c in store.captures()],
        store.open_case_payloads(),
        store.processing_outcome_payloads(),
        store.comparison_baseline().release_id,
    )
    for path in (
        API,
        f"{API}/products/SYN-PROD-100",
        f"{API}/packages/SIM-PKG-100",
        f"{API}/active-substances",
        f"{API}/source",
    ):
        assert client.get(path).status_code == 200
    client.get(f"{API}/compare", params={"productA": "SYN-PROD-100", "productB": "SYN-PROD-200"})
    after = (
        [c.release_id for c in store.captures()],
        store.open_case_payloads(),
        store.processing_outcome_payloads(),
        store.comparison_baseline().release_id,
    )
    assert after == before


def test_responses_contain_no_clinical_wording(catalogue):
    client, _ = catalogue
    for path, params in (
        (API, {}),
        (f"{API}/products/SYN-PROD-100", {}),
        (f"{API}/packages/SIM-PKG-200", {}),
        (f"{API}/active-substances", {}),
        (f"{API}/compare", {"productA": "SYN-PROD-100", "productB": "SYN-PROD-400"}),
        (f"{API}/source", {}),
    ):
        for text in _all_strings(client.get(path, params=params).json()):
            assert not CLINICAL_WORDS.search(text), f"clinical wording {text!r} in {path}"


def test_no_baseline_is_an_explicit_unavailable_state(isolated_app):
    with TestClient(isolated_app) as client:
        for path in (
            API,
            f"{API}/products/X",
            f"{API}/packages/X",
            f"{API}/active-substances",
            f"{API}/source",
        ):
            response = client.get(path)
            assert response.status_code == 503, path
            assert response.json()["detail"]["code"] == "CATALOGUE_UNAVAILABLE"
        compare = client.get(f"{API}/compare", params={"productA": "A", "productB": "B"})
        assert compare.status_code == 503


def test_tampered_capture_is_reported_not_shown(isolated_app):
    with TestClient(isolated_app) as client:
        _ingest(client, "prior-release.xml", (FIXTURES / "prior-release.xml").read_bytes(), 3)
        directory = Path(isolated_app.state.store.comparison_baseline().capture_directory)
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        (directory / manifest["files"][0]["contentReference"]).write_bytes(b"<changed/>")
        response = client.get(API)
        assert response.status_code == 503
        assert response.json()["detail"]["code"] == "CATALOGUE_SOURCE_UNREADABLE"
