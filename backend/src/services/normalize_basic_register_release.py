"""Read the selected no-namespace XML format without inventing source values.

This boundary parses a complete supplied document; raw capture, checksum verification,
source ordering and ingestion status belong to the subsequent ingestion tasks.
"""

from pathlib import Path
from xml.etree import ElementTree as ET

from ..domain.medicine_snapshot import (
    ActiveSubstanceFields,
    AuthorizationBranch,
    AuthorizationRegistrationFields,
    MedicineSnapshot,
    PackageAvailabilityFields,
    PackageFields,
    ProductFields,
)
from ..domain.source_field import SourceField
from ..domain.source_release import SourceProvenance, SourceRelease


def _field(parent: ET.Element, name: str) -> SourceField:
    elements = parent.findall(name)
    if len(elements) > 1:
        raise ValueError(f"Repeated singular field: {name}")
    if not elements:
        return SourceField.missing()
    element = elements[0]
    if len(element):
        raise ValueError(f"Expected a scalar source field: {name}")
    return SourceField.of(element.text or "", attributes=tuple(element.attrib.items()))


def _index(root: ET.Element, tag: str) -> dict[str, ET.Element]:
    result = {}
    for element in root.findall(tag):
        key = element.get("id")
        if not key or key in result:
            raise ValueError(f"Missing or duplicate {tag} id: {key!r}")
        result[key] = element
    return result


def normalize_basic_register_release(
    content: bytes, *, file_name: str, checksum: str
) -> tuple[SourceRelease, tuple[MedicineSnapshot, ...]]:
    """Return all snapshots atomically, or raise on malformed/ambiguous links.

    Checksum is caller-supplied provenance, not a claim of verified raw capture.
    Code-table attributes remain attributes, including their display value.
    """
    # The selected source format uses neither DTDs nor entity declarations.
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise ValueError("DTD and entity declarations are unsupported")
    root = ET.fromstring(content)
    if root.tag != "Perusrekisteri":
        raise ValueError("Expected a no-namespace Perusrekisteri document")
    versions = root.findall("Versiotiedot")
    if len(versions) != 1:
        raise ValueError("Exactly one Versiotiedot is required")
    version = versions[0]
    if _field(version, "Kattavuus").value != "1":
        raise ValueError("Only full-coverage documents can be normalized")
    release = SourceRelease(
        ajopvm=_field(version, "Ajopvm"),
        aineistoera=_field(version, "Aineistoera"),
        kkera=_field(version, "Kkera"),
        kattavuus=_field(version, "Kattavuus"),
        provenance=SourceProvenance("Fimea Basic Register", file_name, checksum),
    )
    products = _index(root, "Laakevalmiste")
    substances = _index(root, "Laakeaine")
    snapshots = []
    package_keys = set()
    for position, package in enumerate(root.findall("Pakkaus"), start=1):
        key = _field(package, "Pakkaustunnus").value
        if not key or key in package_keys:
            raise ValueError(f"Missing or duplicate Pakkaustunnus: {key!r}")
        package_keys.add(key)
        product_ref = package.get("Laakevalmiste-ref")
        if product_ref not in products:
            raise ValueError(f"Unresolved product reference: {product_ref!r}")
        product = products[product_ref]
        active = []
        for link in package.findall("Pakkaus_Laakeaine"):
            substance_ref = link.get("Laakeaine-ref")
            if substance_ref not in substances:
                raise ValueError(f"Unresolved substance reference: {substance_ref!r}")
            for item in substances[substance_ref].findall("VaikuttavaAine"):
                active.append(
                    ActiveSubstanceFields(
                        *(
                            _field(item, name)
                            for name in (
                                "Aine",
                                "CASnumero",
                                "Maara",
                                "Maarayksikko",
                                "JakamatonVahvuus",
                            )
                        )
                    )
                )
        authorizations = tuple(
            AuthorizationRegistrationFields(
                AuthorizationBranch(item.tag),
                _field(item, "Tila"),
                _field(item, "Myontamispaiva"),
                _field(item, "Paattymispaiva"),
            )
            for item in product
            if item.tag in {branch.value for branch in AuthorizationBranch}
        )
        availability = package.findall("Kaupanolo")
        if len(availability) > 1:
            raise ValueError("Repeated Kaupanolo")
        availability_parent = availability[0] if availability else ET.Element("Kaupanolo")
        snapshots.append(
            MedicineSnapshot(
                pakkaustunnus=key,
                vnr_numero=_field(package, "VNR-numero"),
                product_reference=SourceField.of(product_ref),
                product=ProductFields(
                    *(
                        _field(product, name)
                        for name in ("Kauppanimi", "Vahvuus", "Laakemuoto", "ATC-koodi")
                    ),
                    antoreitti=tuple(
                        SourceField.of(item.text or "", attributes=tuple(item.attrib.items()))
                        for item in product.findall("Antoreitti")
                    ),
                ),
                active_substances=tuple(active),
                package=PackageFields(
                    *(
                        _field(package, name)
                        for name in (
                            "Pakkauskokoteksti",
                            "Pakkauskoko",
                            "Pakkauskokokerroin",
                            "Pakkauskokoyksikko",
                            "JulkinenTarkenne",
                        )
                    ),
                    availability=PackageAvailabilityFields(
                        *(
                            _field(availability_parent, name)
                            for name in ("Kaupan", "Kauppaantulopaiva", "Kaupastapoistumispaiva")
                        )
                    ),
                ),
                authorizations=authorizations,
                source_release=release,
                source_record_locator=f"/Perusrekisteri/Pakkaus[{position}]",
            )
        )
    return release, tuple(snapshots)


def read_basic_register_release(
    path: str | Path, *, checksum: str
) -> tuple[SourceRelease, tuple[MedicineSnapshot, ...]]:
    """Read one local raw file; I/O errors remain explicit to the ingestion caller."""
    path = Path(path)
    return normalize_basic_register_release(
        path.read_bytes(), file_name=path.name, checksum=checksum
    )
