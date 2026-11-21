# Feature 005: Tasks

**Status (2026-11-21)**: T001–T012 done; T013 is the user's approval and commit.

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
- [ ] T013 Obtain explicit approval before committing or pushing.
