# Contract: Latest-release check API (feature 005)

Base path: `/api/source-releases/latest-check`. JSON, camelCase.

## `POST /api/source-releases/latest-check`

Starts a check in the background and answers `202 Accepted` at once. If a check is already running, nothing new starts and the running check is reported.

```json
{ ...CheckStatus, "started": true }
```

## `GET /api/source-releases/latest-check`

The most recent check since the backend started (`IDLE` before the first).

### CheckStatus

```json
{
  "phase": "IDLE | DOWNLOADING | INGESTING | PREPARING_CATALOGUE | SUCCEEDED | FAILED",
  "running": false,
  "sourceUrl": "https://data.pilvi.fimea.fi/avoin-data/Perusrekisteri.xml",
  "startedAt": "2026-11-21T10:00:49.737057+00:00",
  "finishedAt": "2026-11-21T10:01:58.941601+00:00",
  "downloadedBytes": 199465476,
  "result": {
    "processingStatus": "VALIDATED",
    "chronologyStatus": "AVAILABLE",
    "capturedReleaseReference": "sha256-…",
    "failureDetail": null,
    "alreadyCaptured": false,
    "releaseDate": "2026-10-06",
    "reviewCasesCreated": 0
  },
  "error": null
}
```

- `result` holds the same fields as the `POST /api/source-releases/ingest` response, plus `releaseDate` (Ajopvm of a newly captured release; `null` when already captured) and `reviewCasesCreated`.
- `running` is `true` for `DOWNLOADING`, `INGESTING` and `PREPARING_CATALOGUE`.
- `FAILED` has a plain `error`: a download failure ("Could not reach Fimea: …", "Fimea answered HTTP …", "The download was empty.", size limit), "The release was not accepted: …" (with `result` when ingestion ran), or an unexpected error.
- The state lives in memory: a backend restart returns to `IDLE`. The captured release itself is stored as usual.
