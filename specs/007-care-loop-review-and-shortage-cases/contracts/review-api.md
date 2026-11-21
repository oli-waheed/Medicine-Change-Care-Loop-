# Contract: Review steps and shortage review cases (feature 007)

JSON, camelCase.

## `GET /api/open-review-cases`

Query: `includeReviewed=true` to include reviewed cases (default: only `NEW` and `IN_PROGRESS`). Each case is the stored view plus:

```json
{
  "caseType": "RELEASE | SHORTAGE",
  "status": "NEW | IN_PROGRESS | REVIEWED_NO_ACTION | REVIEWED_FOLLOW_UP",
  "statusHistory": [
    { "eventId": "EVENT-…", "fromStatus": null, "toStatus": "NEW",
      "occurredAt": "2099-01-06T04:00:00+00:00", "reviewerInitials": null, "note": null },
    { "eventId": "EVENT-…", "fromStatus": "NEW", "toStatus": "IN_PROGRESS",
      "occurredAt": "…", "reviewerInitials": "OW", "note": null }
  ]
}
```

Cases stored before feature 007 have no `caseType`; the API reports them as `RELEASE`.

## `POST /api/review-cases/{caseId}/status-events`

```json
{ "expectedStatus": "NEW", "toStatus": "IN_PROGRESS", "reviewerInitials": "OW", "note": null }
```

| Answer | When |
|---|---|
| `201` with the updated case (as in the list) | Step recorded |
| `409 TRANSITION_NOT_ALLOWED` | Not one of: NEW → IN_PROGRESS, NEW or IN_PROGRESS → either Reviewed outcome, Reviewed → IN_PROGRESS |
| `409 STALE_STATUS` (with `currentStatus`) | The case no longer has `expectedStatus` |
| `404 CASE_NOT_FOUND` | Unknown case |
| `422 INVALID_REVIEW_STEP` | Initials not 1–10 letters; note missing for a Reviewed outcome or reopening; note over 1,000 characters |
| `422` | Unknown status value |

Nothing else changes a status: ingestion, comparisons, shortage updates and the daily update only create NEW cases.

## Shortage case (`caseType: "SHORTAGE"`)

```json
{
  "caseId": "CASE-…", "caseType": "SHORTAGE", "status": "NEW", "createdAt": "…",
  "medicineIdentifier": "SIM-PKG-500", "identifierGranularity": "package",
  "matchedRecord": { "recordId": "…", "personReference": "…", "medicineDisplay": "…" },
  "shortageChange": {
    "changeSetId": "…", "kind": "SHORTAGE_STARTED | SHORTAGE_CHANGED | SHORTAGE_ENDED",
    "vnr": "SIM-VNR-500", "changedColumns": ["Valid"],
    "before": ShortageRow | null, "after": ShortageRow | null,
    "detectedAt": "…",
    "package": { "pakkaustunnus": "…", "productName": SourceValue, "strength": SourceValue, "packageSizeText": SourceValue },
    "catalogue": { "releaseId": "sha256-…", "releaseDate": "2099-01-02" },
    "notice": "Dates and status are the company's report to Fimea, shown as published; the end date is an estimate."
  },
  "sources": {
    "prior":   { "sourceName": "Fimea shortage data (Shortages.txt)", "sourceUrl": "…", "fileName": "Shortages.txt",
                 "checksum": "<hex>", "captureReference": "sha256-<hex>", "retrievedAt": "…",
                 "lineNumber": 4, "licence": "CC BY 4.0", "evidenceClass": "VERIFIED", "note": "…",
                 "evidenceAvailable": true },
    "current": { … }
  },
  "evidenceClass": "VERIFIED", "evidenceAvailability": "AVAILABLE | UNAVAILABLE",
  "initialStatusEvent": { … }
}
```

`ShortageRow` is `{ "line", "valid", "unavailableFrom", "endingDate", "notificationDate", "updated", "company" }` as published. `SHORTAGE_CHANGED` compares Valid, UnavailableFrom, EndingDate and Company.

## Shortage outcomes in `GET /api/change-processing-outcomes`

Every shortage change gets one outcome per catalogue package with its VNR (or one for the VNR when there is none), marked `"source": "SHORTAGES"`, with `result` and `reason`: `MATCHED`/`UNIQUE_EXACT_PACKAGE_MATCH`, `AMBIGUOUS`/`MULTIPLE_SIMULATED_RECORDS`, `NO_MATCH`/`NO_SIMULATED_RECORD`, `NO_MATCH`/`NO_CATALOGUE_PACKAGE`, `NO_MATCH`/`NO_CATALOGUE_RELEASE`.

## Shortage update result

`POST`/`GET /api/shortages/update` results include `review: { comparedWith, changes, outcomes, reviewCasesCreated }` when the active shortage file changed.
