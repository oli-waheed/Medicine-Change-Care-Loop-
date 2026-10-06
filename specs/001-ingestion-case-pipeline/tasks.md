# Tasks: Medicine Change Ingestion-to-Case Pipeline

**Input**: Design documents from `specs/001-ingestion-case-pipeline/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Included because the plan and project constitution require automated business-logic/contract tests and manual end-to-end validation.

**Organization**: Tasks are grouped by the three prioritized user stories. Paths follow the logical `workflow/`, `backend/`, `frontend/`, and `tests/` boundaries in `plan.md`; the team must record its chosen language, framework, storage, and test runner before implementing them.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Resolve the documented implementation choices and source assumptions before code is started.

- [ ] T001 [P] Confirm permitted automated access, current Basic Register file layout, source release/order evidence, medicine/package identifiers, and the exact relevant catalog fields; record verified facts and unresolved decisions in `specs/001-ingestion-case-pipeline/research.md`
- [ ] T002 [P] Select the implementation language, backend/UI frameworks, persistence technology, and test runner; update the concrete module paths and commands in `specs/001-ingestion-case-pipeline/plan.md` and `specs/001-ingestion-case-pipeline/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared evidence, entity, fixture, and normalization foundations required by all stories.

- [ ] T003 Define and implement persistence models for `SourceRelease`, `MedicineSnapshot`, `DetectedChange`, `SimulatedMedicationRecord`, `ReviewCase`, and `CaseStatusEvent`, including source references, evidence classes, and uniqueness for `(change_id, simulated_record_id)` in `backend/storage/`
- [ ] T004 [P] Add unit tests for source-record normalization, raw-value/source-locator retention, identifier granularity, and `VERIFIED`/`INFERRED`/`UNKNOWN`/`CONFLICTING` classifications in `tests/unit/normalization/`
- [ ] T005 [P] Create controlled prior/current Basic Register fixtures and fictional medication records, including missing/conflicting metadata cases, in `tests/fixtures/`; ensure fixtures contain no real patient-identifiable information
- [ ] T006 Implement normalization for the team-approved Basic Register files and relevant fields, retaining source release and raw-record references plus evidence classifications, in `backend/src/normalization/`

**Checkpoint**: Entity persistence, evidence rules, simulated fixtures, and normalization are available for independent story work.

---

## Phase 3: User Story 1 - Review a case from a medicine-information change (Priority: P1, MVP)

**Goal**: Turn ordered snapshots and a unique simulated medication match into a traceable NEW case visible in a pharmacist read-only view.

**Independent Test**: Load controlled prior/current release fixtures and one exact-granularity matching simulated medication record; verify one NEW case appears with before/after source evidence, simulated-record details, evidence classifications, and its initial status event.

### Tests for User Story 1

- [ ] T007 [P] [US1] Add unit tests for baseline snapshots, relevant-field comparisons, ordered prior/current evidence, and unknown/conflicting release order in `tests/unit/change-detection/`
- [ ] T008 [P] [US1] Add unit tests for exact identifier matching at the same authorization/package granularity and explicit match outcomes in `tests/unit/matching/`
- [ ] T009 [P] [US1] Add contract tests for the pharmacist case read view and initial NEW status event, including required evidence and source-order fields, in `tests/contract/case-view/`
- [ ] T010 [P] [US1] Add the fixture-driven happy-path integration test from two normalized releases through case creation to the read-only case view in `tests/integration/ingestion-to-case/`

### Implementation for User Story 1

