# Feature 011: Tasks

**Status (2026-11-21)**: T001–T005 done; T006 is the user's approval and commit.

- [x] T001 Specify the feature (`spec.md`, `plan.md`, `contracts/exports-api.md`); choose semicolons and a byte-order mark for Excel with Finnish settings.
- [x] T002 Implement both exports (`api/exports.py`) and allow them in the backend scope guard (FR-001–FR-004).
- [x] T003 Add the download links to the case page (FR-005).
- [x] T004 Tests: `tests/integration/exports/test_exports_api.py`, `ExportLinks.test.tsx`, app scope test.
- [x] T005 Verify: `python -m pytest` 332 passed; Ruff clean; `npx vitest run` 104 passed; type check, Oxlint, Prettier, build clean; with the real-data demo database both files download and open as 18 and 8 columns; no contrast failures or horizontal overflow at 320–1440 px.
- [ ] T006 Obtain explicit approval before committing or pushing.
