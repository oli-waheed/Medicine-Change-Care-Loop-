---
description: "Task list for Application Shell and Open Review Cases Workspace"
---

# Tasks: Application Shell and Open Review Cases Workspace

**Input**: Design documents from `specs/003-app-shell-and-themes/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `contracts/app-shell-ui.md`, `quickstart.md`

**Tests**: Required by FR-029 and FR-030. Existing test assertions stay unchanged except the deliberate scope-test change in T006.

**Revision**: Revised on 2026-11-20 for the final design handoff (light only, handoff palette, case search, release labels, field indicators, tablet rail). Theme-switch tasks from the first draft were removed.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no unmet dependencies). **[Story]**: user story label.
- Run tests with `npx vitest run` (plain `npm test` stays in watch mode).

## Phase 1: Setup

- [x] T001 Confirm the baseline (branch `feature/application-shell-and-catalogue`, created from `main` at `48abcc2`): `git diff --ignore-cr-at-eol --stat` empty; 19 tests pass; build, lint, format clean. Record in `quickstart.md`.
- [x] T002 Add supersession notes for 002 FR-002 and FR-010 to `specs/002-case-review-readability/spec.md`, `plan.md` and `contracts/open-review-cases-ui.md`. (FR-027)

## Phase 2: Foundational

- [x] T003 Define light-only handoff tokens, base styles, focus ring, skip link and `.visually-hidden` in `frontend/src/index.css`. (FR-009, FR-010)
- [x] T004 [P] Add `__APP_VERSION__` (`frontend/vite.config.ts`, `frontend/src/env.d.ts`) and `frontend/src/app/appVersion.ts`. (FR-006)
- [x] T005 [P] Implement `frontend/src/app/navigation.ts`. (FR-003)
- [x] T006 Update `OpenReviewCasesPage.scope.test.tsx`: count case-selection buttons inside the "Open review cases" navigation and assert no other buttons; allow exactly one `input`, of type `search`; no `select`, `textarea` or `form`; re-check wording with a search active. (FR-029)

## Phase 3: User Story 1 — Move around the review workspace (P1) 🎯 MVP

- [x] T007 [P] [US1] `frontend/src/app/navigation.test.ts` and `appVersion.test.ts`.
- [x] T008 [P] [US1] `frontend/src/app/AppShell.test.tsx` (sidebar content, no switch, links, current page, tab title, back, Page not found, modified clicks, no extra requests).
- [x] T009 [P] [US1] `frontend/src/pages/about-data/AboutDataPage.test.tsx`.
- [x] T010 [US1] `Sidebar.tsx`, `AppShell.tsx`, `AppShell.css`, `icons.tsx` in `frontend/src/app/`. (FR-001, FR-002, FR-004, FR-014)
- [x] T011 [P] [US1] `frontend/src/pages/about-data/AboutDataPage.tsx` and `.css`. (FR-008)
- [x] T012 [P] [US1] `frontend/src/pages/not-found/NotFoundPage.tsx`. (FR-005)
- [x] T013 [US1] `frontend/src/App.tsx`: shell, page by path, tab title. (FR-003, FR-007)

## Phase 4: User Story 2 — Review changed and removed packages (P2)

- [x] T014 [US2] Add tests to `OpenReviewCasesPage.test.tsx`: layouts and kind badges, evidence fields visible for both kinds, empty before/after fallback, value-unavailable state, field indicators for all presence combinations, release labels. Confirm they fail on `main`.
- [x] T015 [US2] Extract `evidence/SourceValueDisplay.tsx` (value-unavailable, empty-list fallback), `evidence/EvidenceClassificationLabel.tsx`, `evidence/TimestampDisplay.tsx`, and add `evidence/FieldPath.tsx`. (FR-023, FR-024)
- [x] T016 [US2] Implement `changeIndicator.ts`, `UpdatedPackageReview.tsx`, `RemovedPackageReview.tsx`, `ProvenancePanel.tsx` and `CaseDetail.tsx`. (FR-019, FR-020, FR-022)
- [x] T017 [US2] Reduce `OpenReviewCasesPage.tsx` to loading, selection, states and composition; root `div`. (FR-026, FR-027)
- [x] T018 [US2] Restyle `OpenReviewCasesPage.css` with tokens only; merge duplicates; layouts, indicators, release labels; keep asserted class names. (FR-010, FR-019, FR-023)

## Phase 5: User Story 3 — Find and move through cases (P3)

- [x] T019 [US3] Add tests to `OpenReviewCasesPage.test.tsx`: search by name, identifier and summary with no extra request; "Showing n of N"; no-match message with details kept; arrow/Home/End focus movement without selection change.
- [x] T020 [US3] Implement search and keyboard movement in `CaseList.tsx`, with styles in `OpenReviewCasesPage.css`. (FR-016, FR-017, FR-018)

## Phase 6: User Story 4 — Tablet, phone and keyboard (P4)

- [x] T021 [US4] Extend `AppShell.test.tsx`: skip link first; no focus move on first load; Menu toggle (focus to first link, inert main, Escape, re-click); Tab trap; link closes; scrim closes; tablet "Sidebar" toggle.
- [x] T022 [US4] Implement `useNavigationDrawer.ts` (opener-aware) and the drawer, rail and persistent layouts in `AppShell.css`. (FR-011–FR-013)
- [x] T023 [US4] Verify and adjust 320–1023 px layouts in all stylesheets. (FR-015)

## Phase 7: Polish & cross-cutting

- [x] T024 `frontend/src/app/App.scope.test.tsx` and `frontend/src/test/clinicalWords.ts`: allowed controls and wording on every page, with a search active and with the navigation open. (FR-025, SC-009)
- [x] T025 [P] Update the root `README.md` "Application Interface" section.
- [x] T026 Run the automated checks and record results in `quickstart.md`. (SC-007)
- [ ] T027 Manual checks 1–10 in `quickstart.md`. (Steps 1–9 done and recorded; step 10, the timed scan by a team member, is open.) (SC-001–SC-006, SC-008)
- [x] T028 Run `/speckit-converge`; record findings; resolve or document every gap. (Done 2026-11-20; see Phase 8.)
- [x] T029 Review commit `16927e2` against the spec: restore About the Data (handoff acceptance criterion) and the original evidence-unavailable banner wording and its 002 test; fix formatting, BOM and encoding issues; stop exporting a helper from `CaseList.tsx` (lint); add the missing plan, tasks, research, contract, quickstart and checklist; add the 002 supersession notes. (FR-008, FR-023, FR-027, FR-029)

## Dependencies & Execution Order

- T001 → T002 → Phase 2 (T003; T004, T005, T006 in parallel) → stories.
- US1 needs T003–T005. US2 needs T003 and T006. US3 needs T017. US4 needs T010.
- Polish needs all stories. Within each story: tests first, confirm they fail, implement, confirm they pass.

## Implementation Strategy

1. MVP: Phases 1–3 (shell around the unchanged case page).
2. Then US2 (layouts and indicators), US3 (search and queue keyboard), US4 (tablet, phone, keyboard).
3. Finish with the app-level scope test, README, verification and convergence.

## Phase 8: Convergence

Run on 2026-11-20 against `main` (`d572cde`) by following `.github/skills/speckit-converge/SKILL.md` step by step (read-only). The Copilot Agent run gave an unreliable result, so it was not used. Result: 2 LOW findings, both in the spec text; no code gaps.

- [x] T030 F1 (FR-021, partial, LOW): add the search placeholder, the sidebar tooltips and the navigation link names to FR-021's list of new texts.
- [x] T031 F2 (spec header, partial, LOW): correct the reference to the allowed-controls requirement from FR-022 to FR-025.
