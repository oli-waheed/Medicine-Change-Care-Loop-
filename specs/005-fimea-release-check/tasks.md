# Feature 005: Tasks

**Status (2026-11-21)**: T001–T012 done; T013 is the user's approval and commit. Convergence (Phase 2) found one LOW spec-text item, T014.

- Backend: shared `ingest_release_file()` used by the upload endpoint and the check; `LatestReleaseCheck` service; `GET`/`POST /api/source-releases/latest-check`; `FIMEA_RELEASE_URL`. 9 new integration tests; full backend suite 236 passed; Ruff check and format clean.
- Frontend: "Fimea release updates" on About the Data. 6 new tests; 75 frontend tests passed; TypeScript, Oxlint, Prettier and build clean.
- End to end with the real release (2026-10-06, 190 MB) served locally in place of Fimea: first check 69 s, "New release loaded: release date 2026-10-06"; second check "No new release"; the catalogue then loaded in 2.1 s instead of about 36 s.

## Tasks

- [x] T001 Specify the feature (`spec.md`, `contracts/latest-release-check-api.md`, `plan.md`).
- [x] T002 Move the upload endpoint's ingestion into `backend/src/workflows/ingest_release_file.py`; the endpoint calls it. *(Existing ingestion tests pass unchanged except one monkeypatch target, now the shared module.)*
- [x] T003 Add `FIMEA_RELEASE_URL` to `backend/src/config.py`.
- [x] T004 Implement `LatestReleaseCheck` and `download_release()` in `backend/src/services/latest_release_check.py` (FR-003, FR-005–FR-007).
- [x] T005 Add `GET`/`POST /api/source-releases/latest-check` (`backend/src/api/latest_release_check.py`, `main.py`); share `catalogue_service(app)` with the catalogue API.
- [x] T006 Update the backend clinical-scope guard with the two operations (FR-010).
- [x] T007 Integration tests `tests/integration/latest-release-check/test_latest_release_check_api.py`: idle state, new release with catalogue prepared, unchanged file not stored twice, newer release creates the same cases as an upload, download failure, file not accepted, one check at a time, no clinical wording, download streaming and size limit.
- [x] T008 Frontend client `releaseCheckApi.ts` and section `LatestReleaseCheck.tsx` on About the Data, with styles (FR-001, FR-002, FR-007, FR-008).
- [x] T009 Frontend tests `LatestReleaseCheck.test.tsx`: no request before pressing; progress and new release; no new release; failure alert; following a running check; backend unreachable. App scope test allows the one button (FR-010).
- [x] T010 Verify: `python -m pytest` 236 passed; Ruff clean; `npx vitest run` 75 passed; `npx tsc -b`, Oxlint, Prettier, `npm run build` clean.
- [x] T011 Browser check of About the Data at 320, 768 and 1440 px: no contrast failures, no horizontal overflow; real-release end-to-end run as in the status above.
- [x] T012 Documentation: README (feature, endpoints, `FIMEA_RELEASE_URL`, test counts); 003 spec marked superseded in part.
- [x] T013 Obtain explicit approval before committing or pushing. *(Approved by Oli on 2026-11-21 after the Phase 2 convergence review; T014 remains open.)*

## Phase 2: Convergence

Run on 2026-11-21 against `main` (`31e58fe`) by following `.github/skills/speckit-converge/SKILL.md` step by step (read-only assessment of FR-001–FR-010, the acceptance criteria, the plan and the constitution). Re-verified on that commit: `python -m pytest` 262 passed, `npx vitest run` 84 passed, TypeScript, Oxlint, Prettier and build clean.

Real-data evidence: on the user's computer the app downloaded Fimea's release of 2026-11-21 (200,598,770 bytes) into the real-data database at 12:22 (Helsinki) and compared it with the 2026-10-06 release; a later download of the same file was recognised as already captured (`docs/validation/2026-11-21-real-release-comparison.md`).

Requirements: FR-001–FR-010 and acceptance criteria 1–6 are met; no code gaps. One finding, in the spec text:

- [ ] T014 F1 (spec §2 "Out of scope", LOW): "Scheduling (the n8n workflow remains the daily, automatic route)" is superseded by feature 006, which added the backend's daily update using this check. Add a "Superseded in part by `specs/006-medicine-shortages`" note to the spec header.

Related, outside this feature's code: the "table already exists" error when several first requests reach a new database was fixed in `31e58fe` (`PipelineStore`, test `tests/unit/test_pipeline_store_first_use.py`).
