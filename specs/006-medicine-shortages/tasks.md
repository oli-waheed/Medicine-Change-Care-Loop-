# Feature 006: Tasks

**Status (2026-11-21)**: T001–T014 done; T015 is the user's approval and commit.

- Backend: shortage storage, parser, update and list API; daily automatic update; 25 new tests (`tests/integration/medicine-shortages/`); full backend suite 261 passed; Ruff check and format clean.
- Frontend: Medicine Shortages page with Update button and daily status; 8 page tests and a scope test; 84 frontend tests passed; TypeScript, Oxlint, Prettier and build clean.
- Real data (Fimea `Shortages.txt` of 2026-11-20, 751 rows, served locally in place of Fimea, with the real 2026-10-06 release): the backend started after the set time ran the daily update at once (shortages stored; Basic Register already captured); the list loaded in 0.4–0.7 s with packages for the matching VNRs; searches answered in under 0.01 s; no contrast failures or horizontal overflow at 320–1440 px.

## Tasks

- [x] T001 Inspect the real shortage file and specify the feature (`spec.md` §2, `contracts/shortages-api.md`, `plan.md`).
- [x] T002 Add tables `shortage_captures`, `shortage_retrievals`, `daily_update_runs` and their `PipelineStore` methods.
- [x] T003 Add `FIMEA_SHORTAGES_URL`, `DAILY_UPDATE_TIME` and the shortage storage folder to `config.py`.
- [x] T004 Implement the parser, storage and update (`services/medicine_shortages.py`) (FR-001–FR-003, FR-008).
- [x] T005 Add catalogue matching by VNR without waiting (`cached_baseline`, `warm_in_background`, `packages_by_vnr`) (FR-005).
- [x] T006 Add `GET /api/shortages`, `GET`/`POST /api/shortages/update` (FR-004–FR-008).
- [x] T007 Implement the daily update (`services/daily_updates.py`, `api/daily_updates.py`, lifespan in `main.py`; `start_latest_release_check(app)` shared with 005) and `GET /api/daily-updates` (FR-009, FR-010).
- [x] T008 Update the backend clinical-scope guard; switch the schedule off in tests (`tests/conftest.py`) (FR-011).
- [x] T009 Synthetic fixtures `tests/fixtures/fimea-shortages/` (CRLF kept via `.gitattributes`) and integration tests: format, rejected files, first download, matching, not waiting for the catalogue, unchanged file, later file, failures keep the list, tampered file, paging, no case changes, schedule once a day, restart, failure recorded, lifespan.
- [x] T010 Frontend: navigation item and icon, `MedicineShortagesPage`, `ShortageUpdatePanel`, `shortagesApi.ts`, styles; About the Data names the shortage file.
- [x] T011 Frontend tests: navigation, listing as published, notice, search and filter, update flow, failed update, daily line, no data yet, catalogue loading then ready; app scope test for the page; navigation and shell tests for four links.
- [x] T012 Verify: `python -m pytest` 261 passed; Ruff clean; `npx vitest run` 84 passed; `npx tsc -b`, Oxlint, Prettier, `npm run build` clean.
- [x] T013 Browser check with the real file and release at 320, 375, 768, 1024 and 1440 px.
- [x] T014 Documentation: README (feature, endpoints, settings, daily update, test counts); 003 spec marked superseded in part.
- [ ] T015 Obtain explicit approval before committing or pushing.
