# Quickstart: Validate the Ingestion-to-Case Flow

This guide sets up the prototype on Windows, runs its checks, and walks through the acceptance run for
the ingestion-to-case pipeline. The expected outputs below were produced on 2026-11-18 from `main`
(after T031). Timings, checksums and `capturedReleaseReference` values differ on every machine and run.

## Prerequisites

- Windows with PowerShell (Windows PowerShell 5.1 or PowerShell 7).
- Git.
- Python 3.13.x with the `py` launcher.
- Node.js 24.15.0 or later in the 24.x LTS line, with its bundled npm. This also satisfies jsdom 30.1.2
  and n8n 2.42.3.
- `curl.exe`, which is included in Windows 10 and 11.
- Exact dependency versions are pinned in `backend/pyproject.toml`, `frontend/package.json` and
  `frontend/package-lock.json`, as recorded in [plan.md](plan.md#t001-stack-decision-record).
- Data: synthetic Fimea release fixtures in `tests/fixtures/fimea-basic-register/` and simulated
  medication records in `backend/seed/` and `tests/fixtures/simulated-medication-records/`. Never use
  real patient-identifiable data.

Run every command from the repository root unless a step says otherwise.

## 1. Backend setup and start

Create the virtual environment and install the backend once:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e "./backend[dev]"
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

Expected: the last command prints a SQLite 3.x version, for example `3.53.1`. SQLite comes with Python;
no database server is installed.

Start the backend (keep this terminal open):

```powershell
python -m uvicorn backend.src.main:app --reload
```

Expected output ends with:

```text
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

- http://127.0.0.1:8000/health returns `{"status":"ok"}`.
- http://127.0.0.1:8000/docs shows the API documentation.
- http://127.0.0.1:8000/ returns `{"detail":"Not Found"}`. This is expected; there is no page at `/`.

The SQLite database and the raw release captures are created automatically in `backend\data\`
(git-ignored). Stop the backend with **Ctrl + C**.

## 2. Backend checks

In a second terminal with the virtual environment active:

```powershell
python -m pytest -q
```

Expected: `181 passed`.

Run Ruff from the `backend` folder, where its settings (`backend/pyproject.toml`) live. Run from the
repository root, Ruff falls back to default settings and reports false errors.

```powershell
Set-Location backend
python -m ruff check src ..\tests
python -m ruff format --check src ..\tests
Set-Location ..
```

Expected: `All checks passed!` and `57 files already formatted`.

## 3. Frontend setup, checks and start

```powershell
Set-Location frontend
npm ci
npm run build
npm run test -- --run
npm run lint
npm run format:check
```

Expected:

- `npm run build` ends with `✓ built in …`.
- `npm run test -- --run` shows `Test Files  1 passed (1)` and `Tests  7 passed (7)`.
- `npm run lint` runs `oxlint` and prints no warnings or errors.
- `npm run format:check` prints `All matched files use Prettier code style!`.

Start the development server (keep this terminal open):

```powershell
npm run dev
```

Expected: `VITE v8.3.3  ready in … ms` and `➜  Local:   http://localhost:5173/`. The page
"Open review cases" shows `There are no NEW review cases.` until releases are ingested, and
`Open cases could not be loaded` if the backend is not running. Vite forwards `/api` requests to
`http://127.0.0.1:8000`.

## 4. Local n8n (scheduled ingestion)

```powershell
npx --yes n8n@2.42.3 start
```

n8n prints the address of its editor, by default http://localhost:5678. Import
`workflow/n8n/fimea-basic-register-ingestion.json`. The workflow:

1. runs daily at 06:00 (Schedule Trigger);
2. downloads `https://data.pilvi.fimea.fi/avoin-data/Perusrekisteri.xml`
   (Fimea open data, CC BY 4.0; see the README);
3. uploads it to `http://host.docker.internal:8000/api/source-releases/ingest`;
4. records a download failure, an upload failure, or a failed validation in separate branches.

Notes:

- `host.docker.internal` works only when n8n runs in Docker. When n8n is started with `npx` as above,
  change the upload node's URL to `http://127.0.0.1:8000/api/source-releases/ingest`. If n8n runs in
  Docker and cannot reach the backend, start the backend with `--host 0.0.0.0`.
- The exported workflow is marked active, so its schedule runs once imported.
- Release order comes from the XML's own `Ajopvm`; the polling time and retrieval time are never used as
  source chronology.
- The real file is about 200 MB, below the 250 MiB upload limit. Each run currently stores a full copy
  in `backend\data\source-releases\`, even when the file has not changed.
- Live data creates cases only for simulated records whose `Pakkaustunnus` is a real package identifier
  in the register; the seed records match the synthetic fixtures only.

## 5. Acceptance run

The acceptance run uses the synthetic fixtures and the fixture medication records, which cover all match
scenarios against `prior-release.xml` → `current-release.xml`:

| Package | Change | Simulated records | Expected outcome |
|---|---|---|---|
| `SIM-PKG-100` | name and descriptor changed | `SIM-MED-001` | `MATCHED`, one NEW case |
| `SIM-PKG-300` | no longer present | `SIM-MED-003`, `SIM-MED-004` | `AMBIGUOUS`, no case |
| `SIM-PKG-500` | pack-size text changed | none | `NO_MATCH`, no case |
| `SIM-PKG-200` | unchanged | none | no outcome |

### Prepare a clean run

Stop the backend if it is running (**Ctrl + C**), then in the backend terminal:

```powershell
Remove-Item -Recurse -Force backend\data -ErrorAction SilentlyContinue
$env:SIMULATED_MEDICATION_RECORDS_PATH = "tests\fixtures\simulated-medication-records\medication-records.json"
python -m uvicorn backend.src.main:app --reload
```

The environment variable applies only to this terminal. Without it, the backend uses the demo records
in `backend/seed/`, which give two cases (`SIM-PKG-100` and `SIM-PKG-300`) and one `NO_MATCH`.

In a second terminal at the repository root, define a helper for uploads. The release reference is read
from a file, which avoids quoting JSON on the PowerShell command line:

```powershell
function Ingest($file, $retrievedAt) {
  curl.exe -s -X POST http://127.0.0.1:8000/api/source-releases/ingest `
    -F "file=@tests/fixtures/fimea-basic-register/$file" `
    -F "sourceName=Fimea Basic Register" `
    -F "sourceReleaseReference=<tests/fixtures/acceptance/source-release-reference.json" `
    -F "retrievedAt=$retrievedAt"
}
```

Uploads can also be made from http://127.0.0.1:8000/docs (**POST /api/source-releases/ingest →
Try it out**).

### Steps and expected results

1. **Baseline release.**

   ```powershell
   Ingest prior-release.xml 2099-01-03T06:00:00Z
   (Invoke-RestMethod http://127.0.0.1:8000/api/open-review-cases).Count
   ```

   Expected: `{"processingStatus":"VALIDATED","chronologyStatus":"AVAILABLE","capturedReleaseReference":"sha256-…","failureDetail":null}`
   and `0`. The first release is a baseline only.

2. **Newer release.**

   ```powershell
   Ingest current-release.xml 2099-01-04T06:00:00Z
   ```

   Expected: `"processingStatus":"VALIDATED"` and `"chronologyStatus":"AVAILABLE"`.

3. **Exactly one NEW case for the unique match.**

   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/api/open-review-cases |
     Select-Object @{n='record';e={$_.matchedRecord.recordId}}, medicineIdentifier,
       @{n='kind';e={$_.changeSet.kind}}, @{n='fields';e={$_.changeSet.changes.field -join ', '}}, status
   ```

   Expected: one row, `SIM-MED-001`, `SIM-PKG-100`, `FIELDS_CHANGED`,
   `Laakevalmiste/Kauppanimi, Pakkaus/JulkinenTarkenne`, `NEW`.

4. **Honest outcomes for no-match and ambiguous changes.**

   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/api/change-processing-outcomes |
     Select-Object medicineIdentifier, result, reason,
       @{n='records';e={$_.simulatedRecords.recordId -join ', '}}, @{n='cases';e={$_.caseIds.Count}}
   ```

   Expected:

   | medicineIdentifier | result | reason | records | cases |
   |---|---|---|---|---|
   | SIM-PKG-100 | MATCHED | UNIQUE_EXACT_PACKAGE_MATCH | SIM-MED-001 | 1 |
   | SIM-PKG-300 | AMBIGUOUS | MULTIPLE_SIMULATED_RECORDS | SIM-MED-003, SIM-MED-004 | 0 |
   | SIM-PKG-500 | NO_MATCH | NO_SIMULATED_RECORD | | 0 |

   http://127.0.0.1:8000/api/change-processing-outcomes?result=NO_MATCH&result=AMBIGUOUS returns only
   `SIM-PKG-300` and `SIM-PKG-500`.

5. **Pharmacist view.** Open http://localhost:5173/. Expected: `Cases (1)` with "Fictional Product
   Amber", `SIM-PKG-100`, "2 field changes". The case shows before/after values for both fields, the
   matched simulated record and person, prior and current source evidence (file name, checksum, record
   locator, release date `2099-01-01` / `2099-01-02`, retrieval time, evidence classification), the
   source order basis (`Ajopvm`), and the statement that the case does not make a clinical decision.
   There are no buttons to close, resolve or recommend.

6. **Replay creates no duplicates.**

   ```powershell
   Ingest current-release.xml 2099-01-04T06:00:00Z
   (Invoke-RestMethod http://127.0.0.1:8000/api/open-review-cases).Count
   (Invoke-RestMethod http://127.0.0.1:8000/api/change-processing-outcomes).Count
   ```

   Expected: `VALIDATED` with the same `capturedReleaseReference` as in step 2, then `1` and `3`.

7. **Malformed input fails visibly.**

   ```powershell
   Ingest malformed-release.xml 2099-01-05T06:00:00Z
   ```

   Expected: `"processingStatus":"FAILED"`, `"chronologyStatus":"UNAVAILABLE"` and
   `"failureDetail":"Source release validation failed: mismatched tag: line 8, column 42"`. The raw file
   is still captured for traceability; the case count stays `1`.

8. **Unknown source order is not compared.**

   ```powershell
   Ingest ordering-unknown-release.xml 2099-01-06T06:00:00Z
   ```

   Expected: `"processingStatus":"VALIDATED"` and `"chronologyStatus":"UNAVAILABLE"`. The release has no
   `Ajopvm`, so it is stored but never compared; the case count stays `1`.

9. **Unavailable source.** A failed download never reaches the backend. In n8n, temporarily change the
   download URL to a non-existent file and execute the workflow. Expected: the "Record Download
   Failure" node runs and the upload node does not.

10. **Simulated data and scope.** Confirm that every record and person reference shown starts with
    `SIM-`, and that neither the view nor the API diagnoses, recommends treatment or substitution,
    sets urgency, changes case status, or closes a case.

To return to the demo records afterwards, stop the backend, run
`Remove-Item Env:SIMULATED_MEDICATION_RECORDS_PATH`, delete `backend\data`, and start the backend again.

## Expected result

The acceptance set produces one NEW case for the unique match, a `NO_MATCH` and an `AMBIGUOUS` outcome
with no cases, no duplicates on replay, a visible `FAILED` result for malformed input, no comparison for
a release without verifiable order, and complete source traceability for every stored release, change,
case and outcome. The pharmacist remains the decision-maker.

## Acceptance results (T034)

Record the manual run here.

- Date:
- Tester:
- Commit (`git log --oneline -1`):

| Step | Expected | Actual | Pass |
|---|---|---|---|
| 1 Baseline release | `VALIDATED`, `AVAILABLE`, 0 cases | | |
| 2 Newer release | `VALIDATED`, `AVAILABLE` | | |
| 3 Unique match | 1 NEW case: `SIM-MED-001` / `SIM-PKG-100` | | |
| 4 Outcomes | `MATCHED`, `AMBIGUOUS`, `NO_MATCH` as in the table | | |
| 5 Pharmacist view | 1 case with full evidence, no decision actions | | |
| 6 Replay | same release reference; still 1 case and 3 outcomes | | |
| 7 Malformed input | `FAILED` with reason; still 1 case | | |
| 8 Unknown order | `VALIDATED`, `UNAVAILABLE`; still 1 case | | |
| 9 Unavailable source | n8n download-failure branch runs | | |
| 10 Simulated data and scope | only `SIM-` data; no clinical actions | | |

Refer to [data-model.md](data-model.md) for entity and state requirements and
[contracts/ingestion-and-case-view.md](contracts/ingestion-and-case-view.md) for boundary data
requirements.
