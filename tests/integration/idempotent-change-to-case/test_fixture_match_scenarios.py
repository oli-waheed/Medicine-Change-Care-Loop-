"""US3 independent test, driven only by the fixture files.

prior-release.xml -> current-release.xml with medication-records.json must give:
unique match (SIM-PKG-100) -> one case; ambiguous (SIM-PKG-300) -> none;
no match (SIM-PKG-500) -> none; and replaying the release adds nothing.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.domain.evidence import EvidenceClassification
from src.services.detect_relevant_changes import SourceOrderEvidence, detect_relevant_changes
from src.services.match_detected_changes import MatchStatus, match_detected_changes
from src.services.normalize_basic_register_release import normalize_basic_register_release
from src.services.simulated_medication_records import load_simulated_medication_records

FIXTURES = Path(__file__).parents[2] / "fixtures"
RELEASES = FIXTURES / "fimea-basic-register"
RECORDS_FILE = FIXTURES / "simulated-medication-records" / "medication-records.json"


def _scenarios():
    return json.loads(RECORDS_FILE.read_text(encoding="utf-8"))["matching_scenarios"]


def _upload(client, filename, day):
    response = client.post(
        "/api/source-releases/ingest",
        files={"file": (filename, (RELEASES / filename).read_bytes(), "application/xml")},
        data={
            "sourceName": "Fimea Basic Register",
            "sourceReleaseReference": json.dumps(
                {"value": f"SIM-{filename}", "evidenceClass": "VERIFIED"}
            ),
            "retrievedAt": f"2099-01-0{day}T06:00:00+00:00",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["processingStatus"] == "VALIDATED"


def test_fixture_match_outcomes_are_matched_ambiguous_and_no_match():
    records = load_simulated_medication_records(RECORDS_FILE)
    prior_release, prior = normalize_basic_register_release(
        (RELEASES / "prior-release.xml").read_bytes(), file_name="prior", checksum="p"
    )
    current_release, current = normalize_basic_register_release(
        (RELEASES / "current-release.xml").read_bytes(), file_name="current", checksum="c"
    )
    order = SourceOrderEvidence(
        prior_release, current_release, 1, 2, EvidenceClassification.VERIFIED, "fixture order"
    )
    change_sets = detect_relevant_changes(prior, current, order=order).change_sets
    outcomes = {
        result.change_set.medicine_key: result
        for result in match_detected_changes(change_sets, records)
    }
    scenarios = _scenarios()

    expected = {
        "unique_exact_match": MatchStatus.MATCHED,
        "ambiguous_exact_match": MatchStatus.AMBIGUOUS,
        "no_match": MatchStatus.NO_MATCH,
    }
    for name, status in expected.items():
        scenario = scenarios[name]
        outcome = outcomes[scenario["Pakkaustunnus"]]
        assert outcome.result is status, name
        assert outcome.change_set.kind.value == scenario["change"], name
        assert [r.record_id for r in outcome.simulated_record_references] == scenario[
            "expected_record_ids"
        ], name
    # A record with only a matching VNR-numero is never matched.
    assert all(
        r.record_id != scenarios["primary_key_absent"]["record_id"]
        for outcome in outcomes.values()
        for r in outcome.simulated_record_references
    )


def test_fixture_release_replay_creates_exactly_one_case(isolated_app):
    app = isolated_app
    app.state.medication_records = load_simulated_medication_records(RECORDS_FILE)

    with TestClient(app) as client:
        _upload(client, "prior-release.xml", 3)
        _upload(client, "current-release.xml", 4)
        first = client.get("/api/open-review-cases").json()

        _upload(client, "current-release.xml", 4)  # exact replay
        _upload(client, "current-release.xml", 5)  # same file fetched again later
        replay = client.get("/api/open-review-cases").json()

    (case,) = first
    assert case["matchedRecord"]["recordId"] == "SIM-MED-001"
    assert case["medicineIdentifier"] == "SIM-PKG-100"
    assert case["changeSet"]["kind"] == "FIELDS_CHANGED"
    assert replay == first
