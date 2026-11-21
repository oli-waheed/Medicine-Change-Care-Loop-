# Contract: Shortages and daily-update API (feature 006)

JSON, camelCase. None of these operations reads, changes or closes review cases.

## `GET /api/shortages`

Query: `q` (product name, VNR or company; case-insensitive, contains), `valid` (exact published value, e.g. `K`), `page` (≥ 1), `pageSize` (1–200, default 50).

```json
{
  "source": {
    "sourceName": "Fimea shortage data (Shortages.txt)",
    "sourceUrl": "https://data.pilvi.fimea.fi/avoin-data/Shortages.txt",
    "captureReference": "sha256-…",
    "sizeBytes": 64454,
    "recordCount": 751,
    "firstRetrievedAt": "2026-11-21T10:41:06+00:00",
    "lastRetrievedAt": "2026-11-21T10:41:06+00:00",
    "retrievalCount": 1,
    "latestUpdated": "2026-11-20",
    "licence": "CC BY 4.0"
  },
  "catalogue": { "status": "READY | LOADING | UNAVAILABLE", "releaseId": "sha256-…", "releaseDate": "2026-10-06" },
  "validCounts": { "E": 40, "K": 711 },
  "total": 751, "page": 1, "pageSize": 50,
  "items": [{
    "line": 2,
    "vnr": "550343",
    "valid": "K",
    "unavailableFrom": "2026-11-06",
    "endingDate": "2026-12-01",
    "notificationDate": "2026-09-25",
    "updated": "2026-11-20",
    "company": "Santen Oy",
    "packages": [{ "pakkaustunnus": "87902", "productReference": "…", "productName": SourceValue,
                   "strength": SourceValue, "pharmaceuticalForm": SourceValue, "packageSizeText": SourceValue }]
  }]
}
```

- Values are the published strings (`""` when empty). `line` is the row's line in the file.
- `packages` is `null` while the catalogue is `LOADING` (it is then prepared in the background) or `UNAVAILABLE`, and `[]` when no package has the VNR. Product-name search uses the catalogue only when `READY`.
- `503 SHORTAGES_UNAVAILABLE` before the first accepted download; `503 SHORTAGES_SOURCE_UNREADABLE` when the stored file fails its checksum; `422` for invalid paging.

## `POST /api/shortages/update` and `GET /api/shortages/update`

`POST` starts a download in the background (`202`); if one runs, it reports that one (`"started": false`). `GET` reports the latest since the backend started.

```json
{
  "phase": "IDLE | RUNNING | SUCCEEDED | FAILED",
  "running": false,
  "trigger": "BUTTON | SCHEDULE",
  "startedAt": "…", "finishedAt": "…",
  "result": { "processingStatus": "VALIDATED | FAILED", "alreadyCaptured": false,
              "captureReference": "sha256-…", "recordCount": 751, "failureDetail": null,
              "downloadedBytes": 64454 },
  "error": null
}
```

`FAILED` errors: download failures as in feature 005, or "The shortage file was not accepted: …" (with `result`).

## `GET /api/daily-updates`

```json
{
  "enabled": true, "time": "06:00", "timeZone": "EET",
  "lastRun": { "date": "2026-11-21", "trigger": "SCHEDULE", "startedAt": "…", "finishedAt": "…",
               "outcome": { "shortages": UpdateStatus, "basicRegister": CheckStatus } }
}
```

`basicRegister` is the feature 005 check status (`contracts/latest-release-check-api.md` of 005).
