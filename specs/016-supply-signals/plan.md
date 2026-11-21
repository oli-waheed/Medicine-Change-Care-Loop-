# Feature 016: Implementation Plan

- **Store**: `PipelineStore.shortage_timeline()` — every retrieval of an accepted shortage capture, oldest first.
- **Service** (`services/supply_signals.py`): `StoredShortageFiles` (parsed, checksum-verified stored files, cached by checksum; `app.state.stored_shortage_files`); `supply_signals()` builds status, current rows with day counts, listings, register facts, register changes (from `package_history_events`) and related products (feature 015's `LinkIndex`).
- **API** (`api/medicine_catalogue.py`): two GET endpoints sharing `_supply()`; the active file comes from the Shortages page's reader. Backend scope guard allows them. Contract: `contracts/supply-signals-api.md`.
- **Frontend**: `SupplySignalsCard` on the package and product pages, before Linked records; `fetchSupplySignals` and types; styles.
- **Tests**: `tests/integration/supply-signals/`; `SupplySignals.test.tsx` against responses captured from the real backend (`src/test/supplySignalsResponses.json`, `asOf` fixed to 2099-01-21 with day counts recomputed), served by `catalogueFetch`.
