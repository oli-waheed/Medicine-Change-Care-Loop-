"""Feature 015: medicine change impact explorer — records linked to a package or product.

Links are built only from identifiers and values in the active Basic Register
release and Fimea's shortage file. Each group says how certain its link is:

- ``VERIFIED``: the records share an exact identifier or reference in the source
  (product reference, VNR, active-substance code, holder text exactly equal).
- ``POSSIBLE``: the records only share a name, or a value that differs in spaces
  or letter case. A person has to check them.
- ``MISSING``: the anchor lacks the identifier in the source, so no link can be made.

A link says nothing about whether one product can be used in place of another.
"""

import threading
from collections import defaultdict
from dataclasses import dataclass

from ..domain.medicine_snapshot import MedicineSnapshot
from ..domain.source_field import SourceField, SourceFieldState

ITEM_LIMIT = 50

VERIFIED = "VERIFIED"
POSSIBLE = "POSSIBLE"
MISSING = "MISSING"


def _text(field: SourceField) -> str:
    return field.value or ""


def _display(field: SourceField) -> str:
    """Text, or a code table's display value when the element text is empty."""
    return field.value or dict(field.attributes).get("value", "")


def _fold(value: str) -> str:
    return " ".join(value.split()).casefold()


def _substance_code(substance) -> str | None:
    return dict(substance.aine.attributes).get("id") or None


def _holders(snapshot: MedicineSnapshot) -> set[str]:
    return {
        authorization.haltija.value
        for authorization in snapshot.authorizations
        if authorization.haltija.state is SourceFieldState.VALUE and authorization.haltija.value
    }


@dataclass(frozen=True, slots=True)
class LinkIndex:
    """Lookups over one release; built once per release (about a second)."""

    release_id: str
    packages_by_product: dict[str, tuple[MedicineSnapshot, ...]]
    packages_by_vnr: dict[str, tuple[MedicineSnapshot, ...]]
    products_by_code: dict[str, frozenset[str]]
    products_by_substance_name: dict[str, frozenset[str]]
    products_by_holder: dict[str, frozenset[str]]
    products_by_holder_fold: dict[str, frozenset[str]]
    products_by_name: dict[str, frozenset[str]]
    codes_by_product: dict[str, frozenset[str]]


def build_link_index(release_id: str, snapshots: tuple[MedicineSnapshot, ...]) -> LinkIndex:
    by_product: dict[str, list] = defaultdict(list)
    by_vnr: dict[str, list] = defaultdict(list)
    by_code: dict[str, set] = defaultdict(set)
    by_substance_name: dict[str, set] = defaultdict(set)
    by_holder: dict[str, set] = defaultdict(set)
    by_holder_fold: dict[str, set] = defaultdict(set)
    by_name: dict[str, set] = defaultdict(set)
    codes: dict[str, set] = defaultdict(set)
    for snapshot in snapshots:
        reference = _text(snapshot.product_reference)
        by_product[reference].append(snapshot)
        if snapshot.vnr_numero.state is SourceFieldState.VALUE and snapshot.vnr_numero.value:
            by_vnr[snapshot.vnr_numero.value].append(snapshot)
        for substance in snapshot.active_substances:
            code = _substance_code(substance)
            if code:
                by_code[code].add(reference)
                codes[reference].add(code)
            else:
                name = _fold(_display(substance.aine))
                if name:
                    by_substance_name[name].add(reference)
        for holder in _holders(snapshot):
            by_holder[holder].add(reference)
            by_holder_fold[_fold(holder)].add(reference)
        name = _fold(_text(snapshot.product.kauppanimi))
        if name:
            by_name[name].add(reference)

    def freeze(table):
        return {key: frozenset(value) for key, value in table.items()}

    return LinkIndex(
        release_id=release_id,
        packages_by_product={key: tuple(value) for key, value in by_product.items()},
        packages_by_vnr={key: tuple(value) for key, value in by_vnr.items()},
        products_by_code=freeze(by_code),
        products_by_substance_name=freeze(by_substance_name),
        products_by_holder=freeze(by_holder),
        products_by_holder_fold=freeze(by_holder_fold),
        products_by_name=freeze(by_name),
        codes_by_product=freeze(codes),
    )


