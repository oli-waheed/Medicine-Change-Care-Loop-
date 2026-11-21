"""Read the selected no-namespace XML format without inventing source values.

This boundary parses a complete supplied document; raw capture, checksum verification,
source ordering and ingestion status belong to the subsequent ingestion tasks.
"""

import io
from collections import Counter
from datetime import datetime
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

_MISSING = SourceField.missing()


class _Fields:
    """Builds source fields, sharing one object per distinct value (feature 009).

    A real release has about 3.9 million field occurrences but only about
    90,000 distinct values. Source fields are immutable, so sharing them changes
    no value; it saves most of the memory and the repeated validation.
    """

    def __init__(self) -> None:
        self._known: dict[tuple[str, tuple[tuple[str, str], ...]], SourceField] = {}

    def of(self, text: str, attributes: tuple[tuple[str, str], ...]) -> SourceField:
        key = (text, attributes)
        known = self._known.get(key)
        if known is None:
            known = self._known[key] = SourceField.of(text, attributes=attributes)
        return known

    def field(self, parent: ET.Element, name: str) -> SourceField:
        elements = parent.findall(name)
        if len(elements) > 1:
            raise ValueError(f"Repeated singular field: {name}")
        if not elements:
            return _MISSING
        element = elements[0]
        if len(element):
            raise ValueError(f"Expected a scalar source field: {name}")
        return self.of(element.text or "", tuple(element.attrib.items()))


class _Deferred:
    """A record's normalised value, or the error to raise when it is used."""

    __slots__ = ("error", "value")

    def __init__(self, build) -> None:
        try:
            self.value, self.error = build(), None
        except ValueError as error:
            self.value, self.error = None, error

    def get(self):
        if self.error is not None:
            raise self.error
        return self.value


_SUBSTANCE_FIELDS = ("Aine", "CASnumero", "Maara", "Maarayksikko", "JakamatonVahvuus")
_PRODUCT_FIELDS = ("Kauppanimi", "Vahvuus", "Laakemuoto", "ATC-koodi")
_PACKAGE_FIELDS = (
    "Pakkauskokoteksti",
    "Pakkauskoko",
    "Pakkauskokokerroin",
    "Pakkauskokoyksikko",
    "JulkinenTarkenne",
)
_AVAILABILITY_FIELDS = ("Kaupan", "Kauppaantulopaiva", "Kaupastapoistumispaiva")
_BRANCHES = frozenset(branch.value for branch in AuthorizationBranch)
_SCHEMA_LOCATION = "{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation"


def _count_paths(element: ET.Element, prefix: str, counts: Counter) -> None:
    """Count every element path under a top-level record (feature 014)."""
    path = f"{prefix}/{element.tag}"
    counts[path] += 1
    for child in element:
        _count_paths(child, path, counts)


