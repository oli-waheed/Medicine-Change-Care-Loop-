# Ingestion and Case View Contracts

These are logical data contracts for the prototype's boundaries, not a prescribed transport or framework.
The team must choose the actual transport, serialization schema, and authentication approach before
implementation. Any patient and medication records in payloads must be simulated.

## Source release ingestion

The scheduled n8n workflow provides one complete captured release to the ingestion boundary.
Raw files remain immutable and are linked by file name and checksum.

Required logical fields:

| Field | Requirement |
|---|---|
| `sourceName` | Identifies Fimea Basic Register |
| `sourceReleaseReference` | Source-provided release identifier/date when available; otherwise explicitly unknown |
| `sourceOrder` | Source-evidenced ordering value when available; never substitute local retrieval time |
| `retrievedAt` | Local retrieval timestamp |
| `files[]` | One or more raw files with name, checksum, and retrievable content/reference |
| `captureStatus` | Complete or failed; partial acquisition cannot be submitted as complete |

Illustrative payload:

```json
{
  "sourceName": "Fimea Basic Register",
  "sourceReleaseReference": {
    "value": "source-provided release reference",
    "evidenceClass": "VERIFIED"
  },
  "sourceOrder": {
    "value": "source-evidenced order",
    "evidenceClass": "VERIFIED"
  },
  "retrievedAt": "2026-10-06T00:00:00Z",
  "files": [
    {
      "name": "source-file-name",
      "checksum": "content-checksum",
      "contentReference": "immutable-captured-content"
    }
  ],
  "captureStatus": "COMPLETE"
}
```

Values above illustrate the shape only; they are not Fimea field names or asserted live-release values.
If the source does not provide an order value that can be verified, the release must not be labeled
verified chronological evidence.

## Normalized record and change

Each normalized source record includes a source release reference, raw source-record locator, stable
medicine/package identifiers at their actual granularity, and selected fields with source references.
The change comparison output references prior/current snapshot records and retains before/after values.
Only fields in the team-approved relevant-field set may produce a case-triggering change.

## Deterministic match result

Each change-to-record match result identifies:

- the detected change;
- the simulated medication record reference;
- the identifier and granularity compared;
- the result: `MATCHED`, `NO_MATCH`, or `AMBIGUOUS`;
- evidence classification and source references.

Only a unique `MATCHED` result may create a case. `NO_MATCH` and `AMBIGUOUS` never create a case.

## Pharmacist open-case view

The read view returns open cases (initially `NEW`) with:

- case identity, creation time, and status;
- medicine identifier and identifier granularity;
- matched simulated-record reference and fictional display information;
- detected field and before/after values;
- source release references, raw file/record locators, and retrieval/source-order information;
- evidence classifications, including unknown or conflicting values when relevant.

The view is read-only for this feature. It exposes no diagnosis, treatment recommendation, substitution,
clinical urgency, patient-facing communication, or automatic case closure operation.

## Safety and error behavior

- Incomplete source acquisition returns a failed/incomplete outcome, not a successful snapshot.
- Unknown source order remains unknown; no verified release-to-release change is asserted.
- Malformed or conflicting identifiers cannot be silently normalized into a match.
- Repeated submission of identical release evidence is idempotent.
- A unique change and simulated record pair creates at most one `NEW` case.
- All displayed medication/person data is fictional; no real patient identifiers are valid contract data.
