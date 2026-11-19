# Data Model: Open Review Case Readability

This feature changes presentation only. It adds no stored fields, API fields, or data transitions. The page continues to display the current `OpenReviewCase` response shape defined in `frontend/src/pages/open-review-cases/openReviewCases.ts`.

## Review Case

Represents one existing simulated case in the list and details view.

| Field | Display role | Validation or display rule |
|---|---|---|
| `caseId` | Stable identity and evidence heading context | Unique within the displayed list; do not alter its value |
| `status` | Case status badge and list status | Existing `NEW` status; preserve the exact text |
| `medicineIdentifier` | Case-list and detail identifier | Preserve existing text; allow long values to wrap |
| `identifierGranularity` | Identifier context | Preserve existing text |
| `matchedRecord` | Simulated record identity and medicine display | Keep every existing value visible |
| `createdAt` | Case creation timestamp | For a valid timestamp, display `YYYY-MM-DD HH:MM UTC` in a `<time>` element; retain the exact original string in `dateTime` and show it as small muted text next to the readable time. Preserve the current fallback for invalid or missing values. |
| `changeSet` | Detected source change details | Render all changes or the existing no-longer-present view |
| `sources` | Prior and current source evidence | Keep each source's existing values and evidence-availability state |
| `sourceOrder` | Ordering values, basis, and classification | Preserve exact values and uncertainty |
| `evidenceClass` | Case-level classification | One of `VERIFIED`, `INFERRED`, `UNKNOWN`, or `CONFLICTING`; render the existing text as a distinct label |
| `evidenceAvailability` | Source availability state | Preserve existing unavailable warning behavior |
| `initialStatusEvent` | Initial case status evidence | Existing read-only information; do not add a workflow action |

## Field Change

Represents one changed source field within a change set.

| Field | Display role | Validation or display rule |
|---|---|---|
| `changeId` | Stable list key | Not new user-facing wording |
| `field` | Field locator/name | Preserve exact value; monospace presentation is suitable for technical locators |
| `before` | Prior source field values | Render every item under the existing “Before” wording |
| `after` | Current source field values | Render every item under the existing “After” wording |

Each `SourceField` has a `state` of `missing`, `empty`, or `value`, a nullable `value`, and source `attributes`. Continue using the existing source-value formatter so missing, empty, plain, and code-table values remain distinct.

## Change Set

Represents either a set of changed fields (`FIELDS_CHANGED`) or a package that is no longer present (`NO_LONGER_PRESENT`). Preserve the existing rendering rules, changed-field count, and last-known values; do not infer a reason for absence.

## Source Evidence

Represents evidence for the prior or current source release.

| Field | Display role | Validation or display rule |
|---|---|---|
| `sourceName` | Source identity | Preserve existing wording |
| `releaseReference`, `releaseDate` | Release values | Use the existing source-value formatter |
| `fileName`, `checksum`, `recordLocator` | Technical source references | Preserve exact value and render in monospace |
| `retrievedAt` | Retrieval timestamp | Use the same UTC format, adjacent exact-value display, and fallback rules as `createdAt` |
| `evidenceClass` | Source classification | One of the four supported classification labels |
| `evidenceAvailable` | Raw-file availability | Preserve existing source-unavailable wording and behavior |
| `note` | Source note | Preserve exact existing information |

## View State

- **Selection**: `selectedId` refers to one case in the loaded list or is null. It is presentation state only and is not persisted.
- **Loading**: Existing loading indicator remains until the current request settles.
- **Error**: Existing explicit error message remains visible on request failure.
- **Empty list**: Existing empty-state wording remains visible when there are no cases.
- **Timestamp display**: Valid timestamps use the exact `YYYY-MM-DD HH:MM UTC` display and preserve the original recorded value in `dateTime`; the original is always shown as small muted text next to the formatted time. Missing or invalid values retain the existing fallback and do not produce an invented timestamp.
- **Unavailable evidence**: A classification shown after evidence becomes unavailable retains its existing “when recorded; ... now unavailable” wording and uses a warning presentation distinct from current verification.
- **Source-field states**: `missing`, `empty`, and zero-occurrence values retain their current phrases and are visually distinct from real source values.

No model changes or database migrations are required.
