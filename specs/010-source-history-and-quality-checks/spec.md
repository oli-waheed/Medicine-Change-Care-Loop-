# Feature 010: Source History and Automatic Release Quality Checks

**Status:** Approved specification (requested by Oli on 2026-11-21: ideas 2c and 2d, second in the order 4 → 2c+2d → 3f → 3g → 2e)
**Branch:** feature/source-history-and-quality-checks

**Supersedes in part:**
- `specs/003-app-shell-and-themes` FR-001/FR-002 (as already amended by 004 and 006): the sidebar gets a fifth page, Source History.

## 1. Objective

Make the app's evidence trail visible in one place, and check every new Basic Register release automatically instead of by hand (`docs/validation/2026-11-21-real-release-comparison.md`, `backend/tools/compare_releases.py`).

## 2. Scope

### In scope
- A read-only Source History page: every stored Basic Register release and shortage file, with dates, downloads, size, checksum and whether the stored file is still available.
- An automatic quality check of each compared release pair, stored with the release and shown on the page.
- Checking, during the daily update, consecutive release pairs that have no check yet (for example pairs compared before this feature).

### Out of scope
- Blocking, rejecting or delaying a release because of a check; changing or hiding a change or a case.
- Deleting or downloading files from the page; any control on the page.
- Checks of shortage files (they are already validated column by column when downloaded, feature 006).

## 3. Requirements

- **FR-001** When a newer release is compared with the baseline, a quality check of that pair MUST be stored in the same transaction as the capture, cases and outcomes.
- **FR-002** A check MUST contain: release order (Ajopvm strictly increasing), package-ID uniqueness, the share of the prior release's package IDs still present (limit ≥ 99 %), the share no longer present (limit ≤ 1 %), the share of packages with changed fields (limit ≤ 10 %), the number of likely source clean-ups (feature 008 labels, information only) and the number of VNRs shared by several packages (information only); and the counts behind them, including VNR gained/lost/changed.
- **FR-003** Each check MUST have the status `PASSED`, `ATTENTION` or `INFO`, and the pair an overall `PASSED` or `ATTENTION`. `ATTENTION` only marks a pair for a person to look at; it MUST NOT stop, change or hide anything.
- **FR-004** The daily update MUST, after its downloads, check up to three of the newest consecutive release pairs without a check. A check is stored once per pair.
- **FR-005** `GET /api/source-history` MUST return the stored releases (newest Ajopvm first), the checks (newest first), the pairs without a check, and the stored shortage files (newest first). It MUST be read-only.
- **FR-006** The Source History page MUST show the checks, the releases and the shortage files, mark the catalogue release and the shortage file shown now, name pairs not checked yet, and offer no controls. Wording MUST stay non-clinical.

## 4. Acceptance criteria

1. Synthetic releases: a compared pair gets one stored check with the expected counts; an unchanged pair passes; a pair loaded out of order is listed as unchecked and the backfill adds its check once.
2. On the two real releases (2026-10-06 → 2026-11-21) the backfilled check passes with the same numbers as `backend/tools/compare_releases.py`: 146,021 IDs kept (99.99 %), 21 removed, 2,050 changed (1.40 %), 957 clean-ups, 54 shared VNRs.
3. The page lists releases and shortage files with downloads and checksums, sends one GET and has no controls.
4. All tests, lint, format, type check and build pass; no contrast failures or horizontal overflow at 320–1440 px.

## 5. Decisions (2026-11-21)

- D1 Limits 99 % kept, 1 % removed, 10 % changed, chosen from the real pair (99.99 %, 0.01 %, 1.4 %) with ample room; kept as constants in `services/release_quality_checks.py` for the team to tune.
- D2 Source History is its own page (not a section of About the Data), between Medicine Shortages and About the Data.
