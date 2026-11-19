---
description: "Task list for Open Review Case Readability"
---

# Tasks: Open Review Case Readability

**Input**: Design documents from `specs/002-case-review-readability/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/open-review-cases-ui.md`, and `quickstart.md`

**Tests**: Automated tests are required by FR-017 for timestamp fallback and all four evidence classifications. Existing test assertions must remain unchanged.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other marked tasks because it touches different files and has no unmet dependencies.
- **[Story]**: Maps a task to its user story; setup, foundational, and polish tasks have no story label.
- Every task names the file or files it changes or validates.

## Phase 1: Setup

**Purpose**: Establish a passing baseline before changing the frontend.

- [ ] T001 Run the existing frontend test suite with `npm test -- --run` and the build as defined in `frontend/package.json` before making changes.

---

## Phase 2: Foundational

**Purpose**: Replace starter-wide styling and remove unused starter files before page-specific work.

- [ ] T002 [P] Replace Vite starter rules in `frontend/src/index.css` with the page's global light baseline, set `color-scheme: light`, and ensure the page remains readable when the OS requests dark colors.
- [ ] T003 [P] Remove the unreferenced starter files `frontend/src/App.css`, `frontend/src/assets/vite.svg`, `frontend/src/assets/react.svg`, and `frontend/src/assets/hero.png`; preserve the referenced `frontend/public/favicon.svg`.

**Checkpoint**: The app has a light global baseline, no unused starter styles/assets, and its existing favicon remains available.

---

## Phase 3: User Story 1 - Scan a case and its evidence (Priority: P1) 🎯 MVP

**Goal**: Make selected cases, changed values, classifications, and evidence states easy to scan without altering existing wording or case behavior.

**Independent Test**: With simulated case fixtures, verify all four classifications are explicit and distinguishable without color alone; unavailable evidence retains its qualification wording and looks like a warning; missing, empty, and no-occurrence values are distinguishable; existing text and selection behavior remain intact.

### Tests for User Story 1

- [ ] T004 [US1] Add automated assertions for all four evidence classifications, unavailable-evidence warning presentation, and missing/empty/no-occurrence distinctions in `frontend/src/pages/open-review-cases/OpenReviewCasesPage.test.tsx`, leaving existing assertions unchanged.

### Implementation for User Story 1

- [ ] T005 [US1] Update `frontend/src/pages/open-review-cases/OpenReviewCasesPage.tsx` to retain existing case selection and wording, add the simulated-record notice, and distinguish classifications, unavailable evidence, and missing/empty/no-occurrence values without adding case actions or clinical wording; ensure the header and notice contain no words matched by `CLINICAL_WORDS` in `frontend/src/pages/open-review-cases/OpenReviewCasesPage.scope.test.tsx`.
- [ ] T006 [US1] Style the page header, cards, selected case, before/after groups, classification labels, unavailable warnings, value-state indicators, and loading/error/empty states in `frontend/src/pages/open-review-cases/OpenReviewCasesPage.css`.

**Checkpoint**: A pharmacist can scan a selected simulated case and identify its changed values, evidence classifications, and unavailable or absent-value states.

---

## Phase 4: User Story 2 - Keep case context while reading (Priority: P2)

**Goal**: Keep the list and details usable across mobile, intermediate, and wide viewports.

**Independent Test**: At 320–767 pixels, verify the list and details remain readable without horizontal overflow; at 768–1023 pixels, verify they remain side by side in normal flow; at 1024 pixels and wider, scroll details and verify the list remains visible.

### Implementation for User Story 2

- [ ] T007 [US2] Implement the responsive case layout in `frontend/src/pages/open-review-cases/OpenReviewCasesPage.css`: stack the list and details at 320–767 pixels, keep them side by side without stickiness at 768–1023 pixels, and keep the case list visible during detail scrolling at 1024 pixels and wider.

**Checkpoint**: The page uses the specified layout at all three viewport ranges without overlap or horizontal page overflow.

---

## Phase 5: User Story 3 - Read source metadata and timestamps (Priority: P3)

**Goal**: Make timestamps and source references readable while preserving exact recorded values and the meaningful page identity.

**Independent Test**: Verify valid timestamps display as `YYYY-MM-DD HH:MM UTC`, show the exact recorded value as small muted text next to the time, and retain the original value in the `dateTime` attribute; missing or invalid timestamps retain existing fallback behavior. Verify the browser tab title and monospace source references.

### Tests for User Story 3

- [ ] T008 [US3] Create `frontend/src/pages/open-review-cases/timestamp.test.ts` with unit tests for valid UTC, valid `+02:00` offset, invalid, and missing timestamp inputs.

