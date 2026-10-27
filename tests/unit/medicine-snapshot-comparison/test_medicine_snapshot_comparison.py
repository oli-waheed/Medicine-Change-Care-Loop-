"""Contract tests for source comparison fixtures; no production comparison logic."""

import json
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from src.domain.evidence import EvidenceClassification, EvidenceProvenance
from src.domain.source_field import SourceField
from src.domain.source_release import SourceProvenance, SourceRelease

FIXTURES = Path(__file__).parents[2] / "fixtures"
FIMEA_FIXTURES = FIXTURES / "fimea-basic-register"


@dataclass(frozen=True)
class SyntheticRelease:
    root: ElementTree.Element
    metadata: SourceRelease

    def packages_by_identifier(self) -> dict[str, ElementTree.Element]:
        return {
            package.findtext("Pakkaustunnus", default=""): package
            for package in self.root.findall("Pakkaus")
        }


def _source_field(element: ElementTree.Element | None) -> SourceField:
    if element is None:
        return SourceField.missing()

    attributes = tuple(sorted(element.attrib.items()))
    return SourceField.of(element.text or "", attributes=attributes)


def _read_release(filename: str) -> SyntheticRelease:
    root = ElementTree.parse(FIMEA_FIXTURES / filename).getroot()
    metadata = root.find("Versiotiedot")
    assert metadata is not None

    return SyntheticRelease(
        root=root,
        metadata=SourceRelease(
            ajopvm=_source_field(metadata.find("Ajopvm")),
            aineistoera=_source_field(metadata.find("Aineistoera")),
            kkera=_source_field(metadata.find("Kkera")),
            kattavuus=_source_field(metadata.find("Kattavuus")),
            provenance=SourceProvenance(
                source_name="Synthetic Fimea Basic Register",
                raw_file_name=filename,
                raw_file_checksum=f"synthetic-checksum-{filename}",
            ),
        ),
    )


def _comparison_fields(
    root: ElementTree.Element, package: ElementTree.Element
) -> tuple[tuple[str, tuple[SourceField, ...]], ...]:
    """Project only T005 fields from XML for assertions about the synthetic fixture."""
    product_id = package.attrib["Laakevalmiste-ref"]
    products_by_id = {product.attrib["id"]: product for product in root.findall("Laakevalmiste")}
    product = products_by_id[product_id]
    fields: list[tuple[str, tuple[SourceField, ...]]] = []

    for field_name in ("Kauppanimi", "Vahvuus", "Laakemuoto", "ATC-koodi", "Antoreitti"):
        fields.append(
            (
                f"Product/{field_name}",
                tuple(_source_field(element) for element in product.findall(field_name)),
            )
        )

    substances_by_id = {
        substance.attrib["id"]: substance for substance in root.findall("Laakeaine")
    }
    linked_substances = (
        substances_by_id[reference.attrib["Laakeaine-ref"]]
        for reference in package.findall("Pakkaus_Laakeaine")
    )
    active_names = ("Aine", "CASnumero", "Maara", "Maarayksikko", "JakamatonVahvuus")
    for substance in linked_substances:
        for active in substance.findall("VaikuttavaAine"):
            for field_name in active_names:
                fields.append(
                    (
                        f"ActiveSubstance/{field_name}",
                        tuple(_source_field(element) for element in active.findall(field_name)),
                    )
                )

    package_names = (
        "Pakkauskokoteksti",
        "Pakkauskoko",
        "Pakkauskokokerroin",
        "Pakkauskokoyksikko",
        "JulkinenTarkenne",
    )
    for field_name in package_names:
        fields.append(
            (
                f"Package/{field_name}",
                tuple(_source_field(element) for element in package.findall(field_name)),
            )
        )

    availability = package.find("Kaupanolo")
    for field_name in ("Kaupan", "Kauppaantulopaiva", "Kaupastapoistumispaiva"):
        element = None if availability is None else availability.find(field_name)
        fields.append((f"Package/Kaupanolo/{field_name}", (_source_field(element),)))

    for branch_name in ("Myyntilupa", "Erityislupa", "Rekisterointi"):
        branch = product.find(branch_name)
        if branch is None:
            continue
        for field_name in ("Tila", "Myontamispaiva", "Paattymispaiva"):
            fields.append(
                (
                    f"Authorization/{branch_name}/{field_name}",
                    (_source_field(branch.find(field_name)),),
                )
            )

    return tuple(fields)


def _field_changes(
    prior: tuple[tuple[str, tuple[SourceField, ...]], ...],
    current: tuple[tuple[str, tuple[SourceField, ...]], ...],
) -> tuple[str, ...]:
    """Test-only oracle over the selected fixture field projections."""
    prior_by_path = dict(prior)
    current_by_path = dict(current)
    return tuple(
        path
        for path in prior_by_path.keys() | current_by_path.keys()
        if prior_by_path.get(path) != current_by_path.get(path)
    )


