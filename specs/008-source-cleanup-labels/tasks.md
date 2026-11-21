# Feature 008: Tasks

**Status (2026-11-21)**: T001–T009 done (T009 approved by Oli on 2026-11-21).

- [x] T001 Specify the feature from validation finding 3 (`spec.md`, `plan.md`, `contracts/cleanup-labels.md`).
- [x] T002 Implement the rules in `services/source_cleanup_labels.py` (FR-001–FR-003).
- [x] T003 Return the labels from both case endpoints (FR-004).
- [x] T004 Add the synthetic fixture `cleanup-release.xml` and tests: `tests/unit/test_source_cleanup_labels.py` (rules, edge cases, input not changed) and `tests/integration/source-cleanup-labels/` (real ingestion of three packages, status untouched, single-case answer).
- [x] T005 Frontend: list badge, set-aside switch, case notice, per-field marker, styles (FR-005, FR-006).
- [x] T006 Frontend tests `CleanupLabels.test.tsx` against responses captured from the real backend (`src/test/cleanupLabelResponses.json`); app scope test allows the new switch (FR-007).
- [x] T007 Verify: `python -m pytest` 306 passed; Ruff check and format clean; `npx vitest run` 96 passed; `npx tsc -b`, Oxlint, Prettier and `npm run build` clean; browser check at 320, 375, 768, 1024 and 1440 px: no contrast failures, no horizontal overflow.
- [x] T008 Documentation: README, roadmap, 007 spec marked superseded in part.
- [x] T009 Obtain explicit approval before committing or pushing. *(Approved by Oli on 2026-11-21. Checked beforehand with a copy of the real-data demo database: the Stapressial case (package 161367) shows "Active-substance fields only"; the other four demo cases have no label.)*