### Implementation for User Story 3

- [ ] T009 [P] [US3] Set a meaningful Open Review Cases and project title in `frontend/index.html`.
- [ ] T010 [US3] Implement the timestamp formatter in `frontend/src/pages/open-review-cases/timestamp.ts` and use it in `frontend/src/pages/open-review-cases/OpenReviewCasesPage.tsx` to render valid values as `YYYY-MM-DD HH:MM UTC` in `<time>` elements, keep the exact original in `dateTime`, show it as small muted text beside the time, and preserve existing fallbacks without adding a control.
- [ ] T011 [US3] Style the always-visible exact timestamp text as small and muted, with no focus/tap reveal interaction, and apply monospace styling to checksums, file names, and record locators in `frontend/src/pages/open-review-cases/OpenReviewCasesPage.css`.

**Checkpoint**: Timestamp values are deterministic and accessible without hover; source references and the page title meet the UI contract.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate that the integrated page meets the spec and preserves existing behavior.

- [ ] T012 [P] Manually verify the specified viewport ranges, dark OS text contrast, that the exact timestamp is always visible without a focus/tap control, and that a team member acting as the pharmacist can identify the selected case, every changed field's before/after values, and all evidence classifications within 30 seconds without assistance; also verify existing text, warnings, and the retained favicon using `specs/002-case-review-readability/quickstart.md`.
- [ ] T013 [P] Run `npm test -- --run`, build, lint, and format checks from `frontend/package.json`; confirm existing test assertions and dependency manifests remain unchanged.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; T001 establishes the baseline.
- **Foundational (Phase 2)**: T002 and T003 depend on T001 and can run in parallel.
- **User Story 1 (Phase 3)**: Depends on the foundational styles and cleanup; T004 tests precede T005 and T006.
- **User Story 2 (Phase 4)**: Depends on the foundation and T006 because it extends the same page stylesheet.
- **User Story 3 (Phase 5)**: Timestamp tests depend on the foundation; T010 follows T008, and T011 follows T010 and T007 because both stories update the page stylesheet. T009 is independent of timestamp rendering.
- **Polish (Phase 6)**: T012 and T013 depend on all implementation tasks and can run in parallel.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2; no dependency on another user story.
- **User Story 2 (P2)**: Can start after Phase 2; its shared stylesheet work follows User Story 1 styling to avoid concurrent edits.
- **User Story 3 (P3)**: Can start after Phase 2; timestamp tests and the title update can proceed independently, while its stylesheet work follows the other page-style tasks.

### Within Each User Story

- Add requested tests before their implementation and verify the new assertions fail for the missing behavior.
- Implement markup before styling that depends on its classes or states.
- Preserve existing test assertions, API behavior, and case-selection behavior.
- Complete each story's independent test before treating that story as done.

### Parallel Opportunities

- T002 and T003 can run in parallel after T001 because they modify different files.
- T009 can run in parallel with independent timestamp utility work because `frontend/index.html` is separate from `frontend/src/pages/open-review-cases/timestamp.ts` and `frontend/src/pages/open-review-cases/timestamp.test.ts`.
- T012 and T013 can run in parallel after implementation because manual browser validation and automated checks do not modify the same files.

---

## Parallel Examples

### User Story 1

T004 is test-first and must complete before T005/T006. Keep the markup and dependent styles in sequence; there are no safe parallel implementation tasks within this story.

### User Story 2

After T006, finish T007 before T011 because both change `frontend/src/pages/open-review-cases/OpenReviewCasesPage.css`. The timestamp formatter and its tests use separate files from the responsive layout.

### User Story 3

Complete T008 before T010. T009 may run in parallel with T010 because the page title and timestamp formatter use separate files. Complete T011 after T007 and T010; the exact recorded value remains visible beside the formatted time without an interaction.

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete T001–T003 to establish a passing baseline and remove global starter styling.
2. Complete T004–T006 to make cases and evidence scannable.
3. Validate User Story 1 independently, including all classification and evidence-state tests.

### Incremental Delivery

1. Deliver the P1 case/evidence presentation.
2. Add the P2 responsive list and detail layout.
3. Add the P3 timestamp presentation, exact-value access, source-reference styling, and page title.
4. Run the final browser and automated checks in Phase 6.

---

## Format Validation

- Task IDs are sequential from T001 through T013.
- Each task is an unchecked checklist item with an ID, an optional `[P]` marker, a required story label only in user-story phases, and an explicit file path.
- Setup, foundational, and polish tasks have no story label.
- Every user story has a goal and an independent test criterion.
