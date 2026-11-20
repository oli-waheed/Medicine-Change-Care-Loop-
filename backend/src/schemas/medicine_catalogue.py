"""Read-view serialization for the medicine catalogue (contracts/catalogue-api.md)."""

from ..domain.medicine_snapshot import (
    ActiveSubstanceFields,
    AuthorizationRegistrationFields,
    MedicineSnapshot,
)
from ..domain.source_field import SourceField
from .open_review_cases import _field

COMPARISON_NOTICE = (
    "Source fields are compared as recorded. A difference or match does not "
    "indicate therapeutic equivalence."
)


def source_value(value: SourceField) -> dict[str, object]:
    """The shared {state, value, attributes} shape; never collapsed to a string."""

    return _field(value)


def _values(values: tuple[SourceField, ...]) -> list[dict[str, object]]:
    return [source_value(v) for v in values]


def release(baseline) -> dict[str, object]:
    capture = baseline.capture
    source_release = baseline.ingestion.source_release
    provenance = source_release.provenance if source_release else None
    return {
        "releaseId": capture.release_id,
        "sourceName": capture.source_name,
        "releaseDate": source_value(source_release.ajopvm) if source_release else None,
        "releaseReference": source_value(source_release.aineistoera) if source_release else None,
        # The provenance keeps the time zone; the database column may not.
        "retrievedAt": (
            provenance.retrieved_at.isoformat() if provenance and provenance.retrieved_at else None
        ),
        "fileName": provenance.raw_file_name if provenance else None,
        "checksum": provenance.raw_file_checksum if provenance else None,
        "chronologyEvidence": capture.source_order_evidence_class,
    }


def provenance(snapshot: MedicineSnapshot) -> dict[str, object]:
    source_release = snapshot.source_release
    meta = source_release.provenance
    return {
        "sourceName": meta.source_name,
        "releaseReference": source_value(source_release.aineistoera),
        "releaseDate": source_value(source_release.ajopvm),
        "retrievedAt": meta.retrieved_at.isoformat() if meta.retrieved_at else None,
        "fileName": meta.raw_file_name,
        "checksum": meta.raw_file_checksum,
        "recordIdentifier": snapshot.pakkaustunnus,
        "recordLocator": snapshot.source_record_locator,
        "evidenceClass": "VERIFIED",
    }


def product_summary(snapshot: MedicineSnapshot) -> dict[str, object]:
    product = snapshot.product
    return {
        "productReference": snapshot.product_reference.value,
        "name": source_value(product.kauppanimi),
        "strength": source_value(product.vahvuus),
        "pharmaceuticalForm": source_value(product.laakemuoto),
        "atcCode": source_value(product.atc_koodi),
    }


def package_summary(snapshot: MedicineSnapshot) -> dict[str, object]:
    product = snapshot.product
    return {
        "pakkaustunnus": snapshot.pakkaustunnus,
        "vnr": source_value(snapshot.vnr_numero),
        "productReference": snapshot.product_reference.value,
        "productName": source_value(product.kauppanimi),
        "strength": source_value(product.vahvuus),
        "pharmaceuticalForm": source_value(product.laakemuoto),
        "atcCode": source_value(product.atc_koodi),
        "packageSizeText": source_value(snapshot.package.pakkauskoko_teksti),
        "available": source_value(snapshot.package.availability.kaupan),
    }


def active_substance(substance: ActiveSubstanceFields) -> dict[str, object]:
    return {
        "name": source_value(substance.aine),
        "casNumber": source_value(substance.cas_numero),
        "quantity": source_value(substance.maara),
        "quantityUnit": source_value(substance.maara_yksikko),
        "undividedStrength": source_value(substance.jakamaton_vahvuus),
    }


def authorization(item: AuthorizationRegistrationFields) -> dict[str, object]:
    return {
        "branch": item.branch.value,
        "status": source_value(item.tila),
        "grantedOn": source_value(item.myontamis_paiva),
        "endsOn": source_value(item.paattymis_paiva),
    }


def catalogue_page(baseline, items, *, page: int, page_size: int) -> dict[str, object]:
    start = (page - 1) * page_size
    return {
        "release": release(baseline),
        "total": len(items),
        "page": page,
        "pageSize": page_size,
        "items": [package_summary(s) for s in items[start : start + page_size]],
    }


def product_detail(baseline, view) -> dict[str, object]:
    snapshot = view.representative
    product = snapshot.product
    substances = view.active_substances
    return {
        "release": release(baseline),
        "product": {
            **product_summary(snapshot),
            "administrationRoutes": _values(product.antoreitti),
            "activeSubstances": [active_substance(s) for s in substances or ()],
            "activeSubstancesVaryByPackage": substances is None,
            "authorizations": [authorization(a) for a in snapshot.authorizations],
        },
        "packages": [package_summary(p) for p in view.packages],
    }


def package_detail(baseline, view) -> dict[str, object]:
    snapshot = view.snapshot
    package = snapshot.package
    return {
        "release": release(baseline),
        "package": {
            "pakkaustunnus": snapshot.pakkaustunnus,
            "vnr": source_value(snapshot.vnr_numero),
            "packageSizeText": source_value(package.pakkauskoko_teksti),
            "packageSize": source_value(package.pakkauskoko),
            "packageSizeMultiplier": source_value(package.pakkauskoko_kerroin),
            "packageSizeUnit": source_value(package.pakkauskoko_yksikko),
            "publicClarification": source_value(package.julkinen_tarkenne),
            "availability": {
                "available": source_value(package.availability.kaupan),
                "availableFrom": source_value(package.availability.kauppaantulo_paiva),
                "availableUntil": source_value(package.availability.kaupasta_poistumis_paiva),
            },
            "activeSubstances": [active_substance(s) for s in snapshot.active_substances],
            "provenance": provenance(snapshot),
        },
        "product": product_summary(snapshot),
        "authorizations": [authorization(a) for a in snapshot.authorizations],
        "sameVnrPackages": list(view.same_vnr_packages),
    }


def substances_page(baseline, entries, *, page: int, page_size: int) -> dict[str, object]:
    start = (page - 1) * page_size
    return {
        "release": release(baseline),
        "total": len(entries),
        "page": page,
        "pageSize": page_size,
        "items": [
            {
                "identity": entry.identity,
                "name": source_value(entry.name),
                "casNumber": source_value(entry.cas_number),
                "occurrences": [
                    {
                        "pakkaustunnus": o.pakkaustunnus,
                        "productReference": o.product_reference,
                        "productName": source_value(o.product_name),
                        "position": o.position,
                        **{
                            key: value
                            for key, value in active_substance(o.substance).items()
                            if key in {"quantity", "quantityUnit", "undividedStrength"}
                        },
                    }
                    for o in entry.occurrences
                ],
            }
            for entry in entries[start : start + page_size]
        ],
    }


def comparison(baseline, result) -> dict[str, object]:
    return {
        "release": release(baseline),
        "productA": product_summary(result.product_a.representative),
        "productB": product_summary(result.product_b.representative),
        "fields": [
            {
                "field": f.path,
                "a": _values(f.a),
                "b": _values(f.b),
                "result": "SAME" if f.same else "DIFFERENT",
            }
            for f in result.fields
        ],
        "notice": COMPARISON_NOTICE,
    }


def source_summary(summary) -> dict[str, object]:
    return {
        "release": release(summary.baseline),
        "packageCount": summary.package_count,
        "productCount": summary.product_count,
        "activeSubstanceCount": summary.active_substance_count,
    }
