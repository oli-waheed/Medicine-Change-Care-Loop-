# Data Model: Medicine Change Ingestion-to-Case Pipeline

This model describes the information needed for the feature. It does not prescribe a storage technology.
Every record is prototype data; patient and medication records must be simulated.

## Entities

### SourceRelease

Represents one captured release from the selected Fimea Basic Register.

| Field | Meaning | Validation |
|---|---|---|
| `release_id` | Prototype identifier for this captured release | Unique and immutable |
| `source_name` | Official source name | Required; identify Fimea Basic Register |
| `source_release_reference` | Release/version/date provided by Fimea, if present | Preserve verbatim; may be unknown |
| `source_order` | Established ordering key from source release evidence | Must not be derived from retrieval time |
| `retrieved_at` | Time the prototype fetched the release | Required; not represented as source update time |
| `files` | Captured file names and content checksums | Required for each captured file |
| `processing_status` | Capture/validation outcome | `CAPTURED`, `VALIDATED`, or `FAILED` |
| `failure_detail` | Human-readable reason for incomplete or failed processing | Required when failed |

### MedicineSnapshot

Represents a normalized medicine/package record as captured in a source release.

| Field | Meaning | Validation |
|---|---|---|
| `snapshot_id` | Unique identity for this normalized record in a release | Unique |
| `release_id` | Source release containing this record | Required reference to `SourceRelease` |
| `source_record_reference` | File and record/line locator in raw release evidence | Required |
| `product_source_reference` | `Pakkaus/@Laakevalmiste-ref` resolved to `Laakevalmiste/@id` in this same source document | Preserve source values and relation; not the cross-release package key |
| `package_identifier` | `Pakkaus/Pakkaustunnus` | Primary package comparison key by team decision; preserve as source string; unambiguous presence is required to pair records |
| `supporting_package_reference` | Optional `Pakkaus/VNR-numero` | Supporting source metadata only; never the primary key or fallback match |
| `normalized_fields` | The team-approved source fields used for package comparison | Retain exact source values, paths, multiplicity, and element state; distinguish absent from present-but-empty |
| `evidence_class` | Evidence status of normalized values | One of `VERIFIED`, `INFERRED`, `UNKNOWN`, `CONFLICTING` as applicable; does not indicate clinical significance |

The comparison field set is: product paths `Kauppanimi`, `Vahvuus`, `Laakemuoto`, `ATC-koodi`, `Antoreitti`; linked active-substance paths `VaikuttavaAine/Aine`, `CASnumero`, `Maara`, `Maarayksikko`, `JakamatonVahvuus`; package paths `Pakkauskokoteksti`, `Pakkauskoko`, `Pakkauskokokerroin`, `Pakkauskokoyksikko`, `JulkinenTarkenne`; package-status paths `Kaupanolo/Kaupan`, `Kaupanolo/Kauppaantulopaiva`, `Kaupanolo/Kaupastapoistumispaiva`; and the present authorization/registration branch's `Tila`, `Myontamispaiva`, and `Paattymispaiva` under `Myyntilupa`, `Erityislupa`, or `Rekisterointi`. Product and active-substance paths are resolved through the source document's package IDREFs. For repeated fields, preserve each occurrence and source order. For code-table values, preserve the source element's attributes and text. A difference in one or more selected source values or their element presence is a detected source-data change, not a clinical-significance decision.

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
| `prior_snapshot_id` | Previous evidence record | Required when a comparable prior record exists |
| `current_snapshot_id` | Current evidence record | Required |
| `change_evidence_class` | Certainty of ordering, pairing, and difference | Unknown/conflicting order cannot be labeled verified |
| `detected_at` | Time comparison was performed | Required; distinct from source update time |

### SimulatedMedicationRecord

Represents fictional medication use data for matching.

| Field | Meaning | Validation |
|---|---|---|
| `simulated_record_id` | Fictional record reference | Unique and clearly simulated |
| `simulated_person_reference` | Fictional person reference, if needed to group records | Must not contain real patient identifiers |
| `authorization_identifier` | Optional simulated product authorization metadata | Supporting display/provenance only; not used for package matching |
| `package_identifier` | Optional simulated `Pakkaustunnus` at package granularity | Exact same-granularity comparison only; source stability across releases is not assumed |
| `supporting_package_reference` | Optional simulated `VNR-numero` | Display/provenance only; not used as a match key |
| `display_fields` | Minimum fictional data needed in the pharmacist view | Must contain no real patient-identifiable information |

### ReviewCase

Represents a human-review item created from one detected change and one deterministic simulated-record match.

| Field | Meaning | Validation |
|---|---|---|
| `case_id` | Unique case identity | Unique |
| `change_id` | Detected change supporting the case | Required reference |
| `simulated_record_id` | Matched fictional medication record | Required reference |
| `status` | Current human-review state | New case begins as `NEW` |
| `created_at` | Case creation time | Required |
| `evidence_class` | Evidence status shown with the case | Must preserve unknown/conflicting information |
| `idempotency_key` | Identity derived from change and simulated record | Unique; prevents duplicate cases on reprocessing |

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
- A `DetectedChange` may match zero or more simulated medication records only when each match is deterministic and at the same identifier granularity; ambiguous matches create no case.
- A `ReviewCase` references exactly one detected change and one simulated medication record.
- A unique `(change_id, simulated_record_id)` pair can create at most one case.
- A case is created in `NEW`; this feature does not define case resolution or clinical escalation.
- `CaseStatusEvent` records the initial NEW state and any later important status transition, without this feature adding transitions beyond its scope.
- Failure to establish source order, source identity, or an unambiguous same-value `Pakkaustunnus` pair must be represented as unknown/conflicting evidence, not silently repaired or matched by VNR/product attributes.
- Package/product field changes communicate source differences only. They do not establish clinical significance or permit diagnosis, treatment, urgency, or substitution decisions.
