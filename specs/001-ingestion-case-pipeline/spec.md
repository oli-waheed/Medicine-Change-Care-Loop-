# Feature Specification: Medicine Change Ingestion-to-Case Pipeline

**Feature Branch**: `Not created`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Build the ingestion-to-case pipeline for the Medicine Change Care Loop prototype, from scheduled ingestion of selected official Finnish medicine information through change detection and simulated medication matching to a pharmacist-facing, evidence-based review case list."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review a case from a medicine-information change (Priority: P1)

A pharmacist reviews an open case created after the system ingests a relevant medicine-information change and finds the source evidence and matching simulated medication record needed to understand why the case exists.

**Why this priority**: This is the core user outcome of the feature: a traceable change becomes visible for human review without making a clinical decision.

**Independent Test**: Provide a prior and updated official-source snapshot plus a matching simulated medication record; verify that one NEW case appears in the open-case list with links to its source evidence and simulated record.

**Acceptance Scenarios**:

1. **Given** a valid prior snapshot, a newer snapshot with a relevant medicine-information change, and a matching simulated medication record, **When** the scheduled ingestion and matching flow completes, **Then** the system creates a review case in NEW status and lists it for pharmacist review.
2. **Given** an open review case, **When** a pharmacist opens its evidence, **Then** the view identifies the medicine, matched simulated medication record, source snapshot(s), source update information, detected change, and case status.
3. **Given** a review case is created, **When** it is assigned NEW status, **Then** the creation and initial status are recorded as an important case status event.

---

### User Story 2 - Ingest and trace an official source snapshot (Priority: P2)

A project operator can verify that the scheduled process captured the selected official Finnish medicine-information source as a traceable snapshot, so later change detection is based on identifiable source evidence.

**Why this priority**: Reliable snapshots are a prerequisite for detecting changes and explaining cases; this story establishes that evidence without requiring clinical interpretation.

**Independent Test**: Run the scheduled ingestion against an available source test fixture and verify that the resulting snapshot can be identified by medicine and source, with its source update information and retrieval record.

**Acceptance Scenarios**:

1. **Given** the selected source is available and contains medicine information, **When** a scheduled ingestion runs, **Then** the system stores a normalized snapshot that retains its source identity, source update information, and retrieval time.
2. **Given** the selected source is unavailable or its information cannot be interpreted, **When** ingestion runs, **Then** the run is visibly incomplete or failed and the system does not present partial data as a successfully ingested snapshot.

---

### User Story 3 - Avoid unsupported or duplicate review cases (Priority: P3)

A pharmacist can rely on the open-case list to contain only cases supported by a relevant detected change and a matching simulated medication record, without repeated processing creating duplicate cases.

**Why this priority**: Clear case boundaries reduce noise and protect the human-review workflow from unsupported or repetitive entries.

**Independent Test**: Process changes with no medication match and reprocess an already handled matching change; verify that no unsupported case is created and no duplicate case appears.

**Acceptance Scenarios**:

1. **Given** a relevant medicine-information change and no matching simulated medication record, **When** matching completes, **Then** no review case is created for that change.
2. **Given** a change and matching simulated medication record have already produced a case, **When** the same source data is processed again, **Then** no duplicate case is created for the same change and simulated record.

---

### Edge Cases

