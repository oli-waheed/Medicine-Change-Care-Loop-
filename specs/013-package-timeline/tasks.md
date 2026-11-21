# Feature 013: Tasks

**Status (2026-11-21)**: T001–T006 done; T007 is the user's approval and commit.

- [x] T001 Specify the feature (`spec.md`, `plan.md`, `contracts/package-history-api.md`).
- [x] T002 Tables and `PipelineStore` methods for package history.
- [x] T003 Record history with each ingestion; complete older pairs in the daily update (FR-001–FR-003).
- [x] T004 History endpoint and backend scope guard (FR-004).
- [x] T005 Package page "Change history" (FR-005).
- [x] T006 Tests and verification: `tests/integration/package-history/`, `PackageHistory.test.tsx`; `python -m pytest` 337 passed; `npx vitest run` 117 passed; Ruff, type check, Oxlint, Prettier, build clean; real pair backfilled (2,918 events, 37 s); browser check at 320–1440 px with packages 161367 and 200509: no contrast failures, no horizontal overflow.
- [ ] T007 Obtain explicit approval before committing or pushing.
