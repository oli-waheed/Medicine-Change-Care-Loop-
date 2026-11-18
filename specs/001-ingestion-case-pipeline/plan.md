# Implementation Plan: Medicine Change Ingestion-to-Case Pipeline

**Branch**: `001-ingestion-case-pipeline` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-ingestion-case-pipeline/spec.md`

## Summary

Deliver a small end-to-end prototype slice that imports the official Fimea Basic Register XML through a scheduled n8n workflow, retains source snapshots, compares successive snapshots for relevant catalog-field changes, deterministically matches those changes against simulated medication records, and presents traceable NEW review cases to a pharmacist. Preserve the raw source and provenance throughout the flow. Fimea describes transferring information to the XML file once daily and says an XSD schema exists; this cadence is not evidence of per-record change timestamps or release ordering. The prototype does not claim to detect leaflet/SPC clinical-content changes or determine clinical significance.

The team has selected Python/FastAPI with SQLite and SQLAlchemy for the backend, React/TypeScript/Vite for the frontend, and local n8n for scheduled workflow automation. Use SQLAlchemy ORM mappings and SQLite-portable features; do not use PostgreSQL-specific SQL/types or database-specific UUID generation. The pipeline is implemented as a prototype (T001–T036): scheduled n8n download, immutable raw-release capture, normalization, comparison, matching, SQLite persistence, read APIs, and the pharmacist open-case page. [quickstart.md](quickstart.md) is the canonical setup and acceptance guide.

## Technical Context

**Language/Version**: Python 3.13.x; Node.js 24.x LTS (24.15.0 or later for the selected jsdom release; n8n 2.42.3 refuses to start on Node.js below 24.0.0, as observed in the T034 run); TypeScript 7.0.2.

**Primary Dependencies**: FastAPI 0.142.2; Uvicorn 0.54.0; SQLAlchemy 2.1.3; React/React DOM 19.3.0; Vite 8.3.3 with `@vitejs/plugin-react` 6.1.2; n8n 2.42.3, run locally.

**Storage**: SQLite 3.x through Python's built-in `sqlite3` module, with SQLAlchemy 2.1.3 declarative ORM models. Record the actual SQLite runtime version during setup. Use portable SQLAlchemy types and application-generated identifiers; avoid JSONB, PostgreSQL-specific SQL, and server/database-specific UUID generation.

**Testing and quality**: pytest 9.1.1 and Ruff 0.16.10 for backend tests/linting, with httpx2 2.16.2 for the FastAPI/Starlette test client; Vitest 5.0.3 with React Testing Library 16.3.3, `@testing-library/jest-dom` 7.0.1, jsdom 30.1.2, and React type declarations `@types/react` and `@types/react-dom` 19.3.0 for frontend tests; Oxlint 1.87.0 for frontend linting; Prettier 3.9.9 for formatting; manual end-to-end validation of ingestion through pharmacist case review.

**Target Platform**: Prototype environment; production deployment is out of scope.

**Project Type**: End-to-end web prototype with a Python backend, TypeScript frontend, local SQLite persistence, and locally run n8n scheduled ingestion.

**Performance Goals**: Process one selected source release and its included records in a single scheduled run without losing records or creating duplicate cases; no high-volume or real-time throughput target is defined.

**Constraints**: Simulated patient and medication data only. Human review is mandatory. No diagnoses, treatment recommendations, substitution selection, urgency decisions, automatic clinically relevant case closure, AI explanations, patient-facing views, communication/follow-up, external clinical systems, or production deployment. Unknown or conflicting source order and ambiguous matches must remain explicit and must not produce verified cases.

**Scale/Scope**: One selected official Fimea Basic Register XML feed, successive available snapshots, controlled simulated medication data, and pharmacist-facing open NEW cases. Fimea describes the XML file as refreshed once per day; the prototype must not imply that each transfer is a new ordered release or that every field changed.

**Version baseline**: Runtime minor lines and exact package versions above were selected/documented on 2026-10-06. Exact direct package pins are maintained in `backend/pyproject.toml` and `frontend/package.json`, with the npm resolution lockfile committed as `frontend/package-lock.json`. Use the latest patch within Python 3.13.x and Node.js 24.x LTS, and record actual runtime versions at setup. SQLite is supplied by the selected Python runtime; verify its version rather than installing a separate database server.

### T001 Stack Decision Record

The team finalized the stack for this feature. These versions and commands define the setup baseline; they do not create application code or dependency manifests.

| Area | Selected baseline |
|---|---|
| Backend runtime | Python 3.13.x |
| Backend web framework/server | FastAPI 0.142.2; Uvicorn 0.54.0 |
| ORM and database | SQLAlchemy 2.1.3; SQLite 3.x via Python `sqlite3` |
| Backend tests | pytest 9.1.1 |
| Backend lint/format | Ruff 0.16.10 |
| Frontend runtime | Node.js 24.x LTS with its bundled npm |
| Frontend | React and React DOM 19.3.0; TypeScript 7.0.2; Vite 8.3.3; `@vitejs/plugin-react` 6.1.2 |
| Frontend tests | Vitest 5.0.3; React Testing Library 16.3.3; `@testing-library/jest-dom` 7.0.1; jsdom 30.1.2; `@types/react` and `@types/react-dom` 19.3.0 |
| Frontend lint/format | Oxlint 1.87.0; Prettier 3.9.9 |
| Workflow automation | n8n 2.42.3, run locally on Node.js 24.x |
| Data | Synthetic/simulated data only |

Version source: package release metadata from PyPI and the npm registry, checked 2026-10-06. Python and Node.js use the specified minor/LTS lines and latest compatible patch; pin exact installed patches in setup documentation when the team installs them.

### Commands

Windows PowerShell commands, run from the repository root (the full guide with expected output is in
[quickstart.md](quickstart.md)):

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e "./backend[dev]"
python -c "import sqlite3; print(sqlite3.sqlite_version)"
python -m uvicorn backend.src.main:app --reload
python -m pytest -q
```

