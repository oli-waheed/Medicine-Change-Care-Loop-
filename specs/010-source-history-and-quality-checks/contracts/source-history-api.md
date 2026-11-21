# Contract: Source History (feature 010)

## `GET /api/source-history`

Read-only. JSON, camelCase.

```json
{
  "basicRegister": [
    {
      "releaseId": "sha256-…",
      "releaseDate": "2026-11-21",
      "dateEvidence": "VERIFIED",
      "processingStatus": "VALIDATED",
      "failureDetail": null,
      "fileName": "Perusrekisteri.xml",
      "checksum": "c7ac7fa9…",
      "sizeBytes": 200598770,
      "evidenceAvailable": true,
      "firstRetrievedAt": "2026-11-21T10:22:24+00:00",
      "lastRetrievedAt": "2026-11-21T10:22:24+00:00",
      "retrievalCount": 1,
      "isCatalogueRelease": true
    }
  ],
  "qualityChecks": [
    {
      "checkId": "QC-…",
      "priorReleaseId": "sha256-…",
      "currentReleaseId": "sha256-…",
      "priorReleaseDate": "2026-10-06",
      "currentReleaseDate": "2026-11-21",
      "checkedAt": "…",
      "overall": "PASSED | ATTENTION",
      "counts": {
        "priorPackages": 146042, "currentPackages": 146868, "inBoth": 146021,
        "changed": 2050, "noLongerPresent": 21, "new": 847,
        "vnrGained": 160, "vnrLost": 92, "vnrChanged": 17,
        "formattingOnly": 109, "activeSubstanceOnly": 848, "unlabelled": 1093,
        "sharedVnrs": 54
      },
      "checks": [
        { "id": "RELEASE_ORDER", "label": "Release order", "status": "PASSED", "detail": "…" }
      ]
    }
  ],
  "uncheckedPairs": [{ "priorReleaseDate": "…", "currentReleaseDate": "…" }],
  "shortageFiles": [
    {
      "checksum": "sha256-…", "processingStatus": "VALIDATED", "failureDetail": null,
      "recordCount": 751, "sizeBytes": 64454, "evidenceAvailable": true,
      "firstRetrievedAt": "…", "lastRetrievedAt": "…", "retrievalCount": 3, "isActive": true
    }
  ]
}
```

Check ids: `RELEASE_ORDER`, `UNIQUE_PACKAGE_IDS`, `PACKAGE_IDS_KEPT`, `PACKAGES_REMOVED`, `PACKAGES_CHANGED` (PASSED or ATTENTION), `SOURCE_CLEANUPS`, `SHARED_VNRS` (INFO).

`GET /api/daily-updates` → `lastRun.outcome` also has `qualityChecksAdded` (number of pairs checked by that run).
