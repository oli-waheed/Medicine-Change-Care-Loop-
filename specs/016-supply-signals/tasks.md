# Feature 016: Tasks

**Status (2026-11-21)**: T001–T005 done; T006 is the user's approval and commit.

- [x] T001 Specify the feature; check the real shortage file (751 rows, one per VNR, `Valid` K 711 / E 40, shown as published).
- [x] T002 Shortage download timeline and stored-file reader (FR-002).
- [x] T003 Supply signals service and endpoints, scope guard (FR-001, FR-003–FR-005).
- [x] T004 "Supply signals" on the package and product pages (FR-006).
- [x] T005 Tests and verification: `tests/integration/supply-signals/`, `SupplySignals.test.tsx`; `python -m pytest` 356 passed; `npx vitest run` 128 passed; Ruff, type check, Oxlint, Prettier, build clean; real data (acceptance 2); browser check at 320–1440 px: no contrast failures, no horizontal overflow.
- [ ] T006 Obtain explicit approval before committing or pushing.