class LinkIndexCache:
    """Keeps the index of the active release only."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._index: LinkIndex | None = None

    def get(self, release_id: str, snapshots) -> LinkIndex:
        with self._lock:
            if self._index is None or self._index.release_id != release_id:
                self._index = build_link_index(release_id, snapshots)
            return self._index


def _source_value(field: SourceField) -> dict:
    return {"state": field.state.value, "value": field.value, "attributes": dict(field.attributes)}


def _package_item(snapshot: MedicineSnapshot) -> dict:
    return {
        "pakkaustunnus": snapshot.pakkaustunnus,
        "productReference": _text(snapshot.product_reference),
        "name": _source_value(snapshot.product.kauppanimi),
        "strength": _source_value(snapshot.product.vahvuus),
        "packageSizeText": _source_value(snapshot.package.pakkauskoko_teksti),
        "vnr": _source_value(snapshot.vnr_numero),
    }


def _product_item(index: LinkIndex, reference: str) -> dict:
    first = index.packages_by_product[reference][0]
    return {
        "productReference": reference,
        "name": _source_value(first.product.kauppanimi),
        "strength": _source_value(first.product.vahvuus),
        "form": _source_value(first.product.laakemuoto),
        "holders": sorted(_holders(first)),
        "packageCount": len(index.packages_by_product[reference]),
    }


def _sorted_products(index: LinkIndex, references) -> list[str]:
    return sorted(
        references,
        key=lambda ref: (_fold(_text(index.packages_by_product[ref][0].product.kauppanimi)), ref),
    )


def _group(group_id, label, certainty, basis, items, *, kind, total=None, note=None) -> dict:
    items = list(items)
    return {
        "id": group_id,
        "label": label,
        "certainty": certainty,
        "basis": basis,
        "itemKind": kind,
        "total": len(items) if total is None else total,
        "items": items[:ITEM_LIMIT],
        "note": note,
    }


def _products_group(index, group_id, label, certainty, basis, references) -> dict:
    ordered = _sorted_products(index, references)
    return _group(
        group_id,
        label,
        certainty,
        basis,
        (_product_item(index, ref) for ref in ordered[:ITEM_LIMIT]),
        kind="product",
        total=len(ordered),
    )


def _missing(group_id, label, basis) -> dict:
    return _group(group_id, label, MISSING, basis, (), kind="none")


def links_for(
    index: LinkIndex,
    anchors: tuple[MedicineSnapshot, ...],
    *,
    shortages: tuple | None,
) -> list[dict]:
    """Groups of records linked to one package, or to all packages of one product.

    ``shortages`` is the active shortage file's records, or None when no file is stored.
    """
    references = {_text(a.product_reference) for a in anchors}
    anchor_ids = {a.pakkaustunnus for a in anchors}
    groups = []

    # Other packages of the same product.
    same_product = [
        s
        for ref in sorted(references)
        for s in index.packages_by_product.get(ref, ())
        if s.pakkaustunnus not in anchor_ids
    ]
    groups.append(
        _group(
            "SAME_PRODUCT",
            "Other packages of the same product",
            VERIFIED,
            "Same product reference (Laakevalmiste) in this release.",
            (_package_item(s) for s in same_product),
            kind="package",
        )
    )

    # Packages sharing a VNR.
    vnrs = sorted(
        {a.vnr_numero.value for a in anchors if a.vnr_numero.state is SourceFieldState.VALUE}
    )
    if vnrs:
        same_vnr = [
            s
            for vnr in vnrs
            for s in index.packages_by_vnr.get(vnr, ())
            if s.pakkaustunnus not in anchor_ids
        ]
        groups.append(
            _group(
                "SAME_VNR",
                "Other packages with the same VNR",
                VERIFIED,
                f"Exactly the same VNR ({', '.join(vnrs)}).",
                (_package_item(s) for s in same_vnr),
                kind="package",
            )
        )
    else:
        groups.append(
            _missing(
                "SAME_VNR",
                "Other packages with the same VNR",
                "No VNR in the source for this record, so no VNR link can be made.",
            )
        )

    # Active substances: by code (verified) and by name for substances without a code.
    codes = set().union(*(index.codes_by_product.get(ref, frozenset()) for ref in references))
    nameless = {
        _fold(_display(s.aine))
        for a in anchors
        for s in a.active_substances
        if not _substance_code(s) and _fold(_display(s.aine))
    }
    if codes:
        sharing = set().union(*(index.products_by_code.get(code, frozenset()) for code in codes))
        sharing -= references
        same_set = {ref for ref in sharing if index.codes_by_product.get(ref) == frozenset(codes)}
        groups.append(
            _products_group(
                index,
                "SAME_SUBSTANCES",
                "Products with the same active substances (other strengths and forms)",
                VERIFIED,
                "Exactly the same set of active-substance codes (Aine id).",
                same_set,
            )
        )
        groups.append(
            _products_group(
                index,
                "SHARES_SUBSTANCE",
                "Products that share at least one active substance",
                VERIFIED,
                "At least one active-substance code (Aine id) in common, but not all.",
                sharing - same_set,
            )
        )
    elif not nameless:
        groups.append(
            _missing(
                "SAME_SUBSTANCES",
                "Products with the same active substances",
                "No active substance is listed for this record in the source.",
            )
        )
    if nameless:
        by_name = set().union(
            *(index.products_by_substance_name.get(name, frozenset()) for name in nameless)
        )
        groups.append(
            _products_group(
                index,
                "SUBSTANCE_BY_NAME",
                "Products with an active substance of the same name",
                POSSIBLE,
                "Some active substances have no code in the source; these share only the name.",
                by_name - references,
            )
        )

    # Authorisation or registration holder.
    holders = set().union(*(_holders(a) for a in anchors))
    if holders:
        exact = set().union(*(index.products_by_holder.get(h, frozenset()) for h in holders))
        folded = set().union(
            *(index.products_by_holder_fold.get(_fold(h), frozenset()) for h in holders)
        )
        groups.append(
            _products_group(
                index,
                "SAME_HOLDER",
                "Other products of the same holder",
                VERIFIED,
                f"Exactly the same holder text ({', '.join(sorted(holders))}).",
                exact - references,
            )
        )
        groups.append(
            _products_group(
                index,
                "SIMILAR_HOLDER",
                "Holder written differently",
                POSSIBLE,
                "The holder text differs only in spaces or letter case.",
                folded - exact - references,
            )
        )
    else:
        groups.append(
            _missing(
                "SAME_HOLDER",
                "Other products of the same holder",
                "No holder (Haltija) is recorded for this record in the source.",
            )
        )

    # Same trade name, different product records.
    names = {_fold(_text(a.product.kauppanimi)) for a in anchors if _text(a.product.kauppanimi)}
    same_name = set().union(*(index.products_by_name.get(n, frozenset()) for n in names))
    groups.append(
        _products_group(
            index,
            "SAME_NAME",
            "Other product records with the same trade name",
            POSSIBLE,
            "Only the trade name matches (ignoring spaces and letter case).",
            same_name - references,
        )
    )

    # Fimea's shortage file, by VNR.
    if not vnrs:
        groups.append(
            _missing(
                "SHORTAGES",
                "Shortages reported to Fimea",
                "No VNR in the source, so Fimea's shortage file cannot be linked.",
            )
        )
    elif shortages is None:
        groups.append(
            _missing(
                "SHORTAGES",
                "Shortages reported to Fimea",
                "No shortage file has been downloaded yet.",
            )
        )
    else:
        rows = [record for record in shortages if record.vnr in vnrs]
        groups.append(
            _group(
                "SHORTAGES",
                "Shortages reported to Fimea",
                VERIFIED,
                f"Rows of the shortage file with the same VNR ({', '.join(vnrs)}), as published.",
                (
                    {
                        "line": record.line,
                        "vnr": record.vnr,
                        "valid": record.valid,
                        "unavailableFrom": record.unavailable_from,
                        "endingDate": record.ending_date,
                        "updated": record.updated,
                        "company": record.company,
                    }
                    for record in rows
                ),
                kind="shortage",
                note=(
                    None
                    if rows
                    else "Not listed in the shortage file. This does not show that it is available."
                ),
            )
        )
    return groups
