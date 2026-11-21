# Feature 015: Tasks

**Status (2026-11-21)**: T001–T006 done; T007 is the user's approval and commit.

- [x] T001 Specify the feature (`spec.md`, `plan.md`, `contracts/links-api.md`).
- [x] T002 Read the holder into authorisation records; keep it out of change detection (FR-005).
- [x] T003 Link index and groups (`services/medicine_links.py`) (FR-002, FR-003).
- [x] T004 Package and product link endpoints, scope guard (FR-001, FR-004).
- [x] T005 "Linked records" on the package and product pages, folding long groups (FR-006).
- [x] T006 Tests and verification: synthetic links release and `tests/integration/medicine-links/`; `LinkedRecords.test.tsx`; `python -m pytest` 349 passed; `npx vitest run` 123 passed; Ruff, type check, Oxlint, Prettier, build clean; real release: first request about 1 s, later about 0.01 s; browser check at 320–1440 px: no contrast failures, no horizontal overflow.
- [ ] T007 Obtain explicit approval before committing or pushing.
