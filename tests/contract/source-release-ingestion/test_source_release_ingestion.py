import hashlib
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
        "sourceOrder": source_order or {"value": "1", "evidenceClass": "VERIFIED"},
        "retrievedAt": datetime(2099, 1, 4, tzinfo=UTC).isoformat(),
        "files": [
            {
                "name": filename,
                "checksum": hashlib.sha256((FIXTURE_DIR / filename).read_bytes()).hexdigest(),
                "contentReference": str((FIXTURE_DIR / filename).resolve()),
            }
        ],
        "captureStatus": capture_status,
    }


def _ingest(payload, tmp_path):
    from src.services.ingest_source_release import ingest_source_release

    return ingest_source_release(payload, storage_dir=tmp_path)


def test_complete_release_returns_traceable_normalized_snapshot(tmp_path):
    outcome = _ingest(_request("prior-release.xml"), tmp_path)

    assert outcome.processing_status == "VALIDATED"
    assert outcome.source_release.provenance.source_name == "Fimea Basic Register"
    assert outcome.source_release.provenance.raw_file_name == "prior-release.xml"
    assert outcome.source_release.provenance.raw_file_checksum
    assert outcome.snapshots
    captured_file = outcome.captured_release.files[0]
    assert (
        outcome.captured_release.capture_directory / captured_file.content_reference
    ).read_bytes() == (FIXTURE_DIR / "prior-release.xml").read_bytes()


def test_failed_capture_is_not_reported_as_a_snapshot(tmp_path):
    outcome = _ingest(_request("prior-release.xml", capture_status="FAILED"), tmp_path)

    assert outcome.processing_status == "FAILED"
    assert outcome.snapshots == ()
    assert outcome.failure_detail


def test_malformed_release_fails_without_partial_normalized_records(tmp_path):
    outcome = _ingest(_request("malformed-release.xml"), tmp_path)

    assert outcome.processing_status == "FAILED"
    assert outcome.snapshots == ()
    assert outcome.failure_detail
    assert outcome.captured_release is not None


def test_release_with_unknown_order_is_validated_but_not_chronologically_comparable(
    tmp_path,
):
    outcome = _ingest(
        _request(
            "ordering-unknown-release.xml",
            source_order={"value": None, "evidenceClass": "UNKNOWN"},
        ),
        tmp_path,
    )

    assert outcome.processing_status == "VALIDATED"
    assert outcome.snapshots
    assert outcome.source_order.value is None
    assert outcome.source_order.evidence_class == "UNKNOWN"
    assert outcome.verified_chronological_order is False
    assert outcome.chronology_status.value == "UNAVAILABLE"
    assert outcome.failure_detail is None
    assert outcome.captured_release is not None


def test_non_sha256_checksum_fails_without_capture(tmp_path):
    request = _request("prior-release.xml")
    request["files"][0]["checksum"] = "synthetic-checksum"

    outcome = _ingest(request, tmp_path)

    assert outcome.processing_status == "FAILED"
    assert outcome.snapshots == ()
    assert outcome.captured_release is None
    assert "SHA-256" in outcome.failure_detail


def test_checksum_mismatch_fails_without_capture(tmp_path):
    request = _request("prior-release.xml")
    request["files"][0]["checksum"] = "0" * 64

    outcome = _ingest(request, tmp_path)

    assert outcome.processing_status == "FAILED"
    assert outcome.snapshots == ()
    assert outcome.captured_release is None
    assert "Checksum mismatch" in outcome.failure_detail


def test_inaccessible_file_returns_failed_outcome(tmp_path):
    request = _request("prior-release.xml")
    request["files"][0]["contentReference"] = str(tmp_path / "missing.xml")

    outcome = _ingest(request, tmp_path)

    assert outcome.processing_status == "FAILED"
    assert outcome.snapshots == ()
    assert outcome.captured_release is None
    assert "Cannot access source file" in outcome.failure_detail


def test_incomplete_xml_fails_without_returning_valid_prefix_snapshots(tmp_path):
    content = (
        (FIXTURE_DIR / "prior-release.xml")
        .read_bytes()
        .replace(b"<Kattavuus>1</Kattavuus>", b"<Kattavuus>0</Kattavuus>")
    )
    source_path = tmp_path / "partial.xml"
    source_path.write_bytes(content)
    request = _request("prior-release.xml")
    request["files"][0].update(
        name="partial.xml",
        checksum=hashlib.sha256(content).hexdigest(),
        contentReference=str(source_path),
    )

    outcome = _ingest(request, tmp_path / "captures")

    assert outcome.processing_status == "FAILED"
    assert outcome.snapshots == ()
    assert "full-coverage" in outcome.failure_detail


