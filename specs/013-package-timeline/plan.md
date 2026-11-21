# Feature 013: Implementation Plan

- **Models**: `package_history_pairs` (one row per recorded pair, with dates and event count) and `package_history_events` (pair, Pakkaustunnus, kind, changes as JSON).
- **Service** (`services/package_history.py`): `build_package_history()` from the two ingestion outcomes and the `ComparisonResult` the ingestion already has.
- **Ingestion** (`workflows/ingest_release_file.py`): `_compare_with_baseline()` returns a `_Comparison` (cases, outcomes, quality check, history); `record_ingestion()` stores all in one transaction.
- **Backfill** (`workflows/release_quality.py`): `backfill_release_pairs()` completes checks and histories together; `backfill_quality_checks()` kept for feature 010 callers; the daily update reports `qualityChecksAdded` and `packageHistoriesAdded`.
- **API**: `GET /api/medicine-catalogue/packages/{pakkaustunnus}/history` (`api/medicine_catalogue.py`), allowed in the backend scope guard. Contract: `contracts/package-history-api.md`.
- **Frontend**: `PackageHistoryCard` on `PackageDetailPanel`, `fetchPackageHistory()`, styles; test fixtures captured from the real backend (`src/test/packageHistoryResponses.json`), served by `catalogueFetch`.

## Storage

The real pair adds 2,918 events; the demo database grew to about 10 MB.
