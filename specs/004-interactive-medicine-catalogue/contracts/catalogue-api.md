# Feature 004: Medicine Catalogue API Contract (T006)

Status: implemented (T019–T026) and covered by `tests/integration/medicine-catalogue/test_medicine_catalogue_api.py`; this page describes what the API returns. All endpoints are read-only `GET` requests under `/api/medicine-catalogue`, follow the conventions in `research.md` (T001), and serve only the active baseline (T002).

## Common shapes

### SourceValue

The same shape the open-review-cases API uses. It is never collapsed to a plain string, so missing, empty and present values stay distinguishable.

```json
{ "state": "value", "value": "Fictional Product Amber Revised", "attributes": {} }
{ "state": "empty", "value": null, "attributes": {} }
{ "state": "missing", "value": null, "attributes": {} }
{ "state": "value", "value": "", "attributes": { "listname": "SIM-SUBSTANCE", "id": "SIM-SA01", "value": "fictional substance amber" } }
```

A list of SourceValues (`SourceValue[]`) is used for repeated source elements. An empty list means **no occurrences**.

### Release

Included in every successful response. Product references are valid only within this release (T003).

```json
{
  "releaseId": "sha256-96006afc…",
  "sourceName": "Fimea Basic Register",
  "releaseDate": { "state": "value", "value": "2099-01-02", "attributes": {} },
  "releaseReference": { "state": "value", "value": "SIM-2099-002", "attributes": {} },
  "retrievedAt": "2099-01-04T00:00:00+00:00",
  "fileName": "current-release.xml",
  "checksum": "1304602…",
  "chronologyEvidence": "VERIFIED"
}
```

### Provenance (per package, FR-008)

```json
{
  "sourceName": "Fimea Basic Register",
  "releaseReference": { "state": "value", "value": "SIM-2099-002", "attributes": {} },
  "releaseDate": { "state": "value", "value": "2099-01-02", "attributes": {} },
  "retrievedAt": "2099-01-04T00:00:00+00:00",
  "fileName": "current-release.xml",
  "checksum": "1304602…",
  "recordIdentifier": "SIM-PKG-100",
  "recordLocator": "/Perusrekisteri/Pakkaus[1]",
  "evidenceClass": "VERIFIED"
}
```

Field references are the `project_snapshot_fields()` paths (for example `Laakevalmiste/Kauppanimi`), used as `field` in the comparison.

### PackageSummary

```json
{
  "pakkaustunnus": "SIM-PKG-100",
  "vnr": { "state": "value", "value": "SIM-VNR-100", "attributes": {} },
  "productReference": "SYN-PROD-100",
  "productName": { "state": "value", "value": "Fictional Product Amber Revised", "attributes": {} },
  "strength": { "state": "value", "value": "…", "attributes": {} },
  "pharmaceuticalForm": { "state": "value", "value": "…", "attributes": {} },
  "atcCode": { "state": "value", "value": "…", "attributes": {} },
  "packageSizeText": { "state": "value", "value": "synthetic pack size A", "attributes": {} },
  "available": { "state": "value", "value": "1", "attributes": {} }
}
```

### ProductSummary

```json
{
  "productReference": "SYN-PROD-100",
  "name": SourceValue, "strength": SourceValue,
  "pharmaceuticalForm": SourceValue, "atcCode": SourceValue
}
```

### ActiveSubstance

```json
{
  "name": SourceValue, "casNumber": SourceValue, "quantity": SourceValue,
  "quantityUnit": SourceValue, "undividedStrength": SourceValue
}
```

## Errors and the unavailable state (FR-009)

| Situation | Status | Body |
|---|---|---|
| No validated release with verified chronology | `503` | `{"detail": {"code": "CATALOGUE_UNAVAILABLE", "message": "No validated source release with verified chronology is available."}}` |
| Baseline capture cannot be reconstructed (for example, a checksum mismatch) | `503` | `{"detail": {"code": "CATALOGUE_SOURCE_UNREADABLE", "message": "<reason>"}}` |
| Product or package not in the active release | `404` | `{"detail": {"code": "PRODUCT_NOT_FOUND" \| "PACKAGE_NOT_FOUND", "releaseId": "…"}}` |
| Invalid parameter | `422` | `{"detail": "<readable message>"}` |

The API never falls back to an older or unverified release.

## Endpoints

### `GET /api/medicine-catalogue` — search and filter (FR-002, FR-003, FR-011)

| Parameter | Meaning |
|---|---|
| `q` | Case-insensitive partial match on product name, `pakkaustunnus` or VNR. Only `value` states match (T009 behaviour). |
| `activeSubstance` | Case-insensitive exact match on the substance code-table `id`, its display `value`, or its text. Any package-level occurrence matches. |
| `atc` | ATC code prefix, case-insensitive. |
| `form` | Case-insensitive exact match on the pharmaceutical-form code `id`, display `value` or text. |
| `route` | As `form`, for any administration-route occurrence. |
| `available` | `1` or `0` (the source value of `Kaupan`); any other value is `422`. |
| `vnr` | Exact VNR value (FR-013 grouping uses the same rule). |
| `missing` | Comma-separated fields that must be `missing` or have no occurrences: `vnr`, `atc`, `form`, `route`, `available`. A present-but-empty element counts as present. Unknown names are `422`. Keeps "unknown" separate from known values (FR-003). |
| `page`, `pageSize` | Default `1` and `50`; `pageSize` at most `200`. |

