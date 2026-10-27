import hashlib
import json
from datetime import UTC, datetime

import pytest

from src.domain.evidence import EvidenceClassification
from src.services.capture_source_release import (
    RawReleaseFile,
    SourceEvidence,
    capture_source_release,
)


def _capture(tmp_path, *, source_order=None, content=b"<release />"):
    return capture_source_release(
        storage_dir=tmp_path,
        source_name="Fimea Basic Register",
        source_release_reference=SourceEvidence("SIM-2099-001", EvidenceClassification.VERIFIED),
        source_order=source_order or SourceEvidence("12", EvidenceClassification.VERIFIED),
        retrieved_at=datetime(2099, 1, 4, tzinfo=UTC),
        files=(
            RawReleaseFile(
                "release.xml",
                content,
                ("/Perusrekisteri/Pakkaus[1]", "/Perusrekisteri/Pakkaus[2]"),
            ),
        ),
    )


def test_capture_persists_content_checksum_metadata_and_record_locators(tmp_path):
    captured = _capture(tmp_path)
    item = captured.files[0]
    manifest = json.loads((captured.capture_directory / "manifest.json").read_text("utf-8"))

    assert (captured.capture_directory / item.content_reference).read_bytes() == b"<release />"
    assert item.checksum == hashlib.sha256(b"<release />").hexdigest()
    assert manifest["sourceName"] == "Fimea Basic Register"
    assert manifest["sourceReleaseReference"] == {
        "value": "SIM-2099-001",
        "evidenceClass": "VERIFIED",
    }
    assert manifest["sourceOrder"] == {"value": "12", "evidenceClass": "VERIFIED"}
    assert manifest["retrievedAt"] == "2099-01-04T00:00:00+00:00"
    assert manifest["files"][0]["recordLocators"] == [
        "/Perusrekisteri/Pakkaus[1]",
        "/Perusrekisteri/Pakkaus[2]",
    ]


def test_unknown_source_order_is_not_derived_from_retrieval_time(tmp_path):
    captured = _capture(
        tmp_path,
        source_order=SourceEvidence(None, EvidenceClassification.UNKNOWN),
    )
    manifest = json.loads((captured.capture_directory / "manifest.json").read_text("utf-8"))

    assert manifest["sourceOrder"] == {"value": None, "evidenceClass": "UNKNOWN"}
    assert manifest["retrievedAt"] == "2099-01-04T00:00:00+00:00"


def test_identical_capture_is_idempotent(tmp_path):
    first = _capture(tmp_path)
    second = _capture(tmp_path)

    assert second == first
    assert len(list(tmp_path.iterdir())) == 1


def test_existing_raw_file_is_never_silently_overwritten(tmp_path):
    captured = _capture(tmp_path)
    stored_file = captured.capture_directory / captured.files[0].content_reference
    stored_file.write_bytes(b"modified")

    with pytest.raises(FileExistsError, match="Existing raw file differs"):
        _capture(tmp_path)

    assert stored_file.read_bytes() == b"modified"


@pytest.mark.parametrize("file_name", ["", ".", "..", "../release.xml", "sub\\release.xml"])
def test_capture_rejects_non_basename_file_names(tmp_path, file_name):
    with pytest.raises(ValueError, match="base name"):
        RawReleaseFile(file_name, b"content")


def test_capture_requires_timezone_aware_retrieval_time(tmp_path):
    with pytest.raises(ValueError, match="timezone-aware"):
        capture_source_release(
            storage_dir=tmp_path,
            source_name="Fimea Basic Register",
            source_release_reference=SourceEvidence(None, EvidenceClassification.UNKNOWN),
            source_order=SourceEvidence(None, EvidenceClassification.UNKNOWN),
            retrieved_at=datetime.fromisoformat("2099-01-04T00:00:00"),
            files=(RawReleaseFile("release.xml", b"<release />"),),
        )
