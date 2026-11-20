# Medicine Change Care Loop

A software development project exploring how changes in official medicine information can be captured, compared, and presented for pharmacist review.

## Overview

Medicine Change Care Loop is a prototype that monitors changes in medicine information using the Finnish Medicines Agency (Fimea) Basic Register.

The system captures official source releases, preserves their original data and provenance, and supports the identification of changes between comparable medicine package records. Relevant changes can be linked to simulated medication records and presented as review cases with supporting evidence.

The project focuses on traceability, evidence quality, and pharmacist-led review.

## Key Features

- Retrieve the Fimea Basic Register XML source.
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
- Store an unchanged daily download only once, recording each retrieval time.
- Provide APIs for retrieving open review cases and change processing outcomes.

## How It Works

The source-ingestion and review process follows these main steps:

1. Retrieve the Fimea Basic Register XML.
2. Capture the original source release.
3. Validate and normalize the XML data.
4. Preserve source metadata, provenance, and checksums.
5. Compare eligible source releases.
6. Identify changes in medicine package information, grouped per package, including packages that are no longer present in the register.
7. Match each package's changes with simulated medication records.
8. Create one review case per package update and matched record for pharmacist assessment.
9. Present the changes and supporting evidence through the application interface.

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
| Workflow automation | n8n |
| Source format | XML |
| Version control | Git and GitHub |

## Application Interface

The frontend is a light-themed review workspace in the approved navy and teal design. A sidebar holds the product name, links to the two pages, the Fimea attribution with the CC BY 4.0 licence link, and the application version once `frontend/package.json` has a real version (the placeholder `0.0.0` is hidden). The sidebar is persistent from 1024 px wide, collapses to an icon rail with a **Sidebar** toggle on tablets, and opens from a **Menu** button on phones.

- **Open Review Cases** (`/`): a searchable case queue (by medicine name, identifier or change summary; arrow keys move between cases) and the selected case.
- **About the Data** (`/about-data`): simulated records, the Fimea data source and licence, attribution, and limitations.
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
| GET | `/api/open-review-cases` | Retrieve open review cases |
| GET | `/api/change-processing-outcomes` | Retrieve every matching outcome (`MATCHED`, `NO_MATCH`, `AMBIGUOUS`); filter with `?result=NO_MATCH&result=AMBIGUOUS` |
| POST | `/api/source-releases/ingest` | Submit and process a source release |

### API Documentation

These links work only on your own computer while the backend is running:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Source Ingestion Workflow

The Fimea Basic Register ingestion process is automated using n8n.

The workflow retrieves the XML source and submits it to the backend ingestion API. The backend handles source-release capture, validation, and normalization.

Release order is derived by the backend from the XML's own `Ajopvm` (dataset run date). The `sourceOrder` value sent by the workflow is recorded for traceability only and is not used for chronology. Each new release with a later `Ajopvm` is compared with the stored baseline, and matching changes create review cases.

