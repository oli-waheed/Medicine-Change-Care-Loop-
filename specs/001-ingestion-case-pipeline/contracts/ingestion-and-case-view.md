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

## Evidence and provenance

Each evidence item is linked to its `SourceRelease`, which supplies the source name, source release
identifier/date when present, and captured-file provenance. Record/package identifier is required;
record locator and source field/path are supplied when applicable. Preserve the original source value
and its missing, empty, or populated state separately from its evidence classification and optional
note.

Use only these classifications:

| Classification | Meaning |
|---|---|
| `VERIFIED` | Directly supported by the referenced source evidence with traceable provenance; not a clinical conclusion |
| `INFERRED` | Derived rather than directly stated; identify the basis in a note or linked evidence |
| `UNKNOWN` | Not established from available evidence; do not guess or silently substitute another value |
| `CONFLICTING` | Relevant evidence disagrees and remains unresolved; retain the competing references/values |

An evidence note explains provenance or uncertainty only. Neither source values nor evidence
classifications establish clinical significance, diagnosis, treatment, substitution, or urgency.

## Normalized record and change

Each normalized package snapshot includes a source release reference, raw source-record locator,
`Pakkaustunnus` as the team-selected primary package comparison key, optional `VNR-numero` as
supporting metadata only, and the package-to-product relation resolved from
`Pakkaus/@Laakevalmiste-ref` to `Laakevalmiste/@id` within that source document. Do not use
`Laakevalmiste/@id` as the cross-release package key. `Pakkaustunnus` was unique in the inspected
local XML only; stability or uniqueness across separate releases is not verified.

For each package paired by the same unambiguous `Pakkaustunnus`, compare only these source paths:

- Product: `Kauppanimi`, `Vahvuus`, `Laakemuoto`, `ATC-koodi`, `Antoreitti`, resolved through the
  package's product reference.
- Active substance: `VaikuttavaAine/Aine`, `CASnumero`, `Maara`, `Maarayksikko`,
  `JakamatonVahvuus`, for linked substance records reached through `Pakkaus_Laakeaine` references.
- Package: `Pakkauskokoteksti`, `Pakkauskoko`, `Pakkauskokokerroin`, `Pakkauskokoyksikko`,
  `JulkinenTarkenne`.
- Package status: `Kaupanolo/Kaupan`, `Kaupanolo/Kauppaantulopaiva`,
  `Kaupanolo/Kaupastapoistumispaiva`.
- Present authorization/registration branch: `Tila`, `Myontamispaiva`, and `Paattymispaiva` under
  `Myyntilupa`, `Erityislupa`, or `Rekisterointi`.

Preserve original source values, source paths, repeated-element occurrences, and code-table attributes.
Represent an absent element differently from a present-but-empty element. A detected difference means
one or more selected source values or their presence changed; it does not mean the change is clinically
significant. Do not compare identifiers, references, retrieval metadata, or `Substituutioryhma` as
case-triggering fields. If key pairing or source ordering is missing/ambiguous, do not fall back to VNR,
product attributes, or retrieval time to assert a verified change.

## Deterministic match result

Each change-to-record match result identifies:

- the detected change;
- the simulated medication record reference;
- the identifier and granularity compared;
- the result: `MATCHED`, `NO_MATCH`, or `AMBIGUOUS`;
- evidence classification and source references.

Only a unique `MATCHED` result may create a case. `NO_MATCH` and `AMBIGUOUS` never create a case.
For package-level matching, the compared identifier is the exact simulated `Pakkaustunnus`; `VNR-numero`
is supporting metadata only, not a match key. This key decision does not assert that
`Pakkaustunnus` is stable across Fimea releases. A source-field change or match never makes a clinical
or substitution decision; human review remains required.

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
