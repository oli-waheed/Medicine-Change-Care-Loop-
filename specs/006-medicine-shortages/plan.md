# Feature 006: Implementation Plan

## Backend

- **Storage** (`backend/src/models`, `PipelineStore`): `shortage_captures` (one row per distinct content: checksum, status, address, file path, size, row count, first and last download, failure reason), `shortage_retrievals` (every download) and `daily_update_runs` (date, trigger, times, outcome). New tables are created automatically by the existing `create_all`; no existing table changes.
- **Raw files**: `<storage>/../shortages/<sha256>.txt` next to the source-release captures (`backend/data/shortages`, or `backend/data/real/shortages` with the real-data settings), written once and verified before reading.
- **Parser and update** (`backend/src/services/medicine_shortages.py`): strict CSV parsing (FR-002), `store_shortage_file()`, `update_shortages()` reusing feature 005's `download_release()`, and `ShortageUpdate` (one background update at a time) for the button and the schedule.
- **Catalogue matching**: `MedicineCatalogueService.cached_baseline()` returns the baseline only if already in memory (never blocks), `warm_in_background()` prepares it, `packages_by_vnr()` indexes it. This keeps the shortage list fast while the 190 MB release is being reconstructed (about 35 s).
- **Daily update** (`backend/src/services/daily_updates.py`, `api/daily_updates.py`): a daemon thread started in the FastAPI lifespan checks every minute; from `DAILY_UPDATE_TIME` it runs shortages then the feature 005 check, recording the run first so a restart does not repeat it. Tests set `DAILY_UPDATE_TIME=off` in `tests/conftest.py`; a directly built `ApplicationConfig` has no schedule.
- **API** (`api/medicine_shortages.py`, `api/daily_updates.py`): contract in `contracts/shortages-api.md`. `start_latest_release_check(app)` is shared by the button of 005 and the schedule.

## Frontend

- `pages/medicine-shortages/`: `shortagesApi.ts`, `ShortageUpdatePanel.tsx` (button, polling, daily line), `MedicineShortagesPage.tsx` (source summary, notice, search, status filter, table, paging; requests keyed so newer requests show as loading; retries every 5 s while the catalogue is loading), `MedicineShortagesPage.css` (reuses the catalogue layout and tokens).
- Navigation: "Medicine Shortages" at `/medicine-shortages` with a warning-triangle icon. About the Data names the shortage file under Source data.

## Decisions

- The open-data file, not the RSS feed: structured, complete, and licensed as open data.
- Values are shown as published; `Valid` is shown as the letter with Fimea's description, without deriving a status from dates.
- Only the latest accepted file is listed; earlier files remain stored for traceability.
- The daily update lives in the backend because the user asked for it to run without n8n; the n8n workflow keeps working unchanged.

## Risks

- The daily Basic Register check downloads 190 MB and needs about 2.3 GB of memory while reconstructing; it runs at most once a day.
- If Fimea changes the file's columns, updates fail with the reason and the previous list stays.
