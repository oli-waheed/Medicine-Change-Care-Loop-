import hashlib
from datetime import UTC, datetime
from pathlib import Path

from src.workflows.ingestion_to_review import run_release_ingestion_to_review

FIXTURES = Path(__file__).parents[2] / "fixtures" / "fimea-basic-register"


def _release_payload(filename, release_reference, source_order, retrieved_at):
    path = FIXTURES / filename
    return {
        "sourceName": "Fimea Basic Register",
        "sourceReleaseReference": {
            "value": release_reference,
            "evidenceClass": "VERIFIED",
        },
        "sourceOrder": {
            "value": str(source_order),
            "evidenceClass": "VERIFIED",
        },
        "retrievedAt": retrieved_at.isoformat(),
        "files": [
            {
                "name": filename,
                "checksum": hashlib.sha256(path.read_bytes()).hexdigest(),
                "contentReference": str(path.resolve()),
            }
        ],
        "captureStatus": "COMPLETE",
    }


def test_complete_release_ingestion_creates_traceable_review_case(
    tmp_path, medication_record
):
    prior_payload = _release_payload(
        "prior-release.xml",
        "SIM-RELEASE-001",
        1,
        datetime(2099, 1, 3, tzinfo=UTC),
    )
    current_payload = _release_payload(
        "current-release.xml",
        "SIM-RELEASE-002",
        2,
        datetime(2099, 1, 4, tzinfo=UTC),
    )
    open_cases = []

    result = run_release_ingestion_to_review(
        prior_payload,
        current_payload,
        (medication_record,),
        storage_dir=tmp_path,
        open_cases=open_cases,
        created_at=datetime(2099, 1, 5, tzinfo=UTC),
    )

    assert result.prior_ingestion.processing_status.value == "VALIDATED"
    assert result.current_ingestion.processing_status.value == "VALIDATED"
    assert result.prior_ingestion.captured_release is not None
    assert result.current_ingestion.captured_release is not None
    assert result.prior_ingestion.snapshots
    assert result.current_ingestion.snapshots

    changes = result.workflow_result.comparison.changes
    assert any(
        change.medicine_key == "SIM-PKG-100"
        and change.field_name == "Laakevalmiste/Kauppanimi"
        for change in changes
    )

    cases = result.workflow_result.created_cases
    assert any(
        case.change.medicine_key == "SIM-PKG-100"
        and case.medication_record.record_id == "SIM-MED-100"
        and case.status.value == "NEW"
        for case in cases
    )
    assert open_cases == list(cases)

    assert result.prior_ingestion.captured_release.capture_directory.exists()
    assert result.current_ingestion.captured_release.capture_directory.exists()


def test_unknown_source_order_captures_releases_without_creating_cases(
    tmp_path, medication_record
):
    prior_payload = _release_payload(
        "prior-release.xml",
        "SIM-RELEASE-UNKNOWN-001",
        1,
        datetime(2099, 1, 3, tzinfo=UTC),
    )
    current_payload = _release_payload(
        "current-release.xml",
        "SIM-RELEASE-UNKNOWN-002",
        2,
        datetime(2099, 1, 4, tzinfo=UTC),
    )
    for payload in (prior_payload, current_payload):
        payload["sourceOrder"] = {
            "value": None,
            "evidenceClass": "UNKNOWN",
        }

    open_cases = []
    result = run_release_ingestion_to_review(
        prior_payload,
        current_payload,
        (medication_record,),
        storage_dir=tmp_path,
        open_cases=open_cases,
    )

    assert result.prior_ingestion.processing_status.value == "VALIDATED"
    assert result.current_ingestion.processing_status.value == "VALIDATED"
    assert result.workflow_result.comparison.classification.value == "UNKNOWN"
    assert result.workflow_result.comparison.changes == ()
    assert result.workflow_result.created_cases == ()
    assert open_cases == []


def test_decreasing_verified_source_order_is_conflicting(
    tmp_path, medication_record
):
    prior_payload = _release_payload(
        "prior-release.xml",
        "SIM-RELEASE-LATER",
        2,
        datetime(2099, 1, 3, tzinfo=UTC),
    )
    current_payload = _release_payload(
        "current-release.xml",
        "SIM-RELEASE-EARLIER",
        1,
        datetime(2099, 1, 4, tzinfo=UTC),
    )

    open_cases = []
    result = run_release_ingestion_to_review(
        prior_payload,
        current_payload,
        (medication_record,),
        storage_dir=tmp_path,
        open_cases=open_cases,
    )

    assert result.prior_ingestion.processing_status.value == "VALIDATED"
    assert result.current_ingestion.processing_status.value == "VALIDATED"
    assert result.workflow_result.comparison.classification.value == "CONFLICTING"
    assert result.workflow_result.comparison.changes == ()
    assert result.workflow_result.created_cases == ()
    assert open_cases == []


def test_replaying_complete_release_pair_does_not_duplicate_open_case(
    tmp_path, medication_record
):
    prior_payload = _release_payload(
        "prior-release.xml",
        "SIM-RELEASE-REPLAY-001",
        1,
        datetime(2099, 1, 3, tzinfo=UTC),
    )
    current_payload = _release_payload(
        "current-release.xml",
        "SIM-RELEASE-REPLAY-002",
        2,
        datetime(2099, 1, 4, tzinfo=UTC),
    )
    open_cases = []

    first = run_release_ingestion_to_review(
        prior_payload,
        current_payload,
        (medication_record,),
        storage_dir=tmp_path,
        open_cases=open_cases,
    )
    replay = run_release_ingestion_to_review(
        prior_payload,
        current_payload,
        (medication_record,),
        storage_dir=tmp_path,
        open_cases=open_cases,
    )

    assert len(first.workflow_result.created_cases) >= 1
    assert replay.workflow_result.created_cases == ()
    assert len(open_cases) == len(first.workflow_result.created_cases)