- [ ] T011 [US1] Implement release ordering, baseline handling, and relevant-field change detection with prior/current snapshot references and honest unknown/conflicting outcomes in `backend/src/change-detection/`
- [ ] T012 [US1] Implement deterministic matching using only the agreed identifier and identical granularity; return explicit `MATCHED`, `NO_MATCH`, or `AMBIGUOUS` outcomes in `backend/src/matching/`
- [ ] T013 [US1] Create one review case for a unique matched change in `NEW` status and record its initial `CaseStatusEvent` with timestamps and evidence links in `backend/src/cases/`
- [ ] T014 [US1] Implement a read-only case query that returns medicine identity, simulated match, changed field and before/after values, release/source references, retrieval/order information, evidence classifications, and current status in `backend/src/case-view/`
- [ ] T015 [US1] Build the pharmacist-facing open-case list and case evidence view with no case-closing or clinical-decision controls in `frontend/src/case-review/`

**Checkpoint**: The controlled happy path is independently testable from normalized release fixtures through the pharmacist's read-only case view.

---

## Phase 4: User Story 2 - Ingest and trace an official source snapshot (Priority: P2)

**Goal**: Capture complete Fimea Basic Register releases on an agreed schedule and retain immutable, identifiable source evidence and normalized snapshots.

**Independent Test**: Run the scheduled n8n workflow against an approved source fixture; verify complete raw files, filenames/checksums, source identity/order metadata, retrieval time, and normalized snapshots are traceable, while unavailable, malformed, or partial input is visibly incomplete/failed and creates no successful snapshot.

### Tests for User Story 2

- [ ] T016 [P] [US2] Add ingestion contract tests for complete versus failed capture and required source identity, source order, retrieval time, file checksums, and immutable content references in `tests/contract/ingestion/`
- [ ] T017 [P] [US2] Add ingestion integration tests for successful fixture capture plus unavailable, malformed, and interrupted/partial source responses in `tests/integration/source-ingestion/`

### Implementation for User Story 2

- [ ] T018 [US2] Create the n8n scheduled workflow to check for and acquire complete Fimea Basic Register releases using the agreed schedule without implying a cadence faster than the twice-monthly source releases in `workflow/n8n/medicine-basic-register-ingestion.json`
- [ ] T019 [US2] Implement the ingestion boundary to retain each raw release bundle immutably with filenames, checksums, content references, source-provided release/order evidence, and local retrieval time in `backend/src/ingestion/`
- [ ] T020 [US2] Validate whole-release completeness before publishing normalized snapshots; record an auditable ingestion-run status event with source/release references, timestamps, outcome, and failure detail, never substitute retrieval time for source chronology, and prevent partial data from appearing successful in `backend/src/ingestion/`
- [ ] T021 [US2] Connect the n8n workflow to the ingestion boundary and verify that a successful release produces traceable `SourceRelease` and `MedicineSnapshot` records while a failed run produces no case-triggering partial snapshot in `workflow/n8n/medicine-basic-register-ingestion.json`

**Checkpoint**: A source operator can distinguish a successfully captured release from an incomplete or failed ingestion and trace every normalized record to immutable raw evidence.

---

## Phase 5: User Story 3 - Avoid unsupported or duplicate review cases (Priority: P3)

**Goal**: Keep unmatched, ambiguous, or uncertain changes out of the case list and make replay idempotent.

**Independent Test**: Process a no-match change, an ambiguous identifier, an unknown/conflicting-order change, and a unique match twice; verify only one case exists for the unique match and there are no unsupported cases or duplicate initial status events.

### Tests for User Story 3

- [ ] T022 [P] [US3] Add unit tests proving missing, conflicting, or multiple plausible identifiers yield `NO_MATCH`/`AMBIGUOUS` outcomes and never a case in `tests/unit/matching/`
- [ ] T023 [P] [US3] Add replay integration tests proving identical release evidence and the same change/record pair create no duplicate case or initial status event in `tests/integration/idempotency/`

### Implementation for User Story 3

- [ ] T024 [US3] Preserve explicit unmatched and ambiguous processing outcomes with their evidence classifications and suppress case creation unless there is one deterministic same-granularity match in `backend/src/matching/`
- [ ] T025 [US3] Derive a stable idempotency key from the detected change and simulated medication record, enforce atomic uniqueness during case creation, and leave the existing case/status event unchanged on replay in `backend/src/cases/`
- [ ] T026 [US3] Make replay and suppressed-case outcomes inspectable in processing results without presenting uncertain changes as verified cases in `backend/src/processing-status/`

