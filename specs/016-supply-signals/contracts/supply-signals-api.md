# Contract: Supply signals (feature 016)

## `GET /api/medicine-catalogue/packages/{pakkaustunnus}/supply-signals`
## `GET /api/medicine-catalogue/products/{product_reference}/supply-signals`

Read-only. 404 `PACKAGE_NOT_FOUND` / `PRODUCT_NOT_FOUND`; 503 as other catalogue endpoints.

```json
{
  "releaseId": "sha256-…",
  "anchorPackages": ["87902"],
  "asOf": "2026-11-21",
  "notice": "Facts from Fimea's files as published, side by side. …",
  "vnrs": ["550343"],
  "status": "LISTED | NOT_LISTED | NO_VNR | NO_FILE",
  "shortageFile": { "captureReference": "sha256-…", "lastRetrievedAt": "…" },
  "current": [
    { "line": 2, "vnr": "550343", "valid": "K", "unavailableFrom": "2026-11-06",
      "endingDate": "2026-12-01", "notificationDate": "2026-09-25", "updated": "2026-11-20",
      "company": "Santen Oy", "daysSinceUnavailableFrom": 15, "daysUntilEstimatedEnd": 10 }
  ],
  "listings": [
    { "vnr": "550343", "firstSeen": "…", "lastSeen": "…", "downloads": 1, "listedNow": true,
      "unavailableFromFirst": "2026-11-06", "endingDateLast": "2026-12-01", "listedDays": 0 }
  ],
  "downloadsChecked": 1,
  "unreadableDownloads": 0,
  "register": [
    { "pakkaustunnus": "87902", "vnr": {}, "onMarket": {}, "marketedFrom": {}, "marketedUntil": {},
      "authorisations": [{ "branch": "Myyntilupa", "status": {}, "endDate": {} }] }
  ],
  "registerChanges": [
    { "pakkaustunnus": "…", "priorReleaseDate": "…", "currentReleaseDate": "…",
      "kind": "FIELDS_CHANGED | NO_LONGER_PRESENT | NEWLY_PRESENT",
      "field": "Pakkaus/Kaupanolo/Kaupan", "before": [], "after": [] }
  ],
  "related": { "sameSubstanceProducts": 13, "listedNow": 0, "available": true, "items": [] }
}
```

Day counts are whole days between the published date and `asOf`: positive `daysSinceUnavailableFrom` is in the past, positive `daysUntilEstimatedEnd` in the future. Source values (`{}` above) have `state`, `value` and `attributes`.