@pytest.mark.parametrize(
    ("value", "evidence_class"),
    [(None, "UNKNOWN"), ("inferred-1", "INFERRED"), ("", "VERIFIED"), ("999", "VERIFIED")],
)
def test_declared_source_order_is_recorded_but_chronology_comes_from_ajopvm(
    tmp_path, value, evidence_class
):
    outcome = _ingest(
        _request(
            "prior-release.xml",
            source_order={"value": value, "evidenceClass": evidence_class},
        ),
        tmp_path,
    )

    assert outcome.processing_status == "VALIDATED"
    assert outcome.declared_source_order.value == value
    assert outcome.source_order.value == "2099-01-01"
    assert outcome.source_order.evidence_class == "VERIFIED"
    assert outcome.chronology_status.value == "AVAILABLE"


def test_caller_cannot_claim_verified_order_for_release_without_ajopvm(tmp_path):
    outcome = _ingest(
        _request(
            "ordering-unknown-release.xml",
            source_order={"value": "5", "evidenceClass": "VERIFIED"},
        ),
        tmp_path,
    )

    assert outcome.processing_status == "VALIDATED"
    assert outcome.source_order.evidence_class == "UNKNOWN"
    assert outcome.chronology_status.value == "UNAVAILABLE"


def test_source_order_is_optional_in_the_request(tmp_path):
    request = _request("prior-release.xml")
    del request["sourceOrder"]

    outcome = _ingest(request, tmp_path)

    assert outcome.processing_status == "VALIDATED"
    assert outcome.declared_source_order is None
    assert outcome.chronology_status.value == "AVAILABLE"


@pytest.mark.parametrize("ajopvm", [b"<Ajopvm/>", b"<Ajopvm>06.10.2026</Ajopvm>", b""])
def test_absent_empty_or_non_iso_ajopvm_leaves_chronology_unknown(tmp_path, ajopvm):
    content = (
        (FIXTURE_DIR / "prior-release.xml")
        .read_bytes()
        .replace(b"<Ajopvm>2099-01-01</Ajopvm>", ajopvm)
    )
    source_path = tmp_path / "variant.xml"
    source_path.write_bytes(content)
    request = _request("prior-release.xml")
    request["files"][0].update(
        name="variant.xml",
        checksum=hashlib.sha256(content).hexdigest(),
        contentReference=str(source_path),
    )

    outcome = _ingest(request, tmp_path / "captures")

    assert outcome.processing_status == "VALIDATED"
    assert outcome.source_order.evidence_class == "UNKNOWN"
    assert outcome.chronology_status.value == "UNAVAILABLE"


def test_captured_release_can_be_reloaded_from_disk(tmp_path):
    from src.services.ingest_source_release import reload_captured_release

    original = _ingest(_request("prior-release.xml"), tmp_path)
    reloaded = reload_captured_release(original.captured_release.capture_directory)

    assert reloaded.processing_status == "VALIDATED"
    assert reloaded.snapshots == original.snapshots
    assert reloaded.source_order == original.source_order
    assert reloaded.captured_release.release_id == original.captured_release.release_id


def test_tampered_capture_is_not_reloaded(tmp_path):
    from src.services.ingest_source_release import reload_captured_release

    original = _ingest(_request("prior-release.xml"), tmp_path)
    captured = original.captured_release
    stored = captured.capture_directory / captured.files[0].content_reference
    stored.write_bytes(stored.read_bytes() + b"<!-- edited -->")

    with pytest.raises(ValueError, match="checksum"):
        reload_captured_release(captured.capture_directory)


@pytest.mark.parametrize("status", ["PARTIAL", "UNKNOWN"])
def test_non_complete_capture_status_is_rejected(status):
    from src.services.ingest_source_release import ingest_source_release

    with pytest.raises(ValueError, match="captureStatus"):
        ingest_source_release(
            _request("prior-release.xml", capture_status=status),
            storage_dir=Path("unused"),
        )


def test_multiple_files_are_validated_atomically(tmp_path):
    request = _request("prior-release.xml")
    invalid_content = (FIXTURE_DIR / "malformed-release.xml").read_bytes()
    invalid_path = tmp_path / "malformed.xml"
    invalid_path.write_bytes(invalid_content)
    request["files"].append(
        {
            "name": "malformed.xml",
            "checksum": hashlib.sha256(invalid_content).hexdigest(),
            "contentReference": str(invalid_path),
        }
    )

    outcome = _ingest(request, tmp_path / "captures")

    assert outcome.processing_status == "FAILED"
    assert outcome.snapshots == ()
    assert outcome.source_releases == ()
    assert outcome.captured_release is not None
    assert len(outcome.captured_release.files) == 2


def test_duplicate_records_across_files_fail_atomically(tmp_path):
    request = _request("prior-release.xml")
    second_path = FIXTURE_DIR / "current-release.xml"
    request["files"].append(
        {
            "name": "current-release.xml",
            "checksum": hashlib.sha256(second_path.read_bytes()).hexdigest(),
            "contentReference": str(second_path.resolve()),
        }
    )

    outcome = _ingest(request, tmp_path)

    assert outcome.processing_status == "FAILED"
    assert outcome.snapshots == ()
    assert "Duplicate package identifier" in outcome.failure_detail
