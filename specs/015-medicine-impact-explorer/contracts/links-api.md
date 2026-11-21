# Contract: Linked records (feature 015)

## `GET /api/medicine-catalogue/packages/{pakkaustunnus}/links`
## `GET /api/medicine-catalogue/products/{product_reference}/links`

Read-only. 404 `PACKAGE_NOT_FOUND` / `PRODUCT_NOT_FOUND`; 503 as other catalogue endpoints.

```json
{
  "releaseId": "sha256-…",
  "anchorPackages": ["148768"],
  "shortageSource": { "captureReference": "sha256-…", "lastRetrievedAt": "…" },
  "notice": "Links show shared identifiers and values in Fimea's source only. They say nothing about whether one product can be used in place of another.",
  "groups": [
    {
      "id": "SAME_SUBSTANCES",
      "label": "Products with the same active substances (other strengths and forms)",
      "certainty": "VERIFIED | POSSIBLE | MISSING",
      "basis": "Exactly the same set of active-substance codes (Aine id).",
      "itemKind": "package | product | shortage | none",
      "total": 104,
      "items": [],
      "note": null
    }
  ]
}
```

Group ids: `SAME_PRODUCT`, `SAME_VNR`, `SAME_SUBSTANCES`, `SHARES_SUBSTANCE`, `SUBSTANCE_BY_NAME`, `SAME_HOLDER`, `SIMILAR_HOLDER`, `SAME_NAME`, `SHORTAGES`. At most 50 items per group; `total` counts all.

Package item: `pakkaustunnus`, `productReference`, `name`, `strength`, `packageSizeText`, `vnr` (source values). Product item: `productReference`, `name`, `strength`, `form`, `holders`, `packageCount`. Shortage item: `line`, `vnr`, `valid`, `unavailableFrom`, `endingDate`, `updated`, `company`, as published.
