from pathlib import Path
from xml.etree.ElementTree import ParseError

import pytest

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "fimea-basic-register"


def _normalize(filename: str):
    from src.services.normalize_basic_register_release import (
        normalize_basic_register_release,
    )

    content = (FIXTURE_DIR / filename).read_bytes()
    return normalize_basic_register_release(
        content,
        file_name=filename,
        checksum=f"synthetic-checksum-{filename}",
    )


def test_prior_release_preserves_provenance_and_field_states():
    release, snapshots = _normalize("prior-release.xml")

    assert release.provenance.source_name == "Fimea Basic Register"
    assert release.provenance.raw_file_name == "prior-release.xml"
    assert release.provenance.raw_file_checksum == "synthetic-checksum-prior-release.xml"
    assert release.ajopvm.value == "2099-01-01"
    assert release.aineistoera.value == "SIM-2099-001"
    package = next(item for item in snapshots if item.pakkaustunnus == "SIM-PKG-100")
    assert package.source_record_locator
    assert package.product_reference.value == "SYN-PROD-100"
    assert package.product.kauppanimi.value == "Fictional Product Amber"
    assert package.package.julkinen_tarkenne.value == "synthetic detail A"


def test_normalization_resolves_product_and_substance_links_with_source_values():
    _, snapshots = _normalize("current-release.xml")
    package = next(item for item in snapshots if item.pakkaustunnus == "SIM-PKG-100")

    assert package.product_reference.value == "SYN-PROD-100"
    assert package.product.kauppanimi.value == "Fictional Product Amber Revised"
    assert package.active_substances[0].aine.value == "fictional substance amber"
    assert package.active_substances[0].cas_numero.value == "SIM-CAS-100"
    assert package.package.pakkauskoko.value == "10"
    assert package.package.pakkauskokoyksikko.attributes == (
        ("listname", "SIM-UNIT"),
        ("id", "SIM-COUNT"),
        ("value", "fictional units"),
    )


def test_normalization_distinguishes_absent_and_empty_fields():
    _, snapshots = _normalize("prior-release.xml")
    package = next(item for item in snapshots if item.pakkaustunnus == "SIM-PKG-200")
    populated_package = next(item for item in snapshots if item.pakkaustunnus == "SIM-PKG-100")

    assert package.package.julkinen_tarkenne.state.value == "empty"
    assert populated_package.package.julkinen_tarkenne.state.value == "value"
    assert package.product.antoreitti[0].state.value == "empty"
    current_release, current_snapshots = _normalize("current-release.xml")
    missing_package = next(item for item in current_snapshots if item.pakkaustunnus == "SIM-PKG-400")
    assert missing_package.package.julkinen_tarkenne.state.value == "missing"
    assert current_release.ajopvm.value == "2099-01-02"


def test_normalization_retains_repeated_source_elements_and_authorization_branch():
    _, snapshots = _normalize("current-release.xml")
    package = next(item for item in snapshots if item.pakkaustunnus == "SIM-PKG-100")
    special_authorized = next(item for item in snapshots if item.pakkaustunnus == "SIM-PKG-400")

    assert isinstance(package.product.antoreitti, tuple)
    assert len(package.product.antoreitti) == 1
    assert special_authorized.authorizations[0].branch.value == "Erityislupa"
    assert special_authorized.authorizations[0].tila.value == "synthetic granted"


@pytest.mark.parametrize("filename", ["malformed-release.xml"])
def test_parser_rejects_malformed_synthetic_xml(filename):
    from src.services.normalize_basic_register_release import (
        normalize_basic_register_release,
    )

    content = (FIXTURE_DIR / filename).read_bytes()
    with pytest.raises((ValueError, ParseError)):
        normalize_basic_register_release(
            content, file_name=filename, checksum=f"synthetic-checksum-{filename}"
        )
