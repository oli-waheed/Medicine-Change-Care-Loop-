# Feature 010: Implementation Plan

- **Model**: `release_quality_checks` table (`ReleaseQualityCheckRow`: check id from both release ids, both release ids, time, JSON payload). `create_all` adds it to existing databases.
- **Checks** (`services/release_quality_checks.py`): `build_quality_check()` works on the two ingestion outcomes and the `ComparisonResult` the ingestion already computed, so no second comparison is needed. Clean-up labels reuse feature 008's `cleanup_label()`.
- **Ingestion** (`workflows/ingest_release_file.py`): `_compare_with_baseline()` also returns the check; `PipelineStore.record_ingestion(..., quality_check)` stores it in the same transaction.
- **Backfill** (`workflows/release_quality.py`): `backfill_quality_checks(store, limit=3)` re-reads both captures of pairs without a check (about 25–40 s per real pair) and stores the result; `run_daily_jobs()` calls it and reports `qualityChecksAdded`. `source_order_evidence()` was moved out of `run_ingested_release_to_review()` so both use the same order rule.
- **API**: `GET /api/source-history` (`api/source_history.py`); backend scope guard allows it. Contract: `contracts/source-history-api.md`.
- **Frontend**: `pages/source-history/` (page, API client, styles), navigation item "Source History" with a history icon, App route; tests against a response captured from the real backend (`src/test/sourceHistoryResponse.json`); app scope and shell tests updated for five pages.

## Risks

- The limits are judgement calls; ATTENTION never has an effect beyond the label.
- Backfill reads two real releases in the daily update; it is limited to three pairs per run.
