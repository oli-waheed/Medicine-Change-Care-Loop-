# Feature 006: Medicine Shortages and the Daily Automatic Update

**Status:** Approved specification (requested by Oli on 2026-11-21: shortage information, updated automatically every day by the backend, with an update button, shown on a new Shortages page)
**Branch:** feature/medicine-shortages

**Supersedes in part:** `specs/003-app-shell-and-themes` FR-001 and FR-002 (the sidebar also lists "Medicine Shortages", between "Medicine Catalogue" and "About the Data") and FR-025 (the Shortages page adds its search field, status filter, paging and the "Update shortage data" button). No case actions or clinical wording are added; features 003–005 otherwise stay in force.

**Superseded in part by:** `specs/007-care-loop-review-and-shortage-cases` — §3 "Out of scope: linking shortages to review cases": changes between accepted shortage files now create review cases for matched records.

## 1. Objective

Show the medicine shortages that marketing authorisation holders report to Fimea, as Fimea publishes them in its open data, next to the matching packages of the Medicine Catalogue, and keep both the shortage data and the Basic Register up to date automatically every day.

## 2. Source

Fimea open data, `https://data.pilvi.fimea.fi/avoin-data/Shortages.txt`, licensed CC BY 4.0, published daily. Inspected on 2026-11-21 (64,454 bytes, 751 rows):

- UTF-8 text, CRLF line endings, `;` separated, every value in double quotes, one header row.
- Columns: `NordicArticleNumber` (the VNR), `Valid` (`K` or `E` in the inspected file), `UnavailableFrom`, `EndingDate`, `DateOfTheNotification`, `Updated` (all `YYYY-MM-DD`), `Company`.
- One row per VNR. 747 of the 751 VNRs match a package of the 2026-10-06 Basic Register.
- Fimea describes `Valid` as whether the shortage is ongoing; in the inspected file every `K` row had started and every `E` row starts later. The page shows the published letter with that description ("K (ongoing: yes)", "E (ongoing: no)") and no further interpretation.

## 3. Scope

### In scope
- Download, check and store the shortage file, once per content, with every download recorded.
- A "Medicine Shortages" page: source summary, the list in the file's order, search, status filter, paging, packages matched by VNR from the active catalogue release.
- An "Update shortage data" button.
- A daily automatic update in the backend for the shortage file and the Basic Register (the feature 005 check).

### Out of scope
- Linking shortages to review cases, or creating cases from shortages.
- Suggesting other products, judging the effect of a shortage, or any clinical wording.
- Shortage history across files (only the latest accepted file is listed; earlier files stay stored).
- The RSS feed of Fimea's shortage search (the open-data file holds the same shortages in a structured form).

## 4. Functional requirements

- **FR-001**: The backend MUST download the shortage file from `FIMEA_SHORTAGES_URL` (default the address above), within `MAX_SOURCE_RELEASE_UPLOAD_BYTES`.
- **FR-002**: A file MUST be accepted only if it is UTF-8, has exactly the seven columns in order, seven values on every row, a VNR on every row, no repeated VNR, and `YYYY-MM-DD` or empty dates. Other files MUST be stored as FAILED with the reason and never shown.
- **FR-003**: Each distinct file content MUST be stored once, named by its SHA-256 checksum, and verified against it before it is shown; every download MUST be recorded with its time.
- **FR-004**: The list MUST show the latest downloaded accepted file, rows in the file's order and values exactly as published (an empty value as "Empty in source").
- **FR-005**: Each shortage MUST show the packages of the active catalogue release with the same VNR, or say that none has it. The list MUST NOT wait for the catalogue to be prepared; it shows the shortages at once and adds packages when ready.
- **FR-006**: Users MUST be able to search by product name, VNR or company and filter by the published `Valid` value.
- **FR-007**: The page MUST show the source (file, address, checksum, licence, first and last download, latest `Updated` date, counts by `Valid`) and state that dates and status are the company's report to Fimea and the end date an estimate.
- **FR-008**: "Update shortage data" MUST download the file now, one update at a time, show progress and then "updated", "no change" or the reason it did not complete, and reload the list.
- **FR-009**: While the backend runs, it MUST update the shortage file and then the Basic Register once per day from `DAILY_UPDATE_TIME` (local time, default `06:00`; `off` disables it). A backend started after that time MUST catch up at once. A run MUST be recorded and not repeated on the same day, also after a restart; a failed run is retried the next day.
- **FR-010**: The page MUST show the daily schedule and the outcome of the last automatic run.
- **FR-011**: Nothing in this feature may create, change or close review cases. The clinical-scope guards MUST be updated deliberately for the four new operations, the new page link and its controls.

## 5. Acceptance criteria

1. With the synthetic files, an update stores the file, lists three shortages in file order, matches SIM-VNR-200 and SIM-VNR-500 to packages and reports SIM-VNR-900 as not in the catalogue.
2. An unchanged file is not stored twice; a later file replaces the list; a rejected file or failed download keeps the previous list; a tampered stored file is reported, not shown.
3. The daily update runs once per day from the set time, catches up after a late start, is not repeated after a restart, and records failures.
4. With the real file (751 rows) and the real 2026-10-06 release, the page lists all shortages with packages, searches and filters, and has no contrast failures or horizontal overflow at 320–1440 px.
5. All backend and frontend tests, type check, lint, format check and build pass.