**Checkpoint**: Replays are idempotent, and unsupported or uncertain matches remain visible as outcomes without entering the pharmacist case list.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Align operator guidance, acceptance evidence, and safety boundaries across the completed stories.

- [ ] T027 [P] Update `specs/001-ingestion-case-pipeline/quickstart.md` and `README.md` with selected stack prerequisites, fixture setup, agreed source/relevant-field assumptions, n8n run instructions, and automated test commands
- [ ] T028 Run every quickstart acceptance scenario, including source failure, unknown order, ambiguous/no match, replay, and evidence-unavailable display; record results and unresolved issues in `specs/001-ingestion-case-pipeline/acceptance-results.md`
- [ ] T029 Review `workflow/n8n/`, `backend/`, `frontend/`, and `tests/` against the safety constraints; verify all person/medication data is simulated and no diagnosis, treatment recommendation, substitution, urgency decision, automatic closure, patient view, external clinical integration, or production deployment was added

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 and T002 can run in parallel; both must finish before implementation foundations are finalized.
- **Foundational (Phase 2)**: Depends on Setup; T003 and T005 establish shared persistence/fixtures, T004 defines normalization expectations, and T006 implements normalization after its tests and fixtures are ready. This phase blocks all user stories.
- **User Stories (Phases 3-5)**: US1 and US2 can start after Foundation and can proceed in parallel. US3 depends on the matching and case-creation behavior from US1.
- **Polish (Phase 6)**: Depends on the stories selected for delivery; full acceptance and safety review require US1, US2, and US3.

### User Story Dependencies

- **US1 (P1)**: Depends on Foundation; uses controlled normalized fixtures and is independently testable without the scheduled live-source workflow.
- **US2 (P2)**: Depends on Foundation; exercises scheduled source acquisition and snapshot persistence independently of case matching and UI delivery.
- **US3 (P3)**: Depends on US1 matching and case creation; adds explicit suppression and replay guarantees to that flow.

### Parallel Opportunities

- **Setup**: T001 and T002 edit separate planning artifacts.
- **Foundation**: T004 and T005 can proceed in parallel after Setup; T006 follows both and the shared entity foundation.
- **US1**: T007-T010 are separate test slices and can be authored in parallel; after those tests, change detection (T011) and matching (T012) can proceed in parallel.
- **US2**: T016 and T017 can be authored in parallel; workflow configuration and backend ingestion work may be split once their boundary contract is agreed.
- **US3**: T022 and T023 can be authored in parallel; suppression and idempotency implementation touch distinct matching and case modules.
- **Across stories**: US1 and US2 can be staffed in parallel after Foundation; US3 follows US1.

### Parallel Example: User Story 1

```text
After Foundation, author these independent tests in parallel:
T007 tests/unit/change-detection/
T008 tests/unit/matching/
T009 tests/contract/case-view/
T010 tests/integration/ingestion-to-case/

After the tests are in place, implement in parallel:
T011 backend/src/change-detection/
T012 backend/src/matching/
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup and Foundational phases, including the source-field/order decisions and simulated fixtures.
2. Complete US1 using controlled prior/current normalized snapshots and a unique simulated medication match.
3. Validate the one-NEW-case journey, evidence links, read-only pharmacist view, and initial status event independently.
4. Defer scheduled external acquisition to US2; do not use the fixture-based MVP to imply that live Fimea ingestion is complete.

### Incremental Delivery

1. Complete Setup + Foundation and verify normalization against controlled fixtures.
2. Deliver US1 as the traceable case-review MVP.
3. Deliver US2 to add scheduled n8n acquisition of complete official source releases.
4. Deliver US3 to prove no-match/ambiguous suppression and idempotent replay.
5. Run the full quickstart acceptance set and safety review before declaring the feature complete.