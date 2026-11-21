# Feature 006: Tasks

**Status (2026-11-21)**: T001–T015 done (T015 approved by Oli on 2026-11-21). From the convergence review, T017 is resolved; T016 (scheduler) and T018 (VNR comparison) await team decisions.

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
- [x] T015 Obtain explicit approval before committing or pushing. *(Approved by Oli on 2026-11-21 after the Phase 2 convergence review; T016-T018 remain open.)*

## Phase 2: Convergence

Run on 2026-11-21 against `main` (`31e58fe`) by following `.github/skills/speckit-converge/SKILL.md` step by step (read-only assessment of FR-001–FR-011, the acceptance criteria, the plan and the constitution). Re-verified on that commit: `python -m pytest` 262 passed, `npx vitest run` 84 passed, TypeScript, Oxlint, Prettier and build clean.

Real-data evidence: on the user's computer the daily update ran on 2026-11-21 at 13:03 (Helsinki) against Fimea itself: the shortage file was downloaded and accepted (751 shortages, 64,454 bytes) and the Basic Register check found the 2026-11-21 release already captured. A demo database built from the two real releases with fictional records produced 5 review cases.

Requirements: FR-001–FR-011 and acceptance criteria 1–5 are met; no code gaps against the spec. Findings:

- [ ] T016 F1 (plan "Decisions", constitution "Decisions … must be recorded with rationale", MEDIUM): two daily schedulers now download the Basic Register at 06:00, the backend's (this feature) and the n8n workflow (`workflow/n8n/fimea-basic-register-ingestion.json`, `"active": true`). Duplicate detection prevents double storage, but the 190 MB file is downloaded twice. Record the team's decision on the primary scheduler; if it is the backend, deactivate the n8n trigger and update the README "Source Ingestion Workflow".
- [x] T017 F2 (FR-010, LOW): on Windows the schedule shows the time-zone name as "FLE Standard Time" instead of a short name. Show the UTC offset (for example "UTC+02:00") instead. *(Done: `utc_offset()` in `backend/src/api/daily_updates.py`; contract, fixture and page test updated.)*
- [ ] T018 F3 (spec §1 objective and the validation report, LOW): shortages are linked by VNR, but change detection does not compare VNR (269 packages changed VNR between the real releases of 2026-10-06 and 2026-11-21). Record the decision on whether VNR becomes a compared field; this belongs to the comparison of feature 001, not to this feature's code.

Related, outside this feature's code: the "table already exists" error when the Shortages page's first requests reach a new database together was fixed in `31e58fe`.
