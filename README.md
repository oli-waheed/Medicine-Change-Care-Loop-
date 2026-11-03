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
- Create new review cases for pharmacist assessment.
- Present before-and-after information and supporting source evidence.
- Provide an API for retrieving open review cases.

## How It Works

The source-ingestion and review process follows these main steps:

1. Retrieve the Fimea Basic Register XML.
2. Capture the original source release.
3. Validate and normalize the XML data.
4. Preserve source metadata, provenance, and checksums.
5. Compare eligible source releases.
6. Identify changes in medicine package information.
7. Match relevant changes with simulated medication records.
8. Create review cases for pharmacist assessment.
9. Present the changes and supporting evidence through the application interface.

A source-data change does not automatically mean that there is a clinically significant change.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript |
| Frontend build tool | Vite |
| Frontend testing | Vitest |
| Backend | Python 3.13, FastAPI |
| Backend dependency | SQLAlchemy |
| Backend testing | pytest |
| Workflow automation | n8n |
| Source format | XML |
| Version control | Git and GitHub |

## Application Interface

The frontend includes an Open Review Cases page.

It retrieves open review cases through the backend API and presents:

- Simulated medication record information.
- Medicine identifiers and matching information.
- Detected source-data changes.
- Before-and-after values.
- Prior and current source evidence.
- Source-release references and checksums.
- Evidence classifications.
- Source-order information.

The interface is designed to support pharmacist assessment. It does not make clinical decisions.

## Backend API

The backend is implemented using FastAPI.

Current API endpoints include:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check backend health |
| GET | `/api/open-review-cases` | Retrieve open review cases |
| POST | `/api/source-releases/ingest` | Submit and process a source release |

### API Documentation

When the backend is running locally:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Source Ingestion Workflow

The Fimea Basic Register ingestion process is automated using n8n.

The workflow retrieves the XML source and submits it to the backend ingestion API. The backend handles source-release capture, validation, and normalization.

The workflow includes success and failure handling for download and upload operations.

The workflow configuration is available in:

`workflow/n8n/fimea-basic-register-ingestion.json`

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
- Node.js 24.15.0 or later
- npm

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

The backend is available at:

http://127.0.0.1:8000

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

The frontend is available at:

http://localhost:5173/

During local development, Vite proxies requests beginning with `/api` to the FastAPI backend at `http://127.0.0.1:8000`.

Keep both backend and frontend development servers running while using the application.

## Testing

### Backend Tests

From the project root:

```powershell
python -m pytest
```

### Frontend Tests

From the frontend directory:

```powershell
npm test -- --run --pool=threads --maxWorkers=1 --minWorkers=1
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
|   |   +-- medicine/
|   |   +-- models/
|   |   +-- schemas/
|   |   +-- services/
|   |   +-- workflow/
|   +-- pyproject.toml
|
+-- frontend/
|   +-- src/
|   |   +-- pages/
|   |   +-- assets/
|   |   +-- test/
|   +-- package.json
|   +-- vite.config.ts
|
+-- workflow/
|   +-- n8n/
|
+-- tests/
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

The project is under active development.

The current implementation includes source-release ingestion, source-data normalization, evidence preservation, review-case generation, backend API endpoints, an n8n ingestion workflow, and a frontend page for viewing open review cases.

Local backend and frontend startup, API proxying, frontend tests, and the frontend production build have been verified.

The frontend tests currently include two passing tests covering the open-case interface, source evidence, loading errors, and the empty state. A populated review-case workflow has not yet been verified through the browser.

Further development and validation are tracked in the project specifications and task lists.

## Academic Context

This project is developed as part of the Xamk Software Development Project 2026.