Ruff reads its settings from `backend/pyproject.toml`, so run it from the `backend` folder:

```powershell
Set-Location backend
python -m ruff check src ..\tests
python -m ruff format --check src ..\tests
Set-Location ..
```

The frontend scaffold was created with `create-vite@9.2.1`; that scaffolding
CLI version is independent of the pinned Vite application version. The exact
direct dependency pins and lockfile are in `frontend/package.json` and
`frontend/package-lock.json`. Install and verify them with:

```powershell
Set-Location frontend
npm ci
npm run build
npm run test -- --run
npm run lint
npm run format:check
npm run dev
```

`npm run format` applies Prettier formatting.

Run the local workflow editor in a separate terminal:

```powershell
npx --yes n8n@2.42.3 start
```

### File Naming Conventions

- Backend source root: `backend/src/`; use lowercase `snake_case.py` modules and `__init__.py` package markers. The ASGI entry point is `backend/src/main.py`; API route modules are under `api/` (one module per endpoint group; the empty `api/routes/` package from the T002 skeleton is unused), domain types under `domain/`, SQLAlchemy ORM mappings under `models/`, response serialization under `schemas/`, business logic under `services/`, and the ingestion-to-review orchestration under `workflows/`. Demo simulated medication records are in `backend/seed/`.
- SQLAlchemy models use declarative typed mappings (`Mapped` and `mapped_column`) and portable SQLite-compatible column types. Do not add PostgreSQL-only types or raw PostgreSQL-specific SQL.
- Backend unit and contract tests live in repository-root `tests/unit/` and `tests/contract/` as `test_<subject>.py`; integration tests live in `tests/integration/` and use `test_<journey>.py`. Shared pytest fixtures are in `tests/conftest.py`; synthetic source and simulated medication fixtures are under `tests/fixtures/`.
- Frontend source: `frontend/src/main.tsx`; React components and page files use `PascalCase.tsx` (for example, `OpenReviewCasesPage.tsx`); hooks use `use<Name>.ts`; non-component TypeScript modules use `camelCase.ts`. The open-case page and its helpers live together in `frontend/src/pages/open-review-cases/`.
- Frontend tests: colocated `<Name>.test.tsx` or `<name>.test.ts`; test setup uses `frontend/src/test/setup.ts`.
- n8n exported workflows use descriptive kebab-case JSON filenames, including `workflow/n8n/fimea-basic-register-ingestion.json`.
- Simulated medication records use descriptive JSON fixture filenames; synthetic Fimea release fixtures retain the source-like text extension/format. Never place real patient-identifiable information in source, fixtures, logs, or demonstrations.

## Constitution Check

**Pre-research gate: PASS**

- **Evidence-driven decisions**: Preserve raw source material, source release identity, retrieval time, and evidence references; distinguish source facts from assumptions and unknowns.
- **User-centered delivery**: Prioritize the pharmacist's traceable open-case review journey.
- **Shared accountability**: Record ownership and decisions in project artifacts and review changes through the team workflow.
- **Quality before completion**: Validate each vertical slice with automated business-logic/API tests and manual end-to-end testing.
- **Continuous improvement**: Checkpoint source suitability and relevant-field definitions before expanding scope.
- **Human-in-the-loop safety and scope**: Cases remain review items; no clinical decisions or prohibited integrations are introduced.
- **Simulated data and privacy**: Use fictional records in all environments and fixtures.
- **Small vertical slices**: Implement from a source fixture through a visible case before broadening coverage.

