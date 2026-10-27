from datetime import UTC, datetime
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "fimea-basic-register"


def _request(filename: str, *, capture_status: str = "COMPLETE", source_order=None):
    return {
        "sourceName": "Fimea Basic Register",
        "sourceReleaseReference": {
            "value": "SIM-2099-001",
            "evidenceClass": "VERIFIED",
        },
        "sourceOrder": source_order
        or {"value": "1", "evidenceClass": "VERIFIED"},
        "retrievedAt": datetime(2099, 1, 4, tzinfo=UTC).isoformat(),
        "files": [
            {
                "name": filename,
                "checksum": f"synthetic-checksum-{filename}",
                "contentReference": str((FIXTURE_DIR / filename).resolve()),
            }
        ],
        "captureStatus": capture_status,
    }


def _ingest(payload):
    from src.services.ingest_source_release import ingest_source_release

    return ingest_source_release(payload)


def test_complete_release_returns_traceable_normalized_snapshot():
    outcome = _ingest(_request("prior-release.xml"))

    assert outcome.processing_status == "VALIDATED"
    assert outcome.source_release.provenance.source_name == "Fimea Basic Register"
    assert outcome.source_release.provenance.raw_file_name == "prior-release.xml"
    assert outcome.source_release.provenance.raw_file_checksum
    assert outcome.snapshots


def test_partial_release_marked_failed_is_not_reported_as_a_snapshot():
    outcome = _ingest(_request("prior-release.xml", capture_status="FAILED"))

    assert outcome.processing_status == "FAILED"
    assert outcome.snapshots == ()
    assert outcome.failure_detail


def test_malformed_release_fails_without_partial_normalized_records():
    outcome = _ingest(_request("malformed-release.xml"))

    assert outcome.processing_status == "FAILED"
    assert outcome.snapshots == ()
    assert outcome.failure_detail


def test_release_with_unknown_order_keeps_order_unknown():
    outcome = _ingest(
        _request(
            "ordering-unknown-release.xml",
            source_order={"value": None, "evidenceClass": "UNKNOWN"},
        )
    )

    assert outcome.processing_status == "VALIDATED"
    assert outcome.source_order.value is None
    assert outcome.source_order.evidence_class == "UNKNOWN"
    assert outcome.verified_chronological_order is False


@pytest.mark.parametrize("status", ["PARTIAL", "UNKNOWN"])
def test_non_complete_capture_cannot_be_silently_accepted_as_complete(status):
    with pytest.raises(ValueError):
        _ingest(_request("prior-release.xml", capture_status=status))