Filters combine with AND. Results keep source order.

```json
{ "release": { … }, "total": 4, "page": 1, "pageSize": 50, "items": [PackageSummary, …] }
```

### `GET /api/medicine-catalogue/products/{productReference}` — product details (FR-004)

```json
{
  "release": { … },
  "product": {
    "productReference": "SYN-PROD-100",
    "name": SourceValue, "strength": SourceValue, "pharmaceuticalForm": SourceValue,
    "atcCode": SourceValue, "administrationRoutes": [SourceValue],
    "activeSubstances": [ActiveSubstance],
    "activeSubstancesVaryByPackage": false,
    "authorizations": [{ "branch": "Myyntilupa", "status": SourceValue, "grantedOn": SourceValue, "endsOn": SourceValue }]
  },
  "packages": [PackageSummary]
}
```

VNR is shown per package, in `packages[].vnr` (VNR is package-level, T003). Active substances are recorded per package (`Pakkaus_Laakeaine`); `activeSubstances` is the list shared by every package of the product, and when the packages differ it is empty and `activeSubstancesVaryByPackage` is `true`.

### `GET /api/medicine-catalogue/packages/{pakkaustunnus}` — package details (FR-005, FR-012, FR-013)

```json
{
  "release": { … },
  "package": {
    "pakkaustunnus": "SIM-PKG-100",
    "vnr": SourceValue,
    "packageSizeText": SourceValue, "packageSize": SourceValue,
    "packageSizeMultiplier": SourceValue, "packageSizeUnit": SourceValue,
    "publicClarification": SourceValue,
    "availability": { "available": SourceValue, "availableFrom": SourceValue, "availableUntil": SourceValue },
    "activeSubstances": [ActiveSubstance],
    "provenance": Provenance
  },
  "product": ProductSummary,
  "authorizations": [ … as in product details … ],
  "sameVnrPackages": ["SIM-PKG-…"]
}
```

`sameVnrPackages` lists other packages whose VNR `state` is `value` and whose value is equal. It is an empty list when this package's VNR is missing or empty. Packages are never merged.

### `GET /api/medicine-catalogue/active-substances` — substance explorer (FR-006)

Parameters: `q` (partial match on substance text or code display value), `page`, `pageSize`.

```json
{
  "release": { … },
  "total": 3, "page": 1, "pageSize": 50,
  "items": [{
    "identity": "Aine=SIM-SA01",
    "name": SourceValue,
    "casNumber": SourceValue,
    "occurrences": [{
      "pakkaustunnus": "SIM-PKG-100",
      "productReference": "SYN-PROD-100",
      "productName": SourceValue,
      "position": 1,
      "quantity": SourceValue, "quantityUnit": SourceValue, "undividedStrength": SourceValue
    }]
  }]
}
```

`identity` is the existing substance identity of change detection (`Aine=<code id>`, else the text, else the CAS number), the same key used in comparison field paths. `occurrences` keep source order and repeated occurrences (FR-006).

### `GET /api/medicine-catalogue/compare?productA=…&productB=…` — comparison (FR-007)

```json
{
  "release": { … },
  "productA": ProductSummary,
  "productB": ProductSummary,
  "fields": [
    { "field": "Laakevalmiste/Kauppanimi", "a": [SourceValue], "b": [SourceValue], "result": "DIFFERENT" },
    { "field": "Laakevalmiste/ATC-koodi",  "a": [SourceValue], "b": [SourceValue], "result": "SAME" }
  ],
  "notice": "Source fields are compared as recorded. A difference or match does not indicate therapeutic equivalence."
}
```

- `result` is `SAME` or `DIFFERENT`, comparing the full SourceValue lists including `state` and `attributes`. A missing value is never treated as equal to an empty one.
- Comparison covers the `project_snapshot_fields()` paths under `Laakevalmiste/` and `Laakeaine/` of each product's first package in source order, and does not change the T005 change-detection code. A field present on one side only is compared with no occurrences.
- `422` if either parameter is absent or both are equal; `404` (`PRODUCT_NOT_FOUND`) if either product is not in the active release.

### `GET /api/medicine-catalogue/source` — active release and provenance (FR-008)

```json
{ "release": { … }, "packageCount": 4, "productCount": 3, "activeSubstanceCount": 3 }
```

## Frontend use

- **Unavailable:** a `503` with `CATALOGUE_UNAVAILABLE` shows a clear message (FR-009); `CATALOGUE_SOURCE_UNREADABLE` shows an error state.
- **Source values:** render with the existing evidence components, so missing, empty and no-occurrences look the same as in the review workspace.
- **Wording:** no response text contains clinical wording. The comparison `notice` stays factual.
