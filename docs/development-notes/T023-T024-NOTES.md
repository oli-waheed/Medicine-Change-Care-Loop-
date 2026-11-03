# T023–T024 implementation notes

## Purpose

- T023 captures immutable raw source-release files with source identity, source
  reference/order evidence, retrieval time, file names, SHA-256 checksums and
  record locators.
- T024 validates source file access and checksums, normalizes complete XML
  releases, and returns explicit failed outcomes without partial snapshots when
  acquisition or validation fails.

## Implementation

`backend/src/services/capture_source_release.py` stores captured bytes and a
manifest under a content-derived release directory. Repeated identical capture
is idempotent; if an existing capture or raw file differs, it raises an error
instead of silently overwriting it. The manifest retains file names, checksums,
source evidence, retrieval time and supplied record locators.

`backend/src/services/ingest_source_release.py` verifies each referenced file's
SHA-256 before capture, then reuses
`normalize_basic_register_release.py`. All files and package identifiers are
validated before snapshots are returned. Inaccessible, incomplete, checksum
mismatched, malformed or duplicate-record input produces a failed outcome with
no snapshots.

Data validation and chronological comparison eligibility are separate states.
A release with unknown, empty or unverified source order may still be
`VALIDATED` and return normalized snapshots. Its source-order evidence is
preserved, while `chronology_status` is `UNAVAILABLE` and
`verified_chronological_order` is false. Retrieval time is never substituted
for source order. No verified release-to-release comparison should use such a
release as chronological evidence.

## Files changed for T023–T024

- `backend/src/services/capture_source_release.py`
- `backend/src/services/ingest_source_release.py`
- `tests/unit/source-release-capture/test_capture_source_release.py`
- `tests/contract/source-release-ingestion/test_source_release_ingestion.py`
- `specs/001-ingestion-case-pipeline/contracts/ingestion-and-case-view.md`
- `specs/001-ingestion-case-pipeline/tasks.md`

## Verification

Full backend test suite, from the repository root:

```powershell
$env:PYTHONPATH='backend'; backend\.venv\Scripts\python.exe -m pytest tests -q
```

Result: **101 passed**.

Ruff lint and format checks, from `backend`:

```powershell
.\.venv\Scripts\ruff.exe check src\services\capture_source_release.py src\services\ingest_source_release.py ..\tests\contract\source-release-ingestion\test_source_release_ingestion.py ..\tests\unit\source-release-capture\test_capture_source_release.py
.\.venv\Scripts\ruff.exe format --check src\services\capture_source_release.py src\services\ingest_source_release.py ..\tests\contract\source-release-ingestion\test_source_release_ingestion.py ..\tests\unit\source-release-capture\test_capture_source_release.py
```

Result: **All checks passed; four files already formatted**. `git diff --check`
also passed.

The first full-suite attempt could not collect two test modules because FastAPI
was missing from the local virtual environment. The project dependencies were
installed from `backend/pyproject.toml`; the full suite then passed.

## AI use

The user submitted the requirements through VS Code Copilot Chat; Copilot
assisted with implementation and test execution. During review, the handling of
unknown source order was found inconsistent with the original contract and
existing test, which allow successful normalization while prohibiting verified
chronological comparison. The implementation and tests were then corrected to
preserve that distinction. This note records that AI-assisted process and does
not claim the user independently wrote all code or that additional manual
checks were performed.

## Limitations

- The implementation supports the selected Fimea Basic Register XML format and
  its current full-coverage normalization rules; real-source schema and order
  semantics remain unverified.
- Source content references are currently read as local filesystem paths.
- XML is parsed in memory; memory use for large live releases has not been
  profiled.
- Unknown or unverified source order prevents verified chronological comparison,
  even when file and snapshot validation succeeds.
- Scheduled retrieval, workflow failure reporting and downstream comparison
  integration remain outside T023–T024.
