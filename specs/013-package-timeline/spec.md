# Feature 013: Package Timeline

**Status:** Approved specification (requested by Oli on 2026-11-21: idea 2e, last in the order 4 → 2c+2d → 3f → 3g → 2e)
**Branch:** feature/package-timeline

## 1. Objective

Show, for any package in the Medicine Catalogue, what changed between the compared releases, with the values before and after as published. Until now only the names of changed fields were stored (in matching outcomes), and only cases had values.

## 2. Scope

### In scope
- Recording, for every compared release pair, each package that changed (with all field values before and after), is no longer present, or is newly present.
- Completing the record for pairs compared before this feature, in the daily update (with feature 010's backfill).
- A "Change history" section on the catalogue's package page.

### Out of scope
- Rebuilding history for releases that are no longer stored.
- History for products or substances as such; shortage history (Source History lists the files).
- Any change to cases, matching or the catalogue release.

## 3. Requirements

- **FR-001** When a newer release is compared with the baseline, its package history MUST be stored in the same transaction as the capture, cases, outcomes and quality check: one event per changed (`FIELDS_CHANGED`, with values), removed (`NO_LONGER_PRESENT`) and new (`NEWLY_PRESENT`) package.
- **FR-002** History MUST be stored once per release pair and never rewritten.
- **FR-003** The daily update MUST complete up to three of the newest consecutive pairs that lack a quality check or a history, reading both releases once for both records.
- **FR-004** `GET /api/medicine-catalogue/packages/{pakkaustunnus}/history` MUST return the recorded pairs and the package's events, newest first, with feature 008 labels; it MUST work without the catalogue release in memory and change nothing.
- **FR-005** The package page MUST show the events with field paths and values as published, say when no pair has been compared or nothing changed, and stay non-clinical.

## 4. Acceptance criteria

1. Synthetic releases: a changed package has an event with its values; removed and new packages have their events; three releases give two events, newest first, the newest labelled "Spacing or letter case only".
2. A pair loaded out of order is completed once by the backfill.
3. Real releases (2026-10-06 → 2026-11-21): the backfill records 2,918 events (2,050 changed, 21 removed, 847 new) in about 40 s; package 161367 shows its nine active-substance changes and 200509 its letter-case change.
4. All tests, lint, format, type check and build pass; no contrast failures or horizontal overflow at 320–1440 px.
