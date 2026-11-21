# Feature 010: Tasks

**Status (2026-11-21)**: T001–T008 done; T009 is the user's approval and commit.

- [x] T001 Specify the feature (`spec.md`, `plan.md`, `contracts/source-history-api.md`); check the limits against the real pair.
- [x] T002 Table `release_quality_checks` and `PipelineStore` methods (`record_quality_check`, `quality_check_payloads`, `compared_release_pairs`, `shortage_captures`, `capture_files`).
- [x] T003 `build_quality_check()` and storing it with each ingestion (FR-001–FR-003).
- [x] T004 Backfill in the daily update (FR-004).
- [x] T005 `GET /api/source-history` and the backend scope guard (FR-005).
- [x] T006 Tests: `tests/integration/source-history/` (empty, releases and downloads, automatic check, unchanged pair, clean-up counts, backfill once, read-only, shortage files).
- [x] T007 Frontend page, navigation, tests (`SourceHistoryPage.test.tsx`, app scope, shell and navigation tests) (FR-006).
- [x] T008 Verify: `python -m pytest` 323 passed; Ruff clean; `npx vitest run` 103 passed; type check, Oxlint, Prettier, build clean; real pair backfilled and checked (acceptance 2); browser check at 320–1440 px with the real data: no contrast failures, no horizontal overflow.
- [ ] T009 Obtain explicit approval before committing or pushing.