- A medicine has no prior snapshot: retain the new snapshot as the baseline and do not report a change that cannot be compared.
- Source update information is missing, conflicting, or cannot establish which snapshot is newer: make the uncertainty visible and do not claim a verified change based on unsupported ordering.
- A snapshot contains incomplete or conflicting medicine identifiers: do not create a medication match or review case from an ambiguous match; expose the uncertainty in the processing result.
- A source is unavailable, returns malformed information, or ingestion stops partway through: do not treat the run as complete or create cases from a partial snapshot.
- A relevant change has no matching simulated medication record: retain the traceable detected change but do not create a review case.
- A pharmacist opens a case whose source evidence is no longer available: show that the evidence is unavailable rather than presenting the case as fully verified.
- The same source snapshot is ingested more than once: repeated processing must not create duplicate changes or cases.
- The prototype must not ingest, store, or display real patient-identifiable information.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST run scheduled ingestion for Fimea's Basic Register of medicinal products, capturing complete source releases for comparison.
- **FR-002**: For each successfully ingested source item, the system MUST store a snapshot that identifies the source and medicine and records source update information and retrieval time.
- **FR-003**: The system MUST normalize the medicine information needed for comparison and matching while preserving enough source evidence to trace normalized information to the source snapshot.
- **FR-004**: The system MUST compare each new snapshot with the previous snapshot for the same medicine and identify changes in the defined relevant medicine-information fields, using the source update information to establish source order.
- **FR-005**: Each detected change MUST reference the source snapshot evidence for both the prior and updated information when both are available.
- **FR-006**: The system MUST compare detected changes against simulated patient medication records using defined medicine-matching criteria.
- **FR-007**: When a relevant change matches a simulated medication record, the system MUST create a review case in NEW status and make it available in the pharmacist-facing open-case view.
- **FR-008**: The system MUST NOT create a review case for a change that has no matching simulated medication record or whose match is ambiguous.
- **FR-009**: Reprocessing the same source change for the same simulated medication record MUST NOT create duplicate review cases.
- **FR-010**: The pharmacist-facing view MUST list open review cases and display the medicine, case status, matched simulated medication record, detected change, and source evidence that caused the case to be created.
- **FR-011**: Information presented for snapshots, changes, and cases MUST distinguish verified, inferred, unknown, and conflicting information where applicable.
- **FR-012**: Every snapshot, detected change, and review case MUST be traceable to its source snapshot; important case status transitions, including creation in NEW status, MUST be recorded.
- **FR-013**: All patient and medication records used by the prototype MUST be simulated. The system MUST NOT accept or use real patient-identifiable information.
- **FR-014**: The system MUST detect and communicate medicine-information changes only. It MUST NOT diagnose, recommend treatment, select medicine substitutions, decide clinical urgency, or automatically close clinically relevant cases.
- **FR-015**: If ingestion fails, source ordering cannot be established, or required information is ambiguous, the system MUST expose the incomplete or uncertain result and MUST NOT represent it as a verified successful change-to-case flow.
- **FR-016**: The system MUST NOT include AI explanations, patient-facing views, communication or follow-up workflows, real patient data, Kanta/EHR integration, pharmacy inventory integration, automatic medicine substitution, autonomous clinical decisions, or production deployment in this feature.

### Key Entities *(include if feature involves data)*

- **Source Snapshot**: A captured version of selected official medicine information, associated with a source, medicine, source update information, and retrieval time.
- **Detected Change**: A relevant difference between snapshots for the same medicine, with evidence linking to the source information before and after the change.
- **Simulated Medication Record**: A fictional patient-medication association used only to evaluate whether a detected change should produce a review case.
- **Review Case**: A human-review item created when a relevant detected change matches a simulated medication record; starts in NEW status and retains its evidence links.
- **Case Status Transition**: A recorded change to a review case's status, including the case identity and transition information.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the agreed acceptance dataset, every relevant source change with a unique matching simulated medication record produces exactly one review case in NEW status.
- **SC-002**: In the agreed acceptance dataset, no review case is produced for changes with no match or an ambiguous match.
- **SC-003**: For every case in the acceptance dataset, a pharmacist can reach the source snapshot evidence and identify the change and matching simulated medication record from the case view.
- **SC-004**: Reprocessing the acceptance dataset produces no additional duplicate review cases.
- **SC-005**: In all acceptance scenarios, the system creates no diagnosis, treatment recommendation, substitution decision, urgency decision, or automatic case closure.
- **SC-006**: All patient and medication records in the prototype test and demonstration dataset are simulated, with zero real patient-identifiable records.

## Assumptions

- Only catalog fields present in the selected Fimea Basic Register releases are in scope; the team will identify the exact included files and relevant fields before implementation. This source does not establish leaflet/SPC clinical-content change monitoring.
- Source update information is the primary evidence for ordering snapshots; where it is unavailable or contradictory, the system reports uncertainty instead of guessing.
- Matching criteria are deterministic and will use medicine identifiers present in both the source information and simulated medication records.
- An open case for this feature is a case in NEW status; case handling and additional workflow states are outside this feature.
- The scheduled source fetch and ingestion are orchestrated by the requested n8n workflow; the exact Basic Register files and relevant catalog fields will be confirmed before implementation.
- Acceptance data consists exclusively of simulated medication records and controlled source snapshots.
