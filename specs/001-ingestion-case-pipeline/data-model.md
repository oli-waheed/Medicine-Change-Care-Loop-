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
| `authorization_identifier` | Source identifier at marketing-authorization granularity, such as an MA-number | Preserve source value; do not confuse with package identity |
| `package_identifier` | Source identifier at package granularity, such as a Nordic article number | Preserve source value; required for package-level match |
| `normalized_fields` | Selected source fields used for comparison/matching | Each field retains its original source reference |
| `evidence_class` | Evidence status of normalized values | One of `VERIFIED`, `INFERRED`, `UNKNOWN`, `CONFLICTING` as applicable |

### DetectedChange

Represents a difference in an explicitly relevant field between ordered snapshots.

| Field | Meaning | Validation |
|---|---|---|
| `change_id` | Stable identity for the release-to-release change | Deterministic for same source records and field |
| `medicine_key` | Identifier and granularity used to pair the records | Required; ambiguous keys cannot produce verified changes |
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
| `authorization_identifier` | Optional fictional authorization-level medicine key | Only match at same granularity |
| `package_identifier` | Optional fictional package-level medicine key | Only match at same granularity |
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
- Failure to establish source order, source identity, or an unambiguous medicine key must be represented as unknown/conflicting evidence, not silently repaired.
