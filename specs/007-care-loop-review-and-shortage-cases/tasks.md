# Feature 007: Tasks

**Status (2026-11-21)**: T001–T015 done (T015 approved by Oli on 2026-11-21 after trying the review flow).

- Backend: review statuses, transitions and history; review endpoint; reviewed filter; column migration for existing databases; shortage comparison, matching and cases; 24 new tests (`tests/integration/case-review/`); full suite 286 passed; Ruff clean.
- Frontend: review panel, status labels, "Show reviewed cases", shortage case layout; 7 new tests and two scope tests updated on purpose; 91 frontend tests passed; TypeScript, Oxlint, Prettier and build clean.
- Browser: release and shortage cases at 320–1440 px without contrast failures or horizontal overflow; a full review (in progress, follow-up needed, show reviewed, history) recorded against a live backend; the real-data demo database from before this feature opened, gained the new columns and accepted a review step.

## Tasks

- [x] T001 Write and approve the spec (decisions D1–D3, 2026-11-21).
- [x] T002 Statuses, transitions and event validation (`domain/case_status_event`).
- [x] T003 Event columns and their migration for existing databases; `record_status_event()` with the expected-status check; `case_payloads()` with history (`services/pipeline_store.py`, `models`).
- [x] T004 `POST /api/review-cases/{caseId}/status-events`; `includeReviewed` on the case list (`api/review_cases.py`, `api/open_review_cases.py`, `main.py`).
- [x] T005 Shortage comparison and matching (`services/shortage_review_cases.py`).
- [x] T006 Compare the active shortage files after each download and store cases and outcomes (`update_shortages(review=…)`, `api/medicine_shortages.py`, `api/daily_updates.py`, `PipelineStore.record_shortage_review()`); shortage files count for evidence availability.
- [x] T007 Update the backend guards on purpose: one new operation, four statuses, a single caller of `record_status_event`.
- [x] T008 Backend tests: review steps, history, reviewed filter, every rejected step, stale status, unknown case, later releases, migration (`test_case_review_api.py`); baseline file, changed/started/ended, returning file, replays, no catalogue, ambiguous and no-package outcomes, reviewing a shortage case, unavailable evidence (`test_shortage_review_cases.py`); fixture `shortages-third.txt`.
- [x] T009 Frontend types and client (`openReviewCases.ts`), `ReviewPanel.tsx`, `ShortageCaseReview.tsx`, `CaseDetail.tsx`, `CaseList.tsx`, `OpenReviewCasesPage.tsx`, `changeSummary.ts`, styles.
- [x] T010 Frontend tests (`CaseReview.test.tsx`, responses captured from the backend in `src/test/caseReviewResponses.json`); page and app scope tests updated on purpose; empty-state text "There are no open review cases."
- [x] T011 Verify: `python -m pytest` 286 passed; Ruff clean; `npx vitest run` 91 passed; `npx tsc -b`, Oxlint, Prettier, `npm run build` clean.
- [x] T012 Browser and real-data checks as in the status above.
- [x] T013 Documentation: contract, plan, README; 001, 002, 003 and 006 specs marked superseded in part.
- [x] T014 Convergence review against the spec: FR-001–FR-016 and acceptance criteria 1–5 met; acceptance criterion 5's real-data demo was checked with a copy of the demo database. No gaps found.
- [x] T015 Obtain explicit approval before committing or pushing. *(Approved by Oli on 2026-11-21.)*
