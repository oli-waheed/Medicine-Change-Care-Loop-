# Contract: Source clean-up labels (feature 008)

Added to every release case returned by `GET /api/open-review-cases` and by `POST /api/review-cases/{caseId}/status-events`. Shortage cases are unchanged.

```json
{
  "changeSet": {
    "cleanupLabel": "FORMATTING_ONLY | ACTIVE_SUBSTANCE_ONLY | null",
    "changes": [
      {
        "changeId": "…",
        "field": "Laakevalmiste/Kauppanimi",
        "before": [{ "state": "value", "value": "Fictional Product Amber Revised", "attributes": {} }],
        "after": [{ "state": "value", "value": "Fictional  product AMBER revised ", "attributes": {} }],
        "formattingOnly": true
      }
    ]
  }
}
```

Labels are worked out on every read from the stored values; they are not stored and never change the case.
