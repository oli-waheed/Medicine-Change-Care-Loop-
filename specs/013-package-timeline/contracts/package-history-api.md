# Contract: Package history (feature 013)

## `GET /api/medicine-catalogue/packages/{pakkaustunnus}/history`

Read-only; does not need the catalogue release in memory. Unknown packages return an empty `events` list.

```json
{
  "pakkaustunnus": "200509",
  "comparedPairs": [{ "priorReleaseDate": "2026-10-06", "currentReleaseDate": "2026-11-21" }],
  "events": [
    {
      "priorReleaseDate": "2026-10-06",
      "currentReleaseDate": "2026-11-21",
      "kind": "FIELDS_CHANGED | NO_LONGER_PRESENT | NEWLY_PRESENT",
      "cleanupLabel": "FORMATTING_ONLY | ACTIVE_SUBSTANCE_ONLY | null",
      "changes": [
        {
          "field": "Laakevalmiste/Kauppanimi",
          "before": [{ "state": "value", "value": "Ibuprofen Stada", "attributes": {} }],
          "after": [{ "state": "value", "value": "Ibuprofen STADA", "attributes": {} }],
          "formattingOnly": true
        }
      ]
    }
  ]
}
```

`comparedPairs` and `events` are newest first. `GET /api/daily-updates` → `lastRun.outcome.packageHistoriesAdded`.
