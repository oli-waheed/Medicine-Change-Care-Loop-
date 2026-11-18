# Data Model: Medicine Change Ingestion-to-Case Pipeline

This model describes the information needed for the feature. How it is stored in the prototype is summarised in [Implementation mapping](#implementation-mapping).
Every record is prototype data; patient and medication records must be simulated.

## Entities

### SourceRelease

Represents one captured release from the selected Fimea Basic Register.

| Field | Meaning | Validation |
|---|---|---|
| `release_id` | Prototype identifier for this captured release | Unique and immutable; `sha256-` + checksum of the capture manifest |
| `source_name` | Official source name | Required; identify Fimea Basic Register |
| `source_release_reference` | Release/version/date provided by Fimea, if present | Preserve verbatim; may be unknown |
| `source_order` | Established ordering key from source release evidence | Derived by the backend from the XML's `Ajopvm`: `VERIFIED` when every file has the same ISO date, `CONFLICTING` when files disagree, otherwise `UNKNOWN`. Never derived from retrieval time or caller-declared order |
| `retrieved_at` | Time the prototype fetched the release | Required; not represented as source update time |
| `files` | Captured file names and content checksums | Required for each captured file |
| `processing_status` | Capture/validation outcome | `VALIDATED` or `FAILED`; chronology is reported separately as `AVAILABLE` or `UNAVAILABLE` |
| `failure_detail` | Human-readable reason for incomplete or failed processing | Required when failed |

### MedicineSnapshot

Represents a normalized medicine/package record as captured in a source release.

| Field | Meaning | Validation |
|---|---|---|
| identity | The release, `package_identifier`, and `source_record_reference` together | Unique within a release; snapshots are not stored separately (see [Implementation mapping](#implementation-mapping)) |
| `release_id` | Source release containing this record | Required reference to `SourceRelease` |
| `source_record_reference` | File and record locator in raw release evidence, for example `/Perusrekisteri/Pakkaus[1]` | Required |
| `product_source_reference` | `Pakkaus/@Laakevalmiste-ref` resolved to `Laakevalmiste/@id` in this same source document | Preserve source values and relation; not the cross-release package key |
| `package_identifier` | `Pakkaus/Pakkaustunnus` | Primary package comparison key by team decision; preserve as source string; unambiguous presence is required to pair records |
| `supporting_package_reference` | Optional `Pakkaus/VNR-numero` | Supporting source metadata only; never the primary key or fallback match |
| `normalized_fields` | The team-approved source fields used for package comparison | Retain exact source values, paths, multiplicity, and element state; distinguish absent from present-but-empty |
| `evidence_class` | Evidence status of normalized values | One of `VERIFIED`, `INFERRED`, `UNKNOWN`, `CONFLICTING` as applicable, carried by the `EvidenceProvenance` of each change; does not indicate clinical significance |

The comparison field set is: product paths `Kauppanimi`, `Vahvuus`, `Laakemuoto`, `ATC-koodi`, `Antoreitti`; linked active-substance paths `VaikuttavaAine/Aine`, `CASnumero`, `Maara`, `Maarayksikko`, `JakamatonVahvuus`; package paths `Pakkauskokoteksti`, `Pakkauskoko`, `Pakkauskokokerroin`, `Pakkauskokoyksikko`, `JulkinenTarkenne`; package-status paths `Kaupanolo/Kaupan`, `Kaupanolo/Kauppaantulopaiva`, `Kaupanolo/Kaupastapoistumispaiva`; and the present authorization/registration branch's `Tila`, `Myontamispaiva`, and `Paattymispaiva` under `Myyntilupa`, `Erityislupa`, or `Rekisterointi`. Product and active-substance paths are resolved through the source document's package IDREFs. For repeated fields, preserve each occurrence and source order. Linked active substances are paired across releases by their `Aine` code (CT `id`), falling back to `Aine` text and then `CASnumero`, never by list position, so a field change is always reported against the same substance (for example `Laakeaine/VaikuttavaAine[Aine=<code>]/Maara`); a pure reordering of substances is not a change. Authorization/registration occurrences are numbered within their own branch. For code-table values, preserve the source element's attributes and text. A difference in one or more selected source values or their element presence is a detected source-data change, not a clinical-significance decision.

`Pakkaustunnus` uniqueness was observed only within the one inspected local XML snapshot. Stability or uniqueness across separate releases is unverified; do not assert it as a verified cross-release property. If same-key pairing is missing or ambiguous between snapshots, do not substitute VNR or `Laakevalmiste/@id` as the cross-release package key.

### EvidenceProvenance

Records the classification and source traceability for a source value or evidence item. It links to
the `SourceRelease` and its captured-source provenance rather than duplicating or reinterpreting
release metadata.

| Field | Meaning | Validation |
|---|---|---|
| `source_release` | Source release containing the evidence | Required reference to `SourceRelease`; provides source name, release identifier/date when available, and captured-file provenance |
| `source_record_identifier` | Source record or package identifier, such as `Pakkaustunnus` | Required non-empty source value |
| `source_record_locator` | File/record locator for the specific source record | Optional; non-empty when supplied |
| `field_reference` | Source field/path or evidence reference | Optional when evidence applies to a whole record/release; non-empty when supplied |
| `source_value` | Original source value and element state, if applicable | Optional `SourceField`; preserve missing, empty, and populated states and source attributes |
| `classification` | Evidence status | Required `VERIFIED`, `INFERRED`, `UNKNOWN`, or `CONFLICTING` |
| `note` | Brief provenance or uncertainty explanation | Optional; non-empty when supplied; not a clinical interpretation |

Classification rules:

- `VERIFIED`: the value or fact is directly supported by the referenced source evidence and its trace is available. This describes evidence provenance, not clinical truth or significance.
- `INFERRED`: the value is derived rather than directly stated by the cited source. Record the derivation basis in the note or linked evidence; it is not authoritative by itself.
- `UNKNOWN`: the value or its provenance cannot be established from available evidence. Preserve absent/empty source states and do not fill the gap with a guess.
- `CONFLICTING`: relevant source evidence disagrees and the disagreement has not been resolved. Retain the competing source references/values rather than silently selecting one.

Source values, classifications, and notes describe evidence only. They do not diagnose, recommend
treatment or substitution, set clinical urgency, or decide case status. No evidence classification
is itself a clinical conclusion.

### DetectedChange

Represents a difference in an explicitly relevant field between ordered snapshots.

| Field | Meaning | Validation |
|---|---|---|
| `change_id` | Stable identity for the release-to-release change | Deterministic for same source records and field |
| `medicine_key` | `Pakkaustunnus` and package granularity used to pair the records | Required; ambiguous keys cannot produce verified changes; cross-release stability remains unverified |
| `field_name` | Changed field | Must be in the agreed relevant-field set |
| `prior_value` | Value in previous snapshot | Preserve source value and evidence reference |
| `current_value` | Value in current snapshot | Preserve source value and evidence reference |
| `prior_snapshot` | Previous evidence record | Required when a comparable prior record exists |
| `current_snapshot` | Current evidence record | Required |
| `change_evidence_class` | Certainty of ordering, pairing, and difference | Unknown/conflicting order cannot be labeled verified |
| `detected_at` | Time comparison was performed | Required; distinct from source update time |

### PackageChangeSet

Groups everything detected for one package (`Pakkaustunnus`) between one ordered release pair. Review cases are created from change sets, so one package update produces one case per matched simulated record.

| Field | Meaning | Validation |
|---|---|---|
| `change_set_id` | Stable identity | Deterministic from both release identities, `medicine_key` and `kind` |
| `medicine_key` | `Pakkaustunnus` | Required |
| `kind` | `FIELDS_CHANGED` or `NO_LONGER_PRESENT` | Required |
| `field_changes` | The `DetectedChange` items for this package pair | At least one for `FIELDS_CHANGED`; none for `NO_LONGER_PRESENT`; each field at most once |
| `prior_snapshot` | Package record in the prior release | Required |
| `current_snapshot` | Package record in the current release | Required for `FIELDS_CHANGED`; absent for `NO_LONGER_PRESENT` |
| `prior_evidence` / `current_evidence` | Record-level provenance in each release | For `NO_LONGER_PRESENT`, current evidence names the current release and has no record locator |
| `change_evidence_class`, source order, `detected_at` | As for `DetectedChange` | Unknown/conflicting order produces no change set |

`NO_LONGER_PRESENT` is created only when the prior release has exactly one `Pakkaus` with the key and the current full-coverage release (`Kattavuus` = 1) has none. It is a source-data difference only: the source does not state whether the package was withdrawn, renumbered or omitted in error, and the case wording must not claim a reason. Packages present only in the current release are recorded as notes and never create cases; packages whose key is duplicated in either release remain ambiguous notes.

### SimulatedMedicationRecord

Represents fictional medication use data for matching.

| Field | Meaning | Validation |
|---|---|---|
| `simulated_record_id` | Fictional record reference | Unique and clearly simulated |
| `simulated_person_reference` | Fictional person reference, if needed to group records | Must not contain real patient identifiers |
| `package_identifier` | Optional simulated `Pakkaustunnus` at package granularity | Exact same-granularity comparison only; source stability across releases is not assumed |
| `supporting_package_reference` | Optional simulated `VNR-numero` | Display/provenance only; not used as a match key |
| `medicine_display` | Fictional medicine name shown in the pharmacist view | Required; must contain no real patient-identifiable information |

### ReviewCase

Represents a human-review item created from one package change set and one deterministic simulated-record match.

| Field | Meaning | Validation |
|---|---|---|
| `case_id` | Unique case identity | Unique |
| `change_set_id` | Package change set supporting the case | Required reference |
| `simulated_record_id` | Matched fictional medication record | Required reference |
| `status` | Current human-review state | New case begins as `NEW` |
| `created_at` | Case creation time | Required |
| `evidence_class` | Evidence status shown with the case | Must preserve unknown/conflicting information |
| `idempotency_key` | Identity derived from change set and simulated record | Unique; prevents duplicate cases on reprocessing |

### ChangeProcessingOutcome

Records the deterministic match result for one `PackageChangeSet`, including results that create no case.

| Field | Meaning | Validation |
|---|---|---|
| `outcome_id` | Outcome identity | Equal to `change_set_id`; at most one outcome per change set, so replays add nothing |
| `result` | `MATCHED`, `NO_MATCH`, or `AMBIGUOUS` | Required |
| `reason` | `UNIQUE_EXACT_PACKAGE_MATCH`, `NO_SIMULATED_RECORD`, or `MULTIPLE_SIMULATED_RECORDS` | Must agree with `result` |
| `simulated_record_ids` | Records sharing the compared `Pakkaustunnus` | None for `NO_MATCH`; two or more for `AMBIGUOUS` |
| `case_ids` | Case created from a `MATCHED` result | Empty for `NO_MATCH` and `AMBIGUOUS`; never invented when no case exists |
| `evidence_class`, sources, source order | Copied from the change set | Preserve unknown/conflicting information |

### CaseStatusEvent

Records an important case status transition, including initial creation in NEW status.

| Field | Meaning | Validation |
|---|---|---|
| `event_id` | Unique transition event | Unique |
| `case_id` | Case whose status changed | Required reference |
| `from_status` | Previous status, absent for initial creation | Must agree with transition |
| `to_status` | New status | Initial event must be `NEW` |
| `occurred_at` | Time the transition was recorded | Required |

## Relationships and State Rules

- One `SourceRelease` contains many `MedicineSnapshot` records.
- A `DetectedChange` references the prior and current snapshots where both exist; a first snapshot is baseline only and does not imply a detected change.
- A `PackageChangeSet` groups all `DetectedChange` items for one package and release pair, or records that the package is no longer present.
- A `PackageChangeSet` may match zero or more simulated medication records only when each match is deterministic and at the same identifier granularity; ambiguous matches create no case.
- A `ReviewCase` references exactly one package change set and one simulated medication record.
- A unique `(change_set_id, simulated_record_id)` pair can create at most one case. A later release that changes the same package again forms a new change set and therefore a new case.
- A case is created in `NEW`; this feature does not define case resolution or clinical escalation.
- `CaseStatusEvent` records the initial NEW state and any later important status transition, without this feature adding transitions beyond its scope.
- Failure to establish source order, source identity, or an unambiguous same-value `Pakkaustunnus` pair must be represented as unknown/conflicting evidence, not silently repaired or matched by VNR/product attributes.
- Package/product field changes communicate source differences only. They do not establish clinical significance or permit diagnosis, treatment, urgency, or substitution decisions.

## Implementation mapping

As implemented on 2026-11-18:

- Raw source files are stored unchanged in `backend/data/source-releases/<release_id>/` with a
  `manifest.json` that records the source name, release reference, caller-declared order, retrieval time,
  file names, checksums, and record locators when supplied.
- SQLite (`backend/data/medicine-change-care-loop.sqlite3`, through SQLAlchemy) holds four tables:
  `source_release_captures` (`SourceRelease` with processing status, derived order, and failure detail),
  `review_cases` (`ReviewCase` with the stored evidence view), `case_status_events` (`CaseStatusEvent`),
  and `change_processing_outcomes` (`ChangeProcessingOutcome`).
- `MedicineSnapshot`, `DetectedChange`, and `PackageChangeSet` are not stored as separate tables. Snapshots
  are re-derived from the immutable raw capture when needed; for example, after a restart the comparison
  baseline is rebuilt from its raw file once its checksum is verified. The changes and change set behind a
  case or outcome are stored inside that case's or outcome's evidence view.
- Simulated medication records are read at startup from a JSON file (`backend/seed/` by default) and are
  not written to the database.