The workflow includes success and failure handling for download and upload operations. It runs daily at 06:00 and uploads to `http://host.docker.internal:8000`, which works when n8n runs in Docker; when n8n is started with `npx`, change the upload URL to `http://127.0.0.1:8000/api/source-releases/ingest`. n8n 2.42.3 requires Node.js 24. See [quickstart.md](specs/001-ingestion-case-pipeline/quickstart.md#4-local-n8n-scheduled-ingestion).

The workflow configuration is available in:

`workflow/n8n/fimea-basic-register-ingestion.json`

## Data Source and Licence

Source data: **Basic register for medicinal products (Perusrekisteri), Finnish Medicines Agency Fimea**, published as open data under the [Creative Commons Attribution 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) licence ([Fimea open data](https://fimea.fi/en/about_us/open-data)).

- When presenting or sharing results, name Fimea as the licensor, the material ("Basic register for medicinal products"), and the release date of the data used. Each review case shows the release date (`Ajopvm`) and retrieval time of its source files.
- This project changes the presentation of the data: it normalizes selected fields and compares successive releases. The comparisons are this project's, not Fimea's.
- Fimea notes that individual errors may occur in the register and does not guarantee that the online data is complete or up to date.
- The test fixtures in `tests/fixtures/` are synthetic and are not Fimea data.

## Safety and Project Scope

Medicine Change Care Loop is a software development prototype, not an autonomous clinical decision-support system.

The following boundaries apply:

- Only synthetic medication records are used.
- No patient-identifiable information is processed.
- The system does not diagnose medical conditions.
- The system does not recommend treatments or medicine substitutions.
- The system does not make autonomous clinical decisions.
- Pharmacists remain responsible for reviewing and assessing the presented information.
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

Cases, case status events and the source-release capture history are stored in SQLite, so they survive a restart. Raw source files are stored as immutable captures on disk; after a restart, the comparison baseline is rebuilt from its captured raw file, which is checked against its recorded checksum first. A download whose content is already captured, such as an unchanged daily file, is not stored again; only its retrieval time is recorded. If a raw file is later removed, the cases that rely on it are shown as having unavailable evidence.

| Environment variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///backend/data/medicine-change-care-loop.sqlite3` | SQLite database for cases, status events and capture history. |
| `SOURCE_RELEASE_STORAGE_DIR` | `backend/data/source-releases` | Immutable raw-release captures. |
| `SIMULATED_MEDICATION_RECORDS_PATH` | `backend/seed/simulated-medication-records.json` | Fictional medication records used for matching. Without this file no cases can be created. |
| `MAX_SOURCE_RELEASE_UPLOAD_BYTES` | `262144000` | Upload size limit. |

`backend/data/` is git-ignored. Delete it to start from an empty state; the schema is created automatically. The schema is not migrated automatically: after pulling a change to the case model, delete `backend/data/` once.

The seed records match the synthetic test fixtures: `SIM-PKG-100` produces a case with several field changes and `SIM-PKG-300` a case for a package that is no longer present in the register. To see cases from live Fimea data, add fictional records whose `Pakkaustunnus` is a real public package identifier from the register. Never add real patient data.

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

### Backend Tests

From the project root:

```powershell
python -m pytest
```

Expected: `191 passed`. Lint and format checks run from the `backend` folder, where Ruff's settings live:

```powershell
cd backend
python -m ruff check src ..\tests
python -m ruff format --check src ..\tests
```

### Frontend Tests

From the frontend directory:

```powershell
npx vitest run
```

Expected: `Tests  54 passed (54)`. (`npm run test` without arguments stays in watch mode; in PowerShell, `npm run test -- --run` may not pass `--run` through, so `npx vitest run` is the reliable form.)

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
+-- project-plans/
+-- docs/
|   +-- development-notes/
|
+-- README.md
```

## Project Status

All tasks of the feature specification (T001–T036 in [tasks.md](specs/001-ingestion-case-pipeline/tasks.md)) are implemented, and the specification lists no known gaps ([spec.md](specs/001-ingestion-case-pipeline/spec.md#implementation-status)).

The implementation includes source-release ingestion, source-data normalization, evidence preservation, change detection per package, matching outcomes, review-case generation, backend API endpoints, an n8n ingestion workflow, and a frontend review workspace. Feature 002 ([specs/002-case-review-readability](specs/002-case-review-readability/spec.md)) improved the readability of the review page; feature 003 ([specs/003-app-shell-and-themes](specs/003-app-shell-and-themes/spec.md)) added the application shell, About the Data, case search and separate review layouts.

Verification:

- 191 backend tests and 54 frontend tests pass. They include guards that keep all test and demo data simulated and that keep the view and workflow free of clinical decisions.
- The end-to-end acceptance run passed all 10 steps; the results are recorded in [quickstart.md](specs/001-ingestion-case-pipeline/quickstart.md#acceptance-results-t034).

Before relying on live Fimea data, the remaining validation is to confirm the `Ajopvm` release order and `Pakkaustunnus` stability on several real daily downloads, and to check the current Fimea XSD ([research.md](specs/001-ingestion-case-pipeline/research.md)).

## Academic Context

This project is developed as part of the Xamk Software Development Project 2026.