def normalize_basic_register_release(
    content: bytes,
    *,
    file_name: str,
    checksum: str,
    retrieved_at: datetime | None = None,
) -> tuple[SourceRelease, tuple[MedicineSnapshot, ...]]:
    """Return all snapshots atomically, or raise on malformed/ambiguous links.

    Checksum is caller-supplied provenance, not a claim of verified raw capture.
    Code-table attributes remain attributes, including their display value.

    Feature 009: the document is read as a stream. Each top-level record is
    normalised when it ends and then dropped, and each product and substance
    record is normalised once and shared by its packages, so the whole XML tree
    is never held in memory. Checks run after reading, in the same order as
    before, so the same document gives the same result or the same error.
    """
    # The selected source format uses neither DTDs nor entity declarations.
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise ValueError("DTD and entity declarations are unsupported")
    fields = _Fields()
    field = fields.field

    root_tag = None
    versions: list[_Deferred] = []
    products: dict[str, _Deferred] = {}
    substances: dict[str, _Deferred] = {}
    index_errors: dict[str, ValueError] = {}
    packages: list[tuple] = []

    def index(tag: str, table: dict, element: ET.Element, build) -> None:
        key = element.get("id")
        if not key or key in table:
            index_errors.setdefault(tag, ValueError(f"Missing or duplicate {tag} id: {key!r}"))
            return
        table[key] = _Deferred(lambda: build(element))

    def version_fields(element: ET.Element):
        return {
            name: field(element, name) for name in ("Kattavuus", "Ajopvm", "Aineistoera", "Kkera")
        }

    def product_fields(product: ET.Element):
        return (
            ProductFields(
                *(field(product, name) for name in _PRODUCT_FIELDS),
                antoreitti=tuple(
                    fields.of(item.text or "", tuple(item.attrib.items()))
                    for item in product.findall("Antoreitti")
                ),
            ),
            tuple(
                AuthorizationRegistrationFields(
                    AuthorizationBranch(item.tag),
                    field(item, "Tila"),
                    field(item, "Myontamispaiva"),
                    field(item, "Paattymispaiva"),
                    field(item, "Haltija"),
                )
                for item in product
                if item.tag in _BRANCHES
            ),
        )

    def substance_fields(substance: ET.Element):
        return tuple(
            ActiveSubstanceFields(*(field(item, name) for name in _SUBSTANCE_FIELDS))
            for item in substance.findall("VaikuttavaAine")
        )

    def package_record(package: ET.Element):
        def rest():
            availability = package.findall("Kaupanolo")
            if len(availability) > 1:
                raise ValueError("Repeated Kaupanolo")
            parent = availability[0] if availability else ET.Element("Kaupanolo")
            return (
                field(package, "VNR-numero"),
                PackageFields(
                    *(field(package, name) for name in _PACKAGE_FIELDS),
                    availability=PackageAvailabilityFields(
                        *(field(parent, name) for name in _AVAILABILITY_FIELDS)
                    ),
                ),
            )

        return (
            _Deferred(lambda: field(package, "Pakkaustunnus").value),
            package.get("Laakevalmiste-ref"),
            tuple(link.get("Laakeaine-ref") for link in package.findall("Pakkaus_Laakeaine")),
            _Deferred(rest),
        )

    depth = 0
    root = None
    schema_location = None
    structure: Counter = Counter()
    for event, element in ET.iterparse(io.BytesIO(content), events=("start", "end")):
        if event == "start":
            if depth == 0:
                root, root_tag = element, element.tag
                schema_location = element.get(_SCHEMA_LOCATION)
            depth += 1
            continue
        depth -= 1
        if depth != 1:
            continue
        tag = element.tag
        _count_paths(element, root.tag, structure)
        if tag == "Pakkaus":
            packages.append(package_record(element))
        elif tag == "Laakevalmiste":
            index(tag, products, element, product_fields)
        elif tag == "Laakeaine":
            index(tag, substances, element, substance_fields)
        elif tag == "Versiotiedot":
            versions.append(_Deferred(lambda element=element: version_fields(element)))
        del root[:]  # this record is done; drop it from memory

    if root_tag != "Perusrekisteri":
        raise ValueError("Expected a no-namespace Perusrekisteri document")
    if len(versions) != 1:
        raise ValueError("Exactly one Versiotiedot is required")
    version = versions[0].get()
    if version["Kattavuus"].value != "1":
        raise ValueError("Only full-coverage documents can be normalized")
    release = SourceRelease(
        ajopvm=version["Ajopvm"],
        aineistoera=version["Aineistoera"],
        kkera=version["Kkera"],
        kattavuus=version["Kattavuus"],
        provenance=SourceProvenance(
            "Fimea Basic Register", file_name, checksum, retrieved_at=retrieved_at
        ),
        schema_location=schema_location,
        structure=tuple(sorted(structure.items())),
    )
    for tag in ("Laakevalmiste", "Laakeaine"):
        if tag in index_errors:
            raise index_errors[tag]

    snapshots = []
    package_keys = set()
    for position, (key_record, product_ref, substance_refs, rest) in enumerate(packages, start=1):
        key = key_record.get()
        if not key or key in package_keys:
            raise ValueError(f"Missing or duplicate Pakkaustunnus: {key!r}")
        package_keys.add(key)
        if product_ref not in products:
            raise ValueError(f"Unresolved product reference: {product_ref!r}")
        product, authorizations = products[product_ref].get()
        active = []
        for substance_ref in substance_refs:
            if substance_ref not in substances:
                raise ValueError(f"Unresolved substance reference: {substance_ref!r}")
            active.extend(substances[substance_ref].get())
        vnr, package_fields = rest.get()
        snapshots.append(
            MedicineSnapshot(
                pakkaustunnus=key,
                vnr_numero=vnr,
                product_reference=fields.of(product_ref, ()),
                product=product,
                active_substances=tuple(active),
                package=package_fields,
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
