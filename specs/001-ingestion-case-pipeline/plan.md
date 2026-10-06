# Implementation Plan: Medicine Change Ingestion-to-Case Pipeline

**Branch**: `001-ingestion-case-pipeline` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-ingestion-case-pipeline/spec.md`

## Summary

Deliver a small end-to-end prototype slice that imports the official Fimea Basic Register XML through a scheduled n8n workflow, retains source snapshots, compares successive snapshots for relevant catalog-field changes, deterministically matches those changes against simulated medication records, and presents traceable NEW review cases to a pharmacist. Preserve the raw source and provenance throughout the flow. Fimea describes transferring information to the XML file once daily and says an XSD schema exists; this cadence is not evidence of per-record change timestamps or release ordering. The prototype does not claim to detect leaflet/SPC clinical-content changes or determine clinical significance.

The team has selected Python/FastAPI with SQLite and SQLAlchemy for the backend, React/TypeScript/Vite for the frontend, and local n8n for scheduled workflow automation. Use SQLAlchemy ORM mappings and SQLite-portable features; do not use PostgreSQL-specific SQL/types or database-specific UUID generation. The repository now has initial backend/frontend skeletons and pinned dependency manifests; the business pipeline is not yet implemented.

## Technical Context

**Language/Version**: Python 3.13.x; Node.js 24.x LTS (24.15.0 or later for the selected jsdom release; also satisfies the selected local n8n release's Node.js requirement); TypeScript 7.0.2.

**Primary Dependencies**: FastAPI 0.142.2; Uvicorn 0.54.0; SQLAlchemy 2.1.3; React/React DOM 19.3.0; Vite 8.3.3 with `@vitejs/plugin-react` 6.1.2; n8n 2.42.3, run locally.

**Storage**: SQLite 3.x through Python's built-in `sqlite3` module, with SQLAlchemy 2.1.3 declarative ORM models. Record the actual SQLite runtime version during setup. Use portable SQLAlchemy types and application-generated identifiers; avoid JSONB, PostgreSQL-specific SQL, and server/database-specific UUID generation.

**Testing and quality**: pytest 9.1.1 and Ruff 0.16.10 for backend tests/linting; Vitest 5.0.3 with React Testing Library 16.3.3, `@testing-library/jest-dom` 7.0.1, jsdom 30.1.2, and React type declarations `@types/react` and `@types/react-dom` 19.3.0 for frontend tests; Oxlint 1.87.0 for frontend linting; Prettier 3.9.9 for formatting; manual end-to-end validation of ingestion through pharmacist case review.

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

Windows PowerShell commands for the backend:

```powershell
Set-Location backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -c "import sqlite3; print(sqlite3.sqlite_version)"
python -m uvicorn main:app --app-dir src --reload
python -m pytest ..\tests
python -m ruff check src ..\tests
python -m ruff format --check src ..\tests
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

`npm run format` applies Prettier formatting. Vitest exits unsuccessfully when
no matching test files exist, which is expected before feature tests are added.

Run the local workflow editor in a separate terminal:

```powershell
npx --yes n8n@2.42.3 start
```

### File Naming Conventions

- Backend source root: `backend/src/`; use lowercase `snake_case.py` modules and `__init__.py` package markers. The ASGI entry point is `backend/src/main.py`; keep API routes under `api/routes/`, domain types under `domain/`, SQLAlchemy ORM mappings under `models/`, request/response schemas under `schemas/`, and business logic under `services/`.
- SQLAlchemy models use declarative typed mappings (`Mapped` and `mapped_column`) and portable SQLite-compatible column types. Do not add PostgreSQL-only types or raw PostgreSQL-specific SQL.
- Backend unit and contract tests live in repository-root `tests/unit/` and `tests/contract/` as `test_<subject>.py`; integration tests live in `tests/integration/` and use `test_<journey>.py`. Shared pytest fixtures are in `tests/conftest.py`; synthetic source and simulated medication fixtures are under `tests/fixtures/`.
- Frontend source: `frontend/src/main.tsx`; React components and page files use `PascalCase.tsx` (for example, `OpenReviewCasesPage.tsx`); hooks use `use<Name>.ts`; non-component TypeScript modules use `camelCase.ts`.
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

Phase 0 findings and decision rationale are recorded in [research.md](research.md). The selected source is the Fimea Basic Register. Before relying on live data, validate file access, current file layout, release ordering metadata, permitted reuse/automated access, and the exact fields included in the chosen release. If reliable release ordering cannot be established from source evidence, the pipeline must expose the order as unknown and refrain from claiming a verified change.

The Basic Register is a catalog source with package-level release changes; it is not a documented feed of leaflet/SPC clinical text. The team must agree which available catalog fields count as relevant changes before implementation. The feature must not describe catalog differences as clinical risk or medicine advice.

## Design

### Processing Flow

1. n8n checks for a new official Basic Register release on the agreed schedule and captures the raw release bundle without modifying its contents.
2. The ingestion boundary records source identity, any source-supplied release/order information, retrieval time, filenames, and content checksums. Retrieval time is not substituted for missing source update information.
3. The normalizer produces records for fields selected as relevant, retaining each value's source-record reference and evidence classification.
4. The comparison process pairs records for the same medicine/package using an agreed stable identifier, compares successive ordered snapshots, and emits changes only for agreed relevant fields.
5. A deterministic matcher checks each relevant change against simulated medication records at the same identifier granularity. Missing or ambiguous identifiers result in no match and an explicit uncertainty outcome.
6. A matched change creates one NEW review case per unique change and simulated medication record. Reprocessing the same release is idempotent.
7. The pharmacist-facing open-case view reads cases and presents their change, simulated match, source evidence, evidence quality, and current status. No case-closing or clinical-decision action is added in this feature.

### Project Structure

The repository has no application code yet. This selected structure is the baseline T002 will establish:

```text
workflow/
└── n8n/
    └── fimea-basic-register-ingestion.json
backend/
├── src/
│   ├── main.py
│   ├── api/routes/
│   ├── domain/
│   ├── models/
│   ├── schemas/
│   └── services/
frontend/
└── src/
    ├── components/
    ├── pages/
    ├── services/
    └── test/
tests/
├── fixtures/
│   ├── fimea-basic-register/
│   └── simulated-medication-records/
├── unit/
├── contract/
└── integration/
```

**Structure Decision**: Use the selected Python/FastAPI backend, React/TypeScript frontend, SQLite persistence, and local n8n orchestration to make the ingestion-to-review journey testable as small vertical slices. Backend and frontend tests remain in their documented roots. Keep SQLAlchemy models portable across SQLite. Do not add services or layers without a demonstrated need.

## Complexity Tracking

No constitution violations or added architectural complexity require justification.
