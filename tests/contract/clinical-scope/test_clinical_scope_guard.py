"""T035: the system communicates source-data changes only (FR-014, FR-016).

These guards fail if the API, the workflow or the stored case data starts to
diagnose, recommend treatment, select substitutions, set urgency, change a
case's status on its own, or close a case.
"""

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from src.domain.case_status_event import CaseStatus
from src.main import app as main_app
from src.services.simulated_medication_records import load_simulated_medication_records

ROOT = Path(__file__).parents[3]
RELEASES = ROOT / "tests" / "fixtures" / "fimea-basic-register"
RECORDS_FILE = (
    ROOT / "tests" / "fixtures" / "simulated-medication-records" / "medication-records.json"
)
WORKFLOW = ROOT / "workflow" / "n8n" / "fimea-basic-register-ingestion.json"

# Words that would turn a source-data difference into clinical advice or triage.
CLINICAL_WORDS = re.compile(
    r"\b(urgen\w*|priorit\w*|severity|risk\w*|recommend\w*|diagnos\w*|substitut\w*|"
    r"treatment|dos(e|es|ing|age)|contraindicat\w*|interaction\w*|should|stop taking|switch to)\b",
    re.IGNORECASE,
)


def _upload(client, content: bytes, name: str, day: int):
    response = client.post(
        "/api/source-releases/ingest",
        files={"file": (name, content, "application/xml")},
        data={
            "sourceName": "Fimea Basic Register",
            "sourceReleaseReference": json.dumps({"value": name, "evidenceClass": "VERIFIED"}),
            "retrievedAt": f"2099-01-0{day}T06:00:00+00:00",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _keys(item)


def _strings(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, str):
        yield value


def test_api_offers_no_operation_that_changes_or_closes_cases():
    operations = {
        (method.upper(), path)
        for path, methods in main_app.openapi()["paths"].items()
        for method in methods
    }

    assert operations == {
        ("GET", "/health"),
        ("GET", "/api/open-review-cases"),
        ("GET", "/api/change-processing-outcomes"),
        ("POST", "/api/source-releases/ingest"),
        # Feature 004: read-only medicine catalogue (contracts/catalogue-api.md).
        ("GET", "/api/medicine-catalogue"),
        ("GET", "/api/medicine-catalogue/products/{product_reference}"),
        ("GET", "/api/medicine-catalogue/packages/{pakkaustunnus}"),
        ("GET", "/api/medicine-catalogue/active-substances"),
        ("GET", "/api/medicine-catalogue/compare"),
        ("GET", "/api/medicine-catalogue/source"),
        # Feature 005: check Fimea for the latest release (contracts/latest-release-check-api.md).
        # It downloads and ingests exactly like POST /ingest; it never changes or closes cases.
        ("GET", "/api/source-releases/latest-check"),
        ("POST", "/api/source-releases/latest-check"),
        # Feature 006: Fimea shortage data and the daily update (contracts/shortages-api.md).
        # They store Fimea's shortage file and show it; they never change or close cases.
        ("GET", "/api/shortages"),
        ("GET", "/api/shortages/update"),
        ("POST", "/api/shortages/update"),
        ("GET", "/api/daily-updates"),
        # Feature 007: the one operation that changes a case, a pharmacist's review step
        # (contracts/review-api.md). The system never calls it.
        ("POST", "/api/review-cases/{case_id}/status-events"),
    }


def test_case_statuses_are_new_and_the_three_review_outcomes():
    # Adding a status is a deliberate, reviewed change to scope. Feature 007 added the
    # three statuses a pharmacist sets; the system itself only ever creates NEW.
    assert [status.value for status in CaseStatus] == [
        "NEW",
        "IN_PROGRESS",
        "REVIEWED_NO_ACTION",
        "REVIEWED_FOLLOW_UP",
    ]


def test_later_releases_never_change_or_close_an_existing_case(isolated_app):
    app = isolated_app
    app.state.medication_records = load_simulated_medication_records(RECORDS_FILE)
    third = (
        (RELEASES / "current-release.xml")
        .read_bytes()
        .replace(b"<Ajopvm>2099-01-02</Ajopvm>", b"<Ajopvm>2099-01-03</Ajopvm>")
        .replace(b"SIM-2099-002", b"SIM-2099-003")
        .replace(b"Fictional Product Amber Revised", b"Fictional Product Amber Revised Again")
    )

    with TestClient(app) as client:
        _upload(client, (RELEASES / "prior-release.xml").read_bytes(), "prior-release.xml", 3)
        _upload(client, (RELEASES / "current-release.xml").read_bytes(), "current-release.xml", 4)
        (first_case,) = client.get("/api/open-review-cases").json()

        _upload(client, third, "third-release.xml", 5)
        cases = {case["caseId"]: case for case in client.get("/api/open-review-cases").json()}

    # The newer change opens its own case; the earlier case is left exactly as it was.
    assert len(cases) == 2
    assert cases[first_case["caseId"]] == first_case
    for case in cases.values():
        assert case["status"] == "NEW"
        events = app.state.store.status_events(case["caseId"])
        assert [(e.from_status, e.to_status) for e in events] == [(None, "NEW")]


def test_stored_case_and_outcome_data_carry_no_clinical_judgement(isolated_app):
    app = isolated_app
    app.state.medication_records = load_simulated_medication_records(RECORDS_FILE)

    with TestClient(app) as client:
        _upload(client, (RELEASES / "prior-release.xml").read_bytes(), "prior-release.xml", 3)
        _upload(client, (RELEASES / "current-release.xml").read_bytes(), "current-release.xml", 4)
        payloads = (
            client.get("/api/open-review-cases").json()
            + client.get("/api/change-processing-outcomes").json()
        )

    assert payloads
    for key in _keys(payloads):
        assert not CLINICAL_WORDS.search(key), f"clinical field {key!r}"
    for text in _strings(payloads):
        assert not CLINICAL_WORDS.search(text), f"clinical wording {text!r}"


def test_substitution_group_is_never_compared(isolated_app):
    """Substituutioryhma must not be used to select or suggest a substitution."""
    from src.domain.evidence import EvidenceClassification
    from src.services.detect_relevant_changes import SourceOrderEvidence, detect_relevant_changes
    from src.services.normalize_basic_register_release import normalize_basic_register_release

    prior_bytes = (RELEASES / "prior-release.xml").read_bytes()
    current_bytes = prior_bytes.replace(
        b"<Ajopvm>2099-01-01</Ajopvm>", b"<Ajopvm>2099-01-02</Ajopvm>"
    ).replace(
        b"<Kauppanimi>Fictional Product Blue</Kauppanimi>",
        b"<Kauppanimi>Fictional Product Blue</Kauppanimi>"
        b"<Substituutioryhma>SIM-SUBSTITUTION-GROUP</Substituutioryhma>",
    )
    assert current_bytes.count(b"Substituutioryhma") == 2
    prior_release, prior = normalize_basic_register_release(
        prior_bytes, file_name="prior", checksum="p"
    )
    current_release, current = normalize_basic_register_release(
        current_bytes, file_name="current", checksum="c"
    )
    order = SourceOrderEvidence(
        prior_release, current_release, 1, 2, EvidenceClassification.VERIFIED, "test"
    )

    result = detect_relevant_changes(prior, current, order=order)

    assert result.changes == ()
    assert result.change_sets == ()


def test_n8n_workflow_only_downloads_and_uploads_releases():
    workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    node_types = {node["type"] for node in workflow["nodes"]}
    requests = [
        (node["parameters"].get("method", "GET"), node["parameters"]["url"])
        for node in workflow["nodes"]
        if node["type"] == "n8n-nodes-base.httpRequest"
    ]

    assert node_types <= {
        "n8n-nodes-base.scheduleTrigger",
        "n8n-nodes-base.httpRequest",
        "n8n-nodes-base.if",
        "n8n-nodes-base.set",
    }
    assert sorted(requests) == [
        ("GET", "https://data.pilvi.fimea.fi/avoin-data/Perusrekisteri.xml"),
        ("POST", "http://host.docker.internal:8000/api/source-releases/ingest"),
    ]