**Post-design gate: PASS**. The proposed entities/contracts preserve traceability, uncertainty and human review. No constitution violations or additional subsystems are proposed.

## Research Plan and Decisions

Phase 0 findings and decision rationale are recorded in [research.md](research.md). The selected source is the Fimea Basic Register. The file layout, relevant fields (T005), and reuse terms (Fimea open data, CC BY 4.0) are documented there. Still open before relying on live data: confirming that `Ajopvm` orders successive real releases, the 2021/2022 XSD mismatch, and an explicit automated-download frequency statement. If reliable release ordering cannot be established from source evidence, the pipeline exposes the order as unknown and does not claim a verified change.

The Basic Register is a catalog source with package-level release changes; it is not a documented feed of leaflet/SPC clinical text. The team agreed the relevant catalog fields in T005. The feature must not describe catalog differences as clinical risk or medicine advice.

## Design

### Processing Flow

1. n8n downloads the official Basic Register XML once a day (06:00) and uploads it unchanged to `POST /api/source-releases/ingest`. A failed download or upload is recorded in its own n8n branch and never reaches comparison.
2. The ingestion boundary stores the raw file immutably with its checksum, source identity, caller-supplied release reference, and retrieval time, and records the capture in SQLite. Content that is already captured (the unchanged daily file) is not stored again; only the later retrieval time is recorded. Release order is derived by the backend from the XML's own `Ajopvm`; retrieval time and caller-declared order are never used as source chronology.
3. The normalizer validates the whole release atomically (malformed XML, duplicate `Pakkaustunnus`, or `Kattavuus` other than 1 fail the release) and produces package snapshots of the T005 fields, preserving missing/empty/value states and code-table attributes.
4. A release with verified order that is newer than the stored baseline is compared with it. Packages are paired by the exact `Pakkaustunnus`, product and active-substance references are resolved within each source document, and linked substances are paired by `Aine` code. All field differences for one package form one change set; a package present once in the baseline and absent from the newer full-coverage release forms a `NO_LONGER_PRESENT` change set. `VNR-numero` is supporting metadata only, and cross-release key stability remains unverified.
5. A deterministic matcher checks each change set against simulated medication records by exact `Pakkaustunnus` and records one outcome per change set: `MATCHED`, `NO_MATCH`, or `AMBIGUOUS`.
6. A `MATCHED` outcome creates one NEW review case per change set and simulated record, with a NEW status event. Captures, cases, and outcomes are written in one transaction, and reprocessing the same release creates nothing new.
7. The pharmacist-facing open-case view reads cases and presents their changes, simulated match, source evidence, evidence classifications, and status. `GET /api/change-processing-outcomes` exposes every outcome, including those that created no case. No case-closing or clinical-decision action exists in this feature.

### Project Structure

Implemented structure (main folders):

```text
workflow/
└── n8n/
    └── fimea-basic-register-ingestion.json
backend/
├── pyproject.toml
├── seed/                      # simulated demo medication records
└── src/
    ├── main.py
    ├── config.py
    ├── api/                   # open_review_cases, change_processing_outcomes, source_release_ingestion
    ├── domain/                # source release, snapshot, change/change set, case, status event, evidence
    ├── models/                # SQLAlchemy ORM mappings (SQLite)
    ├── schemas/               # API payload serialization
    ├── services/              # capture, normalize, detect, match, outcomes, cases, store, records loader
    └── workflows/             # ingestion_to_review orchestration
frontend/
└── src/
    ├── pages/open-review-cases/
    ├── assets/
    └── test/
tests/
├── fixtures/
│   ├── acceptance/
│   ├── fimea-basic-register/
│   └── simulated-medication-records/
├── unit/
├── contract/
└── integration/
```

Runtime data (SQLite database and raw captures) is created in `backend/data/`, which is git-ignored.

**Structure Decision**: Use the selected Python/FastAPI backend, React/TypeScript frontend, SQLite persistence, and local n8n orchestration to make the ingestion-to-review journey testable as small vertical slices. Backend and frontend tests remain in their documented roots. Keep SQLAlchemy models portable across SQLite. Do not add services or layers without a demonstrated need.

## Complexity Tracking

No constitution violations or added architectural complexity require justification.
