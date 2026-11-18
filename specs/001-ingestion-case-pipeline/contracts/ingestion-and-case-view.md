# Ingestion and Case View Contracts

These are the data contracts for the prototype's boundaries. As implemented, the backend is a FastAPI
HTTP service with JSON responses, run locally without authentication (production deployment is out of
scope). Any patient and medication records in payloads must be simulated.

## Source release ingestion

The scheduled n8n workflow uploads one complete downloaded release file to
`POST /api/source-releases/ingest` as `multipart/form-data`. Raw files remain immutable and are linked
by file name and checksum.

| Form field | Requirement |
|---|---|
| `file` | The raw XML file. Larger than `MAX_SOURCE_RELEASE_UPLOAD_BYTES` (default 250 MiB) is rejected with HTTP 413 |
| `sourceName` | Must be `Fimea Basic Register` |
| `sourceReleaseReference` | JSON `{"value": …, "evidenceClass": …}`: source-provided release identifier/date when available; otherwise `null` with `UNKNOWN` |
| `retrievedAt` | Local retrieval timestamp, ISO 8601 with a time zone |
| `sourceOrder` | Optional JSON `{"value": …, "evidenceClass": …}`. Recorded in the capture manifest for traceability only; chronology is derived by the backend from the XML's `Ajopvm` and never from this field or from retrieval time |

Invalid JSON metadata, an unsupported source name, an invalid evidence class, or a timestamp without a
time zone is rejected with HTTP 422. A failed download never reaches the backend; n8n records it in its
"Record Download Failure" branch.

Response:

```json
{
  "processingStatus": "VALIDATED",
  "chronologyStatus": "AVAILABLE",
  "capturedReleaseReference": "sha256-…",
  "failureDetail": null,
  "alreadyCaptured": false
}
```

- `processingStatus` is `VALIDATED` or `FAILED`. Malformed XML, more than one or no `Versiotiedot`,
  `Kattavuus` other than `1`, unresolved references, or a duplicate `Pakkaustunnus` fail the whole release,
  with the reason in `failureDetail`; no partial snapshot is used.
- `chronologyStatus` is `AVAILABLE` only when every file has a valid ISO `Ajopvm`. Otherwise it is
  `UNAVAILABLE` and the release is stored but never compared.
- `capturedReleaseReference` identifies the immutable capture.
- `alreadyCaptured` is `true` when the uploaded content (by SHA-256 checksum, regardless of file name or
  metadata) is already captured for this source. The existing capture is reused and its reference and
  results are returned; the raw file is not stored again, nothing is compared again, and the new
  retrieval time is recorded as an additional retrieval of that capture. Metadata is still validated.

Internally, the ingestion service accepts a release of one or more files with the same metadata plus
`files[]` (`name`, `checksum`, `contentReference`, optional `recordLocators`) and
`captureStatus` (`COMPLETE` or `FAILED`). The HTTP endpoint always submits one file as `COMPLETE`.
Values above illustrate the shape only; they are not asserted live-release values. If the source does
not provide an order value that can be verified, the release is not labeled verified chronological
evidence.

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

Matching runs on package change sets (all field changes for one package between one ordered release pair, or `NO_LONGER_PRESENT` when the package is absent from the current full-coverage release). Each match result identifies:

- the package change set;
- the simulated medication record reference;
- the identifier and granularity compared;
- the result: `MATCHED`, `NO_MATCH`, or `AMBIGUOUS`;
- evidence classification and source references.

Only a unique `MATCHED` result may create a case. `NO_MATCH` and `AMBIGUOUS` never create a case.

For package-level matching, the compared identifier is the exact simulated `Pakkaustunnus`; `VNR-numero`
is supporting metadata only, not a match key. This key decision does not assert that
`Pakkaustunnus` is stable across Fimea releases. A source-field change or match never makes a clinical
or substitution decision; human review remains required.

### Change processing outcomes view (T031)

Every match result is stored once per package change set and is readable through
`GET /api/change-processing-outcomes`. The optional, repeatable `result` query parameter filters by
`MATCHED`, `NO_MATCH`, or `AMBIGUOUS` (for example `?result=NO_MATCH&result=AMBIGUOUS`); any other
value is rejected with HTTP 422. Each outcome contains:

