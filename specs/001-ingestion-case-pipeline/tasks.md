# Tasks: Medicine Change Ingestion-to-Case Pipeline

**Input**: Design documents from `specs/001-ingestion-case-pipeline/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ingestion-and-case-view.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and validation.

**Path note**: T001's selected stack, versions, commands, and concrete source/test naming conventions
are recorded in `specs/001-ingestion-case-pipeline/plan.md`. The path stems below become files using
those documented conventions; workflow, fixture, and Spec Kit paths are concrete.

## Phase 1: Setup

**Purpose**: Establish the minimum agreed implementation environment before application work.

- [x] T001 Record the team's finalized Python/FastAPI + SQLite/SQLAlchemy backend, React/TypeScript/Vite frontend, local n8n workflow, pytest/Vitest test runners, versions, commands, and file naming conventions in `specs/001-ingestion-case-pipeline/plan.md` and `specs/001-ingestion-case-pipeline/quickstart.md`.
- [x] T002 Create the selected backend and frontend app skeletons, n8n workflow directory, and unit/contract/integration test directories under `backend/`, `frontend/`, `workflow/n8n/`, and `tests/`.
- [x] T003 [P] Add the selected stack's formatting, linting, and test-runner configuration at repository root and document the commands in `specs/001-ingestion-case-pipeline/quickstart.md`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Set source/data boundaries and simulated fixtures shared by all stories.

- [x] T004 Inspect the current Fimea Basic Register release files and document selected files, access/reuse constraints, release identity/order evidence, and parsing rules in `specs/001-ingestion-case-pipeline/research.md`.
- [x] T005 Agree the exact relevant catalog fields and same-granularity medicine/package matching key with the team; record the decision and examples in `specs/001-ingestion-case-pipeline/research.md`.
- [ ] T006 [P] Create a clearly fictional medication-record fixture with unique, absent, and ambiguous identifier examples in `tests/fixtures/simulated-medication-records/`.
- [ ] T007 [P] Create small prior/current synthetic Basic Register release fixtures, including one relevant-field change and malformed/ordering-unknown cases, under `tests/fixtures/fimea-basic-register/`.
- [ ] T008 Define and validate shared source-release and medicine-snapshot types in `backend/src/domain/source-release` and `backend/src/domain/medicine-snapshot` using the conventions recorded in `plan.md`.
- [ ] T009 Define provenance and evidence-classification rules for verified, inferred, unknown, and conflicting values in `specs/001-ingestion-case-pipeline/data-model.md` and `specs/001-ingestion-case-pipeline/contracts/ingestion-and-case-view.md`.

**Checkpoint**: Stack, source scope, simulated fixtures, and shared provenance rules are agreed before story work.

---

## Phase 3: User Story 1 - Review a case from a medicine-information change (Priority: P1) 🎯 MVP

**Goal**: Turn a supported change and matching simulated medication record into a traceable NEW case visible to a pharmacist.

**Independent Test**: Process prior/current source snapshot fixtures and a unique matching simulated record; verify one NEW case is shown with before/after evidence, source references, matching record, and initial status event.

### Tests for User Story 1

- [ ] T010 [P] [US1] Add comparison and evidence-provenance unit tests in `tests/unit/medicine-snapshot-comparison`.
- [ ] T011 [P] [US1] Add deterministic matching and supported-case creation tests in `tests/unit/review-case-creation`.
- [ ] T012 [P] [US1] Add case-list contract tests for required status, match, change, and source evidence fields in `tests/contract/open-review-cases`.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Define detected-change, review-case, and case-status-event domain types in `backend/src/domain/detected-change`, `backend/src/domain/review-case`, and `backend/src/domain/case-status-event`.
- [ ] T014 [US1] Implement ordered snapshot comparison for agreed relevant fields, retaining prior/current snapshot evidence, in `backend/src/services/detect-relevant-changes`.
- [ ] T015 [US1] Implement exact same-granularity matching against simulated medication records and create a NEW case with its initial status event in `backend/src/services/create-review-cases`.
- [ ] T016 [US1] Implement the read operation for open NEW cases with change, simulated-record, and source evidence in `backend/src/api/open-review-cases`.
- [ ] T017 [US1] Implement the pharmacist-facing open-case list and evidence view in `frontend/src/pages/open-review-cases`.
- [ ] T018 [US1] Connect the snapshot fixture, comparison, matching, case creation, and review view as one end-to-end vertical slice in `backend/src/workflows/ingestion-to-review` and `frontend/src/pages/open-review-cases`.

**Checkpoint**: User Story 1 is demonstrable using fixtures without requiring live Fimea ingestion.

---

## Phase 4: User Story 2 - Ingest and trace an official source snapshot (Priority: P2)

**Goal**: Capture complete Fimea Basic Register releases on schedule and expose honest, traceable source snapshots for comparison.

**Independent Test**: Submit a valid synthetic release using the same ingestion path, verify normalized snapshot provenance and source update/order information; simulate unavailable/malformed/partial input and verify failed or incomplete status with no successful partial snapshot.

### Tests for User Story 2

- [ ] T019 [P] [US2] Add parser and normalization tests against the synthetic Basic Register fixtures in `tests/unit/basic-register-normalization`.
- [ ] T020 [P] [US2] Add ingestion contract tests for complete, partial, malformed, and order-unknown source releases in `tests/contract/source-release-ingestion`.
- [ ] T021 [P] [US2] Add end-to-end ingestion tests that verify snapshot provenance and failure handling from synthetic release fixtures in `tests/integration/basic-register-to-snapshots`.

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement a Basic Register file reader and normalizer for the agreed source files and relevant fields in `backend/src/services/normalize-basic-register-release`.
- [ ] T023 [US2] Implement immutable raw-release capture with source identity, source order/reference, retrieval time, file names, checksums, and record locators in `backend/src/services/capture-source-release`.
- [ ] T024 [US2] Implement validation and explicit failed/incomplete outcomes for inaccessible, partial, malformed, or unorderable source data in `backend/src/services/ingest-source-release`.
- [ ] T025 [US2] Implement the n8n scheduled release-check and ingestion workflow with explicit failure reporting in `workflow/n8n/fimea-basic-register-ingestion.json`.
- [ ] T026 [US2] Connect complete release capture and normalization to the snapshot comparison flow in `backend/src/workflows/ingestion-to-review`.

**Checkpoint**: User Story 2 is demonstrable with a controlled release fixture and the scheduled workflow's documented trigger.

---

## Phase 5: User Story 3 - Avoid unsupported or duplicate review cases (Priority: P3)

**Goal**: Prevent cases from unsupported matches and ensure repeated processing cannot create duplicate cases.

**Independent Test**: Process a relevant change with no match, an ambiguous match, and one unique match twice; verify no cases for the first two and exactly one traceable NEW case for the unique match.

### Tests for User Story 3

- [ ] T027 [P] [US3] Add no-match, ambiguous-match, and replay/idempotency tests for change-to-case processing in `tests/unit/review-case-idempotency`.
- [ ] T028 [P] [US3] Add integration tests verifying repeat ingestion creates no duplicate cases and preserves the original evidence links in `tests/integration/idempotent-change-to-case`.

### Implementation for User Story 3

- [ ] T029 [US3] Implement explicit MATCHED, NO_MATCH, and AMBIGUOUS outcomes that preserve evidence classification in `backend/src/services/match-detected-changes`.
- [ ] T030 [US3] Enforce one case per detected-change and simulated-record pair during repeated processing in `backend/src/services/create-review-cases`.
- [ ] T031 [US3] Expose unmatched and ambiguous processing outcomes without creating review cases in `backend/src/api/change-processing-outcomes`.

**Checkpoint**: User Story 3 is demonstrable by replaying the same source fixture and checking all match outcomes.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify end-to-end quality, scope, and project documentation.

- [ ] T032 [P] Update `specs/001-ingestion-case-pipeline/quickstart.md` with the selected stack's prerequisites, runnable commands, and actual expected output.
- [ ] T033 [P] Verify all seeded/test/demo patient and medication data is simulated and contains no real patient-identifiable information in `tests/fixtures/`.
- [ ] T034 Run the complete manual end-to-end acceptance flow in `specs/001-ingestion-case-pipeline/quickstart.md` and record results in `specs/001-ingestion-case-pipeline/quickstart.md`.
- [ ] T035 Verify the pharmacist view and workflow do not diagnose, recommend treatment, select substitutions, determine urgency, autonomously change case status, or automatically close a case in `frontend/src/pages/open-review-cases` and `backend/src/workflows/ingestion-to-review`.
- [ ] T036 Review and align `specs/001-ingestion-case-pipeline/spec.md`, `specs/001-ingestion-case-pipeline/plan.md`, `specs/001-ingestion-case-pipeline/data-model.md`, and `specs/001-ingestion-case-pipeline/contracts/ingestion-and-case-view.md` with the implemented behavior.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; T001 must precede app skeleton and tool configuration.
- **Foundational (Phase 2)**: Depends on Setup; T004-T009 block implementation because source layout, relevant fields, fixtures, and evidence semantics inform all stories.
- **User Stories (Phase 3+)**: Depend on Foundational completion. US1 is MVP and uses release fixtures; it does not wait for live ingestion.
- **Polish (Phase 6)**: Depends on all user stories selected for delivery.

### User Story Dependencies

- **US1 (P1)**: Can start after foundational tasks; no dependency on US2. Provides a fixture-driven MVP.
- **US2 (P2)**: Can start after foundational tasks. T025 integrates its ingestion with the US1 processing path and requires US1's T014/T018.
- **US3 (P3)**: Extends the US1 matching/case creation path; requires US1's T015 and T018. It can overlap with US2 only on distinct files.

### Task Dependencies

- T001 → T002-T003.
- T004-T005 and T006-T009 complete before story implementation.
- US1: T010-T012 before T014-T018; T013 before T015; T014 before T015; T015-T016 before T018; T016 before T017.
- US2: T019-T021 before T022-T026; T022-T024 before T025; T018 and T025 before T026.
- US3: T027-T028 before T029-T031; T015/T018 before T030-T031.
- T032-T036 follow the selected implementation stories.

### Parallel Opportunities

- T003 can run parallel with T001 only if tooling selection is independent; otherwise start it after T001.
- T006 and T007 can run in parallel after fixture conventions are chosen.
- T010-T012 can be written in parallel because they target separate test files.
- T019-T020 and T027-T028 can be written in parallel within their phases.
- After foundational work, US1 and US2 may proceed in parallel on distinct files; US2's integration task T025 waits for the US1 pipeline.
- US3 tests can be authored alongside US2 work; US3 implementation must avoid concurrent edits to US1 service files.
- T032-T033 can run in parallel; final acceptance T034-T036 follows completed feature behavior.

## Parallel Example: User Story 1

```text
Task: T010 comparison/provenance tests in tests/unit/medicine-snapshot-comparison
Task: T011 supported matching/case tests in tests/unit/review-case-creation
Task: T012 open-case contract tests in tests/contract/open-review-cases
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup and Foundational phases, including the source/field/matching decisions and synthetic fixtures.
2. Complete User Story 1 from prior/current fixtures through one NEW case and the pharmacist-facing evidence view.
3. Run the independent US1 automated tests and manual fixture-based acceptance flow.
4. Stop and review the demonstrable vertical slice before adding live scheduled ingestion.

### Incremental Delivery

1. Add User Story 2 to ingest and retain the selected Basic Register releases.
2. Add User Story 3 to verify no-match, ambiguous-match, and replay/idempotency behavior.
3. Complete manual end-to-end, simulated-data, and safety checks in Polish.

### Parallel Team Strategy

Complete source/stack decisions and shared fixtures together first. Then assign US1 fixture-driven case review and US2 release acquisition to separate contributors. Integrate US2 only after US1's processing boundary is available. Assign US3 to a contributor after the case creation contract is stable.

## Notes

- Every task is a checkbox with a sequential ID; `[P]` is used only for independent files, and story labels appear only in user-story phases.
- Source and test code filenames use the language-specific extensions documented in `plan.md` by T001.
- Automated business-logic, contract, and integration tests are included because the project constitution requires them; the acceptance flow also includes manual end-to-end testing.
- Source release access, reuse terms, current file schema, release ordering, relevant fields, and identifier granularity must be verified before live ingestion; never invent source evidence.
