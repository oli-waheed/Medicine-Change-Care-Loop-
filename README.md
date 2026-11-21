# Medicine Change Care Loop

[![CI](https://github.com/oli-waheed/Medicine-Change-Care-Loop-/actions/workflows/ci.yml/badge.svg)](https://github.com/oli-waheed/Medicine-Change-Care-Loop-/actions/workflows/ci.yml)

A software development project exploring how changes in official medicine information can be captured, compared, and presented for pharmacist review.

## Overview

Medicine Change Care Loop is a prototype that monitors changes in medicine information using the Finnish Medicines Agency (Fimea) Basic Register.

The system captures official source releases, preserves their original data and provenance, and supports the identification of changes between comparable medicine package records. Relevant changes can be linked to simulated medication records and presented as review cases with supporting evidence.

The same validated release can be browsed in a read-only Medicine Catalogue, and Fimea's open shortage data is shown next to the matching catalogue packages. The backend keeps both sources up to date with a daily automatic update.

The project focuses on traceability, evidence quality, and pharmacist-led review.

## Key Features

- Retrieve the Fimea Basic Register XML source and Fimea's open shortage data.
- Capture and preserve original source-release files.
- Calculate and store source-file checksums.
- Validate and normalize source data.
- Preserve source metadata and provenance.
- Compare medicine package information across eligible releases.
- Use package identifiers (Pakkaustunnus) as the primary matching key.
- Match source changes with simulated medication records.
- Create one review case per package update and matched record for pharmacist assessment.
- Detect packages that are no longer present in the register.
- Keep an outcome for every change (`MATCHED`, `NO_MATCH`, `AMBIGUOUS`), including those that create no case.
- Present before-and-after information and supporting source evidence, and show when that evidence is no longer available.
- Review cases in a responsive workspace with a sidebar, case search and separate layouts for changed and removed packages (feature 003).
- Browse a read-only Medicine Catalogue of the active validated release: search by name, package ID or VNR, filter by source fields, open product and package records with provenance, explore active substances and compare two products field by field (feature 004).
- Check Fimea for a new release from About the Data with one button, which downloads and loads it like the daily workflow (feature 005).
- See the medicine shortages reported to Fimea, matched to catalogue packages by VNR, on a Medicine Shortages page with an update button; the backend updates the shortage data and the Basic Register automatically every day (feature 006).
- Record a pharmacist's review on any case (In progress, Reviewed – no action needed, Reviewed – follow-up needed, or reopen), with initials, a note and a kept history; and create review cases when a shortage starts, changes or ends for a package of a simulated record (feature 007).
- See at a glance which cases are likely Fimea data clean-ups ("Spacing or letter case only", "Active-substance fields only") and set them aside for the moment if you choose; nothing is hidden or closed automatically (feature 008).
- Store an unchanged daily download only once, recording each retrieval time.
- Provide APIs for review cases and review steps, change processing outcomes, the medicine catalogue, shortage data and the update status.

## How It Works

The source-ingestion and review process follows these main steps:

1. Retrieve the Fimea Basic Register XML.
2. Capture the original source release.
3. Validate and normalize the XML data.
4. Preserve source metadata, provenance, and checksums.
5. Compare eligible source releases.
6. Identify changes in medicine package information, grouped per package, including VNR changes and packages that are no longer present in the register.
7. Match each package's changes with simulated medication records.
8. Create one review case per package update and matched record for pharmacist assessment.
9. Present the changes and supporting evidence through the application interface.
10. Let the pharmacist record each review step on the case; the system never changes a case's status by itself.

Alongside this, the latest validated release is available as a read-only Medicine Catalogue, and Fimea's shortage file is downloaded, checked, stored once per content and matched to catalogue packages by VNR. Once a day the backend updates both automatically (feature 006); each can also be updated with a button. When the shortage file changes, shortages that start, change or end for a package of a simulated record become review cases too (feature 007).

A source-data change does not automatically mean that there is a clinically significant change.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript |
| Frontend build tool | Vite |
| Frontend testing | Vitest |
| Backend | Python 3.13, FastAPI |
| Database | SQLite via SQLAlchemy |
| Backend testing | pytest |
| Workflow automation | The backend's own daily update (feature 006); an n8n workflow kept for reference, switched off |
| Source format | XML |
| Version control | Git and GitHub |

## Application Interface

The frontend is a light-themed review workspace in the approved navy and teal design. A sidebar holds the project logo (a gold bird, crescent and bowl of Hygieia, `frontend/src/assets/brand-logo.png`) and product name, links to the four pages, the Fimea attribution with the CC BY 4.0 licence link, and the application version once `frontend/package.json` has a real version (the placeholder `0.0.0` is hidden). The sidebar is persistent from 1024 px wide, collapses to an icon rail with a **Sidebar** toggle on tablets, and opens from a **Menu** button on phones.

- **Open Review Cases** (`/`): a searchable case queue (by medicine name, identifier, change summary or status; arrow keys move between cases) and the selected case. Release and shortage cases share the queue. Each case has a **Review** section: the reviewer's initials, a note, the steps allowed from the current status, and the case's history. Reviewed cases leave the queue and are shown with **Show reviewed cases** (feature 007). Likely source clean-ups carry a label, and **Set aside likely source clean-ups** takes them out of the list until you turn it off (feature 008).
- **Medicine Catalogue** (`/medicine-catalogue`): packages, products and active substances of the active validated release as the source records them; search, filters, package and product records with provenance, and a two-product comparison (feature 004).
- **Medicine Shortages** (`/medicine-shortages`): the shortages in Fimea's open shortage file, in the file's order and as published, with the matching catalogue packages by VNR; search, a status filter, the **Update shortage data** button and the daily update's last run (feature 006).
- **About the Data** (`/about-data`): simulated records, the Fimea data sources and licence, attribution, limitations, and the **Check for new Fimea release** button (feature 005).
- Any other address shows **Page not found**.

Changed packages and packages no longer present in the register have separate review layouts. Changed fields show their prior-release and current-release values and whether the field was added, removed or changed in the source. Every page starts with a "Skip to main content" link and can be used with the keyboard alone; text meets WCAG 2.2 AA contrast.

The Open Review Cases page retrieves open review cases through the backend API and presents:

- Simulated medication record information.
- Medicine identifiers and matching information.
- Detected source-data changes.
- Before-and-after values.
- Prior and current source evidence.
- Source-release references and checksums.
- Evidence classifications.
- Source-order information.
- Packages that are no longer present in the register, with their last known values.
- A notice when a case's raw source files are no longer stored.

The interface is designed to support pharmacist assessment. It does not make clinical decisions.

## Backend API

The backend is implemented using FastAPI.

Current API endpoints include:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check backend health |
| GET | `/api/open-review-cases` | Retrieve cases to review (`NEW`, `IN_PROGRESS`) with their status history; `?includeReviewed=true` adds reviewed cases |
| POST | `/api/review-cases/{caseId}/status-events` | Record a pharmacist's review step (`expectedStatus`, `toStatus`, `reviewerInitials`, `note`) |
| GET | `/api/change-processing-outcomes` | Retrieve every matching outcome (`MATCHED`, `NO_MATCH`, `AMBIGUOUS`); filter with `?result=NO_MATCH&result=AMBIGUOUS` |
| POST | `/api/source-releases/ingest` | Submit and process a source release |
| GET | `/api/medicine-catalogue` | Search and filter packages of the active validated release (`q`, `activeSubstance`, `atc`, `form`, `route`, `available`, `vnr`, `missing`, `page`, `pageSize`) |
| GET | `/api/medicine-catalogue/products/{productReference}` | One product and its packages |
| GET | `/api/medicine-catalogue/packages/{pakkaustunnus}` | One package, its provenance and packages sharing its VNR |
| GET | `/api/medicine-catalogue/active-substances` | Active substances with every occurrence in source order |
| GET | `/api/medicine-catalogue/compare?productA=…&productB=…` | Source fields of two products side by side |
| GET | `/api/medicine-catalogue/source` | Active catalogue release and record counts |
| POST | `/api/source-releases/latest-check` | Start downloading and ingesting the latest Fimea release in the background |
| GET | `/api/source-releases/latest-check` | Progress and outcome of that check |
| GET | `/api/shortages` | Fimea shortage data with matching catalogue packages (`q`, `valid`, `page`, `pageSize`) |
| POST | `/api/shortages/update` | Download the latest shortage file in the background |
| GET | `/api/shortages/update` | Progress and outcome of that download |
| GET | `/api/daily-updates` | Daily automatic update: schedule and last run |

### API Documentation

These links work only on your own computer while the backend is running:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Source Ingestion Workflow

The Fimea Basic Register is downloaded automatically by the backend's daily update (see below). This is the primary scheduler (decision T016, 2026-11-21).

An n8n workflow that does the same was used before feature 006. It is kept for reference and is switched off (`"active": false`); if you turn it on, the 190 MB file is downloaded twice a day.

The workflow retrieves the XML source and submits it to the backend ingestion API. The backend handles source-release capture, validation, and normalization.

Release order is derived by the backend from the XML's own `Ajopvm` (dataset run date). The `sourceOrder` value sent by the workflow is recorded for traceability only and is not used for chronology. Each new release with a later `Ajopvm` is compared with the stored baseline, and matching changes create review cases.

The workflow includes success and failure handling for download and upload operations. When switched on, it runs daily at 06:00 and uploads to `http://host.docker.internal:8000`, which works when n8n runs in Docker; when n8n is started with `npx`, change the upload URL to `http://127.0.0.1:8000/api/source-releases/ingest`. n8n 2.42.3 requires Node.js 24. See [quickstart.md](specs/001-ingestion-case-pipeline/quickstart.md#4-local-n8n-scheduled-ingestion).

The workflow configuration is available in:

`workflow/n8n/fimea-basic-register-ingestion.json`

To load the latest release by hand, press **Check for new Fimea release** on About the Data (feature 005). The backend downloads the same file from the same address and ingests it the same way; an unchanged file is only recorded as a new retrieval. A real release takes about one to two minutes.

### Daily automatic update (feature 006)

While the backend runs, it downloads Fimea's shortage file (`Shortages.txt`) and then checks the Basic Register once a day from `DAILY_UPDATE_TIME` (default 06:00 local time). If the backend starts after that time, it runs at once; each day's run is recorded, so a restart does not repeat it. Shortage files are stored once per content in a `shortages` folder next to the source-release captures. The Medicine Shortages page also has an **Update shortage data** button. The n8n workflow is switched off, so the file is downloaded once a day.

## Data Source and Licence

Source data: **Basic register for medicinal products (Perusrekisteri), Finnish Medicines Agency Fimea**, published as open data under the [Creative Commons Attribution 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) licence ([Fimea open data](https://fimea.fi/en/about_us/open-data)).

Shortage data: **Fimea's open shortage data** (`Shortages.txt`), under the same licence. It lists the shortages that marketing authorisation holders report to Fimea, by VNR. Its dates and status are the companies' reports, shown as published; the end date is an estimate.

- When presenting or sharing results, name Fimea as the licensor, the material ("Basic register for medicinal products"), and the release date of the data used. Each review case shows the release date (`Ajopvm`) and retrieval time of its source files.
- This project changes the presentation of the data: it normalizes selected fields and compares successive releases. The comparisons are this project's, not Fimea's.
- Fimea notes that individual errors may occur in the register and does not guarantee that the online data is complete or up to date.
- The test fixtures in `tests/fixtures/` (including `tests/fixtures/fimea-shortages/`) are synthetic and are not Fimea data.

## Safety and Project Scope

Medicine Change Care Loop is a software development prototype, not an autonomous clinical decision-support system.

The following boundaries apply:

- Only synthetic medication records are used.
- No patient-identifiable information is processed.
- The system does not diagnose medical conditions.
- The system does not recommend treatments or medicine substitutions; the shortage page lists packages only and does not point to other products.
- The system does not make autonomous clinical decisions.
- Pharmacists remain responsible for reviewing and assessing the presented information. Only a pharmacist's recorded review step changes a case's status; nothing changes it automatically, and the history is never edited.
- Source-data changes are not automatically considered clinically significant.
- Evidence classifications and source provenance are preserved to support transparent review.

## Running the Project Locally

### Prerequisites

- Python 3.13
- Node.js 24.15.0 or later (also required by n8n 2.42.3)
- npm

The full setup and acceptance guide, with the expected output of every command, is in
[specs/001-ingestion-case-pipeline/quickstart.md](specs/001-ingestion-case-pipeline/quickstart.md).

### Backend

From the project root, activate the existing virtual environment if necessary:

```powershell
.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
python -m pip install -e "./backend[dev]"
```

Start the FastAPI development server:

```powershell
uvicorn backend.src.main:app --reload
```

The backend runs at `http://127.0.0.1:8000` while the server is running. It has no page at `/` (opening it shows `{"detail":"Not Found"}`, which is expected). Use these instead:

- API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

#### Backend configuration and data

Cases, case status events (with the reviewer's initials and note), the source-release capture history, the shortage downloads and the daily update runs are stored in SQLite, so they survive a restart. Raw source files are stored as immutable captures on disk; after a restart, the comparison baseline is rebuilt from its captured raw file, which is checked against its recorded checksum first. A download whose content is already captured, such as an unchanged daily file, is not stored again; only its retrieval time is recorded. If a raw file is later removed, the cases that rely on it are shown as having unavailable evidence.

| Environment variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///backend/data/medicine-change-care-loop.sqlite3` | SQLite database for cases, status events and capture history. |
| `SOURCE_RELEASE_STORAGE_DIR` | `backend/data/source-releases` | Immutable raw-release captures. |
| `SIMULATED_MEDICATION_RECORDS_PATH` | `backend/seed/simulated-medication-records.json` | Fictional medication records used for matching. Without this file no cases can be created. |
| `MAX_SOURCE_RELEASE_UPLOAD_BYTES` | `262144000` | Upload and download size limit. |
| `FIMEA_RELEASE_URL` | `https://data.pilvi.fimea.fi/avoin-data/Perusrekisteri.xml` | Basic Register address used by "Check for new Fimea release" (feature 005) and the daily update (feature 006); the n8n workflow's address. |
| `FIMEA_SHORTAGES_URL` | `https://data.pilvi.fimea.fi/avoin-data/Shortages.txt` | Fimea's open-data shortage file (feature 006). |
| `DAILY_UPDATE_TIME` | `06:00` | Local time of the daily automatic update of the shortage file and the Basic Register; `off` disables it. |

`backend/data/` is git-ignored. Delete it to start from an empty state; the schema is created automatically. New nullable columns are added to an existing database automatically (feature 007 added the reviewer's initials and note); other schema changes are not migrated, so after such a change delete `backend/data/` once.

#### Running with real Fimea data

Keep real Fimea data in its own database. The synthetic test releases are dated 2099, so in the default database they stay newer than any real release and hide it. In PowerShell, set both variables in the window that starts the backend:

```powershell
$env:DATABASE_URL = "sqlite:///backend/data/real/real.sqlite3"
$env:SOURCE_RELEASE_STORAGE_DIR = "backend/data/real/source-releases"
uvicorn backend.src.main:app
```

The settings apply only to that window; a new window without them uses the test database again. The real database fills itself: the daily update downloads both the Basic Register and the shortage file, and **Check for new Fimea release** and **Update shortage data** do the same on request. Be aware of the size of a real release (measured on the 2026-10-06 release, feature 004 T005):

- The Basic Register file is about 190 MB (about 146,000 packages). Uploading a newer release (reading it, comparing it with the previous one and creating cases) takes under a minute and about 600 MB of memory (feature 009).
- A backend started after `DAILY_UPDATE_TIME` runs that day's update at once, so the first start of the day downloads both files.
- After a restart, the first catalogue request rebuilds the release (about 12 seconds); the daily update and the release check prepare it in advance. The shortage list does not wait: it shows the shortages first and adds the catalogue packages when ready.

The seed records match the synthetic test fixtures: `SIM-PKG-100` produces a case with several field changes and `SIM-PKG-300` a case for a package that is no longer present in the register. To see cases from live Fimea data, put fictional records whose `Pakkaustunnus` is a real public package identifier in a separate file outside the repository (for example `backend/data/real/real-demo-records.json`) and point `SIMULATED_MEDICATION_RECORDS_PATH` to it. Files in `backend/seed/` must keep `SIM-` identifiers; a test checks this. Cases are created when a newer release is compared, so load the older release first, then the newer one, into a new database (see [the validation report](docs/validation/2026-11-21-real-release-comparison.md)). Never add real patient data.

To check the real releases the daily update has collected, run the comparison helper from the `backend` folder. It reads the stored files only, orders them by `Ajopvm` and compares the newest pair (`--pairs 3` for the newest three; about 15 seconds per release):

```powershell
python tools\compare_releases.py data\real\source-releases --pairs 3 --out data\real\comparison.md
```

The report shows whether the release order is strictly increasing, whether any `Pakkaustunnus` repeats within a release, how many are in both releases, and the changed, removed and new packages, VNR changes and source clean-up labels.

### Frontend

Open a second terminal and navigate to the frontend directory:

```powershell
cd frontend
```

Install frontend dependencies:

```powershell
npm install
```

Start the Vite development server:

```powershell
npm run dev
```

The frontend runs at http://localhost:5173/ while `npm run dev` is running. The backend must be running too; otherwise the page shows "Open cases could not be loaded".

During local development, Vite proxies requests beginning with `/api` to the FastAPI backend at `http://127.0.0.1:8000`.

Keep both backend and frontend development servers running while using the application.

## Testing

Every push and pull request runs all the checks below on GitHub (`.github/workflows/ci.yml`): backend tests, Ruff check and format, frontend tests, Oxlint, Prettier, type check and build. The result shows on the commit and in the **Actions** tab; the badge at the top shows the latest run.

### Backend Tests

From the project root:

```powershell
python -m pytest
```

Expected: `315 passed`. Lint and format checks run from the `backend` folder, where Ruff's settings live:

```powershell
cd backend
python -m ruff check src tools ..\tests
python -m ruff format --check src tools ..\tests
```

### Frontend Tests

From the frontend directory:

```powershell
npx vitest run
```

Expected: `Tests  96 passed (96)`. (`npm run test` without arguments stays in watch mode; in PowerShell, `npm run test -- --run` may not pass `--run` through, so `npx vitest run` is the reliable form.)

Lint and format checks:

```powershell
npm run lint
npm run format:check
```

### Frontend Production Build

From the frontend directory:

```powershell
npm run build
```

## Repository Structure

```text
Medicine-Change-Care-Loop/
|
+-- backend/
|   +-- src/
|   |   +-- api/
|   |   +-- domain/
|   |   +-- models/
|   |   +-- schemas/
|   |   +-- services/
|   |   +-- workflows/
|   +-- seed/
|   +-- pyproject.toml
|
+-- frontend/
|   +-- src/
|   |   +-- app/
|   |   +-- assets/
|   |   +-- pages/
|   |   +-- test/
|   +-- package.json
|   +-- vite.config.ts
|
+-- workflow/
|   +-- n8n/
|
+-- tests/
|   +-- fixtures/
|   +-- unit/
|   +-- contract/
|   +-- integration/
|
+-- specs/
|   +-- 001-ingestion-case-pipeline/ ... 006-medicine-shortages/
+-- project-plans/
+-- docs/
|   +-- development-notes/
|
+-- README.md
```

## Project Status

| Feature | Specification | Tasks |
|---|---|---|
| 001 Ingestion-to-case pipeline | [spec](specs/001-ingestion-case-pipeline/spec.md) | T001–T036 done |
| 002 Case review readability | [spec](specs/002-case-review-readability/spec.md) | done |
| 003 Application shell | [spec](specs/003-app-shell-and-themes/spec.md) | done |
| 004 Interactive Medicine Catalogue | [spec](specs/004-interactive-medicine-catalogue/spec.md) | T001–T060 done |
| 005 Check for a new Fimea release | [spec](specs/005-fimea-release-check/spec.md) | done (approved 2026-11-21) |
| 006 Medicine shortages and daily update | [spec](specs/006-medicine-shortages/spec.md) | done (approved 2026-11-21); T016 and T018 decided 2026-11-21 |
| 007 Recorded reviews and shortage review cases | [spec](specs/007-care-loop-review-and-shortage-cases/spec.md) | done (approved 2026-11-21) |
| 008 Labels for likely source clean-ups | [spec](specs/008-source-cleanup-labels/spec.md) | done (approved 2026-11-21) |
| 009 Faster, lighter catalogue | [spec](specs/009-faster-lighter-catalogue/spec.md) | T001–T005 done; T006 (approval) open |

The implementation includes source-release ingestion, source-data normalization, evidence preservation, change detection per package, matching outcomes, review-case generation, backend API endpoints, an n8n ingestion workflow, and a frontend review workspace. Feature 002 ([specs/002-case-review-readability](specs/002-case-review-readability/spec.md)) improved the readability of the review page; feature 003 ([specs/003-app-shell-and-themes](specs/003-app-shell-and-themes/spec.md)) added the application shell, About the Data, case search and separate review layouts; feature 004 ([specs/004-interactive-medicine-catalogue](specs/004-interactive-medicine-catalogue/spec.md)) added the read-only Medicine Catalogue and its API under `/api/medicine-catalogue`; feature 005 ([specs/005-fimea-release-check](specs/005-fimea-release-check/spec.md)) added "Check for new Fimea release" on About the Data; feature 006 ([specs/006-medicine-shortages](specs/006-medicine-shortages/spec.md)) added Medicine Shortages and the daily automatic update; feature 007 ([specs/007-care-loop-review-and-shortage-cases](specs/007-care-loop-review-and-shortage-cases/spec.md)) added recorded reviews and shortage review cases; feature 008 ([specs/008-source-cleanup-labels](specs/008-source-cleanup-labels/spec.md)) added labels for likely source clean-ups; feature 009 ([specs/009-faster-lighter-catalogue](specs/009-faster-lighter-catalogue/spec.md)) made reading a release about three times faster and five times lighter.

Verification:

- 315 backend tests and 96 frontend tests pass. They include guards that keep all test and demo data simulated and that keep the view and workflow free of clinical decisions.
- The end-to-end acceptance run passed all 10 steps; the results are recorded in [quickstart.md](specs/001-ingestion-case-pipeline/quickstart.md#acceptance-results-t034).

One real Basic Register release (2026-10-06) and one real shortage file (2026-11-20) have been loaded and checked ([004 research.md](specs/004-interactive-medicine-catalogue/research.md), [006 spec.md](specs/006-medicine-shortages/spec.md)). Two real releases (2026-10-06 and 2026-11-21) were compared on 2026-11-21: the order was strictly increasing and no `Pakkaustunnus` repeated within a release ([validation report](docs/validation/2026-11-21-real-release-comparison.md)). Before relying on live Fimea data, the remaining validation is to repeat this on later releases, which the daily update collects, with `backend/tools/compare_releases.py`, and to check the current Fimea XSD ([research.md](specs/001-ingestion-case-pipeline/research.md)).

## Academic Context

This project is developed as part of the Xamk Software Development Project 2026.