def test_same_package_with_t005_field_change_is_detected_in_fixture() -> None:
    prior = _read_release("prior-release.xml")
    current = _read_release("current-release.xml")
    prior_package = prior.packages_by_identifier()["SIM-PKG-100"]
    current_package = current.packages_by_identifier()["SIM-PKG-100"]

    changes = _field_changes(
        _comparison_fields(prior.root, prior_package),
        _comparison_fields(current.root, current_package),
    )

    assert "Product/Kauppanimi" in changes
    assert "Package/JulkinenTarkenne" in changes
    assert "SIM-PKG-100" == prior_package.findtext("Pakkaustunnus")
    assert "SIM-PKG-100" == current_package.findtext("Pakkaustunnus")


def test_same_package_with_no_t005_field_changes_is_unchanged_in_fixture() -> None:
    prior = _read_release("prior-release.xml")
    current = _read_release("current-release.xml")

    prior_fields = _comparison_fields(prior.root, prior.packages_by_identifier()["SIM-PKG-200"])
    current_fields = _comparison_fields(
        current.root, current.packages_by_identifier()["SIM-PKG-200"]
    )

    assert _field_changes(prior_fields, current_fields) == ()


def test_release_package_sets_expose_current_only_and_previous_only_records() -> None:
    prior_ids = set(_read_release("prior-release.xml").packages_by_identifier())
    current_ids = set(_read_release("current-release.xml").packages_by_identifier())

    assert current_ids - prior_ids == {"SIM-PKG-400"}
    assert prior_ids - current_ids == {"SIM-PKG-300"}


def test_missing_and_present_empty_source_fields_are_different_states() -> None:
    prior = _read_release("prior-release.xml")
    current = _read_release("current-release.xml")
    prior_detail = _source_field(
        prior.packages_by_identifier()["SIM-PKG-100"].find("JulkinenTarkenne")
    )
    current_detail = _source_field(
        current.packages_by_identifier()["SIM-PKG-200"].find("JulkinenTarkenne")
    )
    missing = _source_field(
        current.packages_by_identifier()["SIM-PKG-100"].find("JulkinenTarkenne")
    )

    assert prior_detail.state != SourceField.missing().state
    assert current_detail == SourceField.empty()
    assert missing == SourceField.missing()
    assert current_detail != missing


def test_release_order_comes_from_source_metadata_not_retrieval_time() -> None:
    prior = _read_release("prior-release.xml").metadata
    current = _read_release("current-release.xml").metadata

    assert prior.ajopvm.value == "2099-01-01"
    assert current.ajopvm.value == "2099-01-02"
    assert prior.aineistoera.value == "SIM-2099-001"
    assert current.aineistoera.value == "SIM-2099-002"
    assert prior.provenance.source_name == current.provenance.source_name
    assert not hasattr(prior, "retrieved_at")
    assert not hasattr(current, "retrieved_at")


def test_comparison_evidence_retains_source_release_and_package_trace() -> None:
    release = _read_release("current-release.xml")
    package = release.packages_by_identifier()["SIM-PKG-100"]
    evidence = EvidenceProvenance(
        source_release=release.metadata,
        source_record_identifier=package.findtext("Pakkaustunnus", default=""),
        source_record_locator="/Perusrekisteri/Pakkaus[1]",
        field_reference="Laakevalmiste/Kauppanimi",
        classification=EvidenceClassification.VERIFIED,
        source_value=_source_field(
            release.root.find("Laakevalmiste[@id='SYN-PROD-100']/Kauppanimi")
        ),
    )

    assert evidence.source_release.aineistoera.value == "SIM-2099-002"
    assert evidence.source_release.ajopvm.value == "2099-01-02"
    assert evidence.source_record_identifier == "SIM-PKG-100"
    assert evidence.field_reference == "Laakevalmiste/Kauppanimi"


def test_missing_package_identifier_does_not_fall_back_to_vnr() -> None:
    medications = json.loads(
        (FIXTURES / "simulated-medication-records" / "medication-records.json").read_text(
            encoding="utf-8"
        )
    )
    records = medications["records"]
    primary_absent = next(record for record in records if record["record_id"] == "SIM-MED-005")
    primary_present = next(record for record in records if record["record_id"] == "SIM-MED-001")

    assert medications["primary_package_key"] == "Pakkaustunnus"
    assert medications["supporting_package_field"] == "VNR-numero"
    assert "Pakkaustunnus" not in primary_absent
    assert primary_absent["VNR-numero"] == primary_present["VNR-numero"]