- `outcomeId` (equal to `changeSetId`), `result`, `reason` (`UNIQUE_EXACT_PACKAGE_MATCH`,
  `NO_SIMULATED_RECORD`, or `MULTIPLE_SIMULATED_RECORDS`), and a non-clinical `note`;
- `medicineIdentifier`, `comparedIdentifier`, and `identifierGranularity` (`package`);
- `changeSetId`, `changeKind`, and `changedFields`;
- `simulatedRecords`: every simulated record with the compared identifier (none for `NO_MATCH`, two or
  more for `AMBIGUOUS`);
- `caseIds`: the review case created for a `MATCHED` outcome, and always empty for `NO_MATCH` and
  `AMBIGUOUS`;
- `evidenceClass`, prior/current `sources` (same shape as in the case view), `sourceOrder`, and
  `detectedAt`.

The view is read-only. It does not create, change, or close cases. A duplicated `Pakkaustunnus`
inside a release is not a match outcome: the release fails validation and the ingestion response
reports `FAILED` with the reason.

## Pharmacist open-case view

`GET /api/open-review-cases` returns open cases (`NEW`), each with:

- `caseId`, `createdAt`, `status`, and `initialStatusEvent`;
- `medicineIdentifier` (`Pakkaustunnus`) and `identifierGranularity` (`package`);
- `matchedRecord`: the simulated `recordId`, `personReference`, and fictional `medicineDisplay`;
- `changeSet`: `changeSetId`, `kind` (`FIELDS_CHANGED` or `NO_LONGER_PRESENT`), `detectedAt`,
  `changes[]` (each with `changeId`, `field`, and `before`/`after` source values), and `lastKnownFields`
  (the package's prior-release values, only for `NO_LONGER_PRESENT`);
- `sources.prior` and `sources.current`: source name, release date (`Ajopvm`) and reference
  (`Aineistoera`), raw file name, checksum, record locator (none when the package is no longer present),
  retrieval time, evidence classification, note, and `evidenceAvailable` (whether a raw capture file with
  that checksum is still stored, checked when the view is read);
- `evidenceAvailability`: `AVAILABLE`, or `UNAVAILABLE` when either source's raw file is no longer
  stored. The recorded values are still returned, but the view states that they can no longer be checked
  against the source and does not present the case as fully verified;
- `sourceOrder` (prior/current keys, basis, classification) and `evidenceClass`.

Every source value keeps its `state` (`missing`, `empty`, or `value`), text, and code-table attributes.
The view is read-only for this feature. It exposes no diagnosis, treatment recommendation, substitution,
clinical urgency, patient-facing communication, or automatic case closure operation.

## Safety and error behavior

- Incomplete source acquisition returns a failed/incomplete outcome, not a successful snapshot.
- Unknown source order remains unknown. File and snapshot validation may succeed, but chronology
  eligibility is reported separately as unavailable; no verified release-to-release change is asserted.
- Malformed or conflicting identifiers cannot be silently normalized into a match.
- Repeated submission of identical release evidence is idempotent.
- A unique package change set and simulated record pair creates at most one `NEW` case.
- All displayed medication/person data is fictional; no real patient identifiers are valid contract data.

## Clinical scope verification (T035)

Verified on 2026-11-18 against `frontend/src/pages/open-review-cases`, `backend/src/workflows/ingestion_to_review.py`,
the API and the n8n workflow:

- The API has no operation that changes, closes, or deletes a case: only `GET /health`,
  `GET /api/open-review-cases`, `GET /api/change-processing-outcomes`, and `POST /api/source-releases/ingest`.
- `NEW` is the only case status. Cases and their creation event are only inserted; a later release that
  changes the same package again opens a new case and leaves the earlier one unchanged.
- No stored case or outcome field or text expresses diagnosis, treatment or dosing advice, substitution,
  urgency, priority, severity, or risk. `Substituutioryhma` is never read or compared.
- The view's only buttons select which case to show; it has no form controls, reads cases once with
  `GET`, and states that it does not make a clinical decision.
- The n8n workflow only downloads the Fimea file and uploads it to the ingestion endpoint.

These rules are enforced by `tests/contract/clinical-scope/test_clinical_scope_guard.py` and
`frontend/src/pages/open-review-cases/OpenReviewCasesPage.scope.test.tsx`.
