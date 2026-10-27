# Quickstart: Validate the Ingestion-to-Case Flow

This guide defines the selected local toolchain and acceptance run for the prototype. T001 records
Python/FastAPI, SQLite/SQLAlchemy, React/TypeScript/Vite, local n8n, and the test runners. The repository
does not yet contain application code; the commands below become runnable as T002/T003 create the
skeletons and test scripts.

## Prerequisites

- Python 3.13.x and its `py` launcher.
- Node.js 24.15.0 or later in the 24.x LTS line and its bundled npm; this satisfies jsdom 30.1.2 and n8n 2.42.3 runtime requirements.
- PowerShell on Windows for the commands below.
- Dependencies installed at the exact versions in [plan.md](plan.md#t001-stack-decision-record).
- A captured Fimea Basic Register release fixture, plus a prior release fixture, with source identity and
  source-provided order information preserved.
- A controlled set of simulated medication records; do not use real patient-identifiable data.
- An agreed list of relevant source fields and the medicine/package matching key and granularity.
- The local n8n workflow exported at `workflow/n8n/fimea-basic-register-ingestion.json`, or its documented
  manual trigger for acceptance testing.

## Install and run commands

### Backend

From the repository root:

```powershell
py -3.13 -m venv backend\.venv
Set-Location backend
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -c "import sqlite3; print(sqlite3.sqlite_version)"
python -m uvicorn main:app --app-dir src --reload
```

In another terminal, run the backend tests:

```powershell
Set-Location backend
.\.venv\Scripts\Activate.ps1
python -m pytest ..\tests
python -m ruff check src ..\tests
python -m ruff format --check src ..\tests
```

The SQLite version printed is the library included with the installed Python runtime. Use SQLAlchemy
declarative ORM mappings and SQLite-compatible types; do not use PostgreSQL-specific SQL, JSONB, or
database-specific UUID generation. The local database file is planned at
`backend/data/medicine-change-loop.sqlite3`.

### Frontend

The React/TypeScript scaffold was created with `create-vite@9.2.1`. This is the
scaffolding tool version; the application itself uses Vite 8.3.3. From the repository root:

```powershell
Set-Location frontend
npm ci
npm run build
npm run test -- --run
npm run lint
npm run format:check
npm run dev
```

In another terminal, run frontend tests:

```powershell
Set-Location frontend
npm run test -- --run
```

Use `npm run format` to apply Prettier formatting. The one-shot Vitest command
returns a failure if no matching test files exist; this is expected before feature
tests are added. Keep dependency versions aligned with the T001 baseline in [plan.md](plan.md).

### Local n8n

Run the local workflow editor in its own terminal:

```powershell
npx --yes n8n@2.42.3 start
```

Import and run `workflow/n8n/fimea-basic-register-ingestion.json` in the local editor. Configure the
scheduled trigger for the agreed polling schedule. Fimea describes the XML file as refreshed once
daily; do not infer source chronology or a new ordered release from the polling interval or local
retrieval time.

## Acceptance run

1. Load the prior and current source release fixtures through the same ingestion path used by the
   scheduled workflow.
2. Verify both source snapshots retain release provenance, retrieval time, raw file references, and
   checksums. Confirm retrieval time is not represented as source update chronology.
3. Include one changed relevant field with a unique exact simulated-record identifier match; include one
   change with no match and one with an ambiguous identifier.
4. Run the scheduled/manual workflow once.
5. Verify the unique match creates exactly one review case in `NEW`, and the pharmacist open-case view
   exposes its before/after evidence, source references, simulated record, and evidence classifications.
6. Verify the no-match and ambiguous scenarios create no cases and retain an honest outcome.
7. Run the same release through the workflow again. Verify that the existing case remains traceable and
   no duplicate review case is created for the same change and simulated medication record.
8. Simulate unavailable or malformed source input and verify the run is visibly failed/incomplete and
   no case is created from partial data.
9. Inspect the whole fixture set and view to confirm every patient and medication record is simulated and
   no clinical decision, treatment recommendation, substitution, urgency determination, or automatic
   case closure occurs.

## Expected result

The acceptance set produces one unique `NEW` case for the supported match, zero cases for no-match or
ambiguous-match records, no duplicates on replay, visible failure on invalid ingestion, and complete
source traceability for every stored snapshot, detected change, and case. The pharmacist remains the
decision-maker.

Refer to [data-model.md](data-model.md) for entity and state requirements and
[contracts/ingestion-and-case-view.md](contracts/ingestion-and-case-view.md) for boundary data
requirements.
