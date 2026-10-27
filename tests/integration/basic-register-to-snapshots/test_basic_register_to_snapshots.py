"""T021: exercise real file reads through normalization and the comparison boundary."""

import hashlib
from pathlib import Path
from xml.etree.ElementTree import ParseError

import pytest
from src.domain.evidence import EvidenceClassification
from src.services.detect_relevant_changes import SourceOrderEvidence, detect_relevant_changes
from src.services.normalize_basic_register_release import (
    normalize_basic_register_release,
    read_basic_register_release,
)

FIXTURES = Path(__file__).parents[2] / "fixtures" / "fimea-basic-register"


def test_two_files_produce_traceable_changes_only_with_explicit_fixture_order():
    prior_release, prior = read_basic_register_release(
        FIXTURES / "prior-release.xml", checksum="prior-checksum"
    )
    current_release, current = read_basic_register_release(
        FIXTURES / "current-release.xml", checksum="current-checksum"
    )
    order = SourceOrderEvidence(
        prior_release,
        current_release,
        1,
        2,
        EvidenceClassification.VERIFIED,
        "Controlled synthetic fixture sequence; not verified live-source chronology.",
    )
    result = detect_relevant_changes(prior, current, order=order)
    assert result.changes
    name_change = next(
        change for change in result.changes if change.field_name == "Laakevalmiste/Kauppanimi"
    )
    assert name_change.medicine_key == "SIM-PKG-100"
    assert name_change.prior_value[0].value == "Fictional Product Amber"
    assert name_change.current_value[0].value == "Fictional Product Amber Revised"


@pytest.mark.parametrize("filename", ["prior-release.xml", "current-release.xml"])
def test_file_to_snapshots_retains_release_and_raw_record_provenance(filename):
    path = FIXTURES / filename
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    release, snapshots = read_basic_register_release(path, checksum=checksum)
    assert len(snapshots) == 3
    assert release.provenance.raw_file_name == filename
    assert release.provenance.raw_file_checksum == checksum
    assert release.aineistoera.value.startswith("SIM-")
    for index, snapshot in enumerate(snapshots, start=1):
        assert snapshot.source_release is release
        assert snapshot.source_record_locator == f"/Perusrekisteri/Pakkaus[{index}]"
        assert snapshot.product.kauppanimi.value.startswith("Fictional Product")
        assert snapshot.active_substances[0].cas_numero.value.startswith("SIM-CAS-")


def test_missing_source_order_is_not_invented_from_file_metadata():
    release, snapshots = read_basic_register_release(
        FIXTURES / "ordering-unknown-release.xml", checksum="fixture"
    )
    assert release.ajopvm.state.value == "missing"
    assert release.aineistoera.state.value == "missing"
    _, prior = read_basic_register_release(FIXTURES / "prior-release.xml", checksum="fixture")
    assert not detect_relevant_changes(prior, snapshots, order=None).changes


@pytest.mark.parametrize("filename", ["malformed-release.xml", "unavailable.xml"])
def test_failed_file_read_or_parse_never_returns_partial_snapshots(filename):
    with pytest.raises((OSError, ValueError, ParseError)):
        read_basic_register_release(FIXTURES / filename, checksum="fixture")


@pytest.mark.parametrize("mutation", ["product", "substance", "duplicate", "coverage", "truncated"])
def test_invalid_release_is_rejected_atomically_even_after_valid_records(mutation):
    content = (FIXTURES / "prior-release.xml").read_bytes()
    if mutation == "product":
        content = content.replace(
            b'Laakevalmiste-ref="SYN-PROD-300"', b'Laakevalmiste-ref="absent"'
        )
    elif mutation == "substance":
        content = content.replace(b'Laakeaine-ref="SYN-SUB-300"', b'Laakeaine-ref="absent"')
    elif mutation == "duplicate":
        content = content.replace(b"SIM-PKG-300", b"SIM-PKG-100")
    elif mutation == "coverage":
        content = content.replace(b"<Kattavuus>1</Kattavuus>", b"<Kattavuus>0</Kattavuus>")
    else:
        content = content[:-30]
    with pytest.raises((ValueError, ParseError)):
        normalize_basic_register_release(content, file_name="invalid.xml", checksum="fixture")


def test_repeated_elements_raw_whitespace_and_leading_zero_identifiers_are_preserved():
    content = (FIXTURES / "prior-release.xml").read_bytes()
    content = content.replace(b"SIM-PKG-100", b"000100")
    content = content.replace(b"Fictional Product Amber", b" Fictional Product Amber ")
    content = content.replace(b"<Antoreitti/>", b"<Antoreitti/><Antoreitti>second</Antoreitti>")
    content = content.replace(
        b"</VaikuttavaAine>",
        b"</VaikuttavaAine><VaikuttavaAine><Aine>second substance</Aine></VaikuttavaAine>",
        1,
    )
    _, snapshots = normalize_basic_register_release(content, file_name="repeated.xml", checksum="x")
    assert snapshots[0].pakkaustunnus == "000100"
    assert snapshots[0].product.kauppanimi.value == " Fictional Product Amber "
    assert len(snapshots[0].active_substances) == 2
    assert snapshots[0].active_substances[1].aine.value == "second substance"
    assert [field.value for field in snapshots[1].product.antoreitti] == ["", "second"]
