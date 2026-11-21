# Feature 016: Supply Signals

**Status:** Approved specification (requested by Oli on 2026-11-21: roadmap direction A, second feature)
**Branch:** feature/supply-signals

## 1. Objective

For any package or product, put the supply facts Fimea publishes side by side: whether its VNR is in the shortage file now, since when and until when (as the company reported), how its listings ran across the files the app has downloaded, what the Basic Register says about marketing and authorisation, which of those fields changed, and how many products with the same active substances have a listed shortage now.

## 2. Scope

### In scope
- Facts and date arithmetic on published dates only.

### Out of scope
- Forecasts, scores, rankings, "risk" wording or any judgement of significance (constitution; clinical-wording guards; roadmap §2.2).
- Interpreting the file's `Valid` value; it is shown as published.
- Shortage data from sources other than Fimea's open file.

## 3. Requirements

- **FR-001** `GET /api/medicine-catalogue/packages/{pakkaustunnus}/supply-signals` and `.../products/{product_reference}/supply-signals` MUST return, for the record's VNRs: status `LISTED`, `NOT_LISTED`, `NO_VNR` or `NO_FILE`; the active file's rows as published with days since "unavailable from" and until the estimated end, counted to today's date (UTC), which the answer states.
- **FR-002** Listings MUST be computed from every recorded download of an accepted shortage file, in time order: a listing is a run of consecutive downloads that listed the VNR, with first and last download, number of downloads and whether it is listed now. Stored files are verified against their checksums; unreadable ones are counted and skipped.
- **FR-003** Register facts MUST come from the active release: on the market (Kaupan), marketed from and until, each authorisation's status. Recorded changes of those fields, and packages no longer or newly present, MUST come from feature 013's package history.
- **FR-004** The answer MUST count products with exactly the same active-substance codes and list (up to 20) those with a VNR in the active shortage file.
- **FR-005** The answer and the page MUST state that these are facts as published, that dates are the company's report and the end date an estimate, that nothing is a forecast, and that a medicine not listed is not shown to be available.
- **FR-006** The package and product pages MUST show a "Supply signals" section. Read-only; wording passes the clinical-wording guards.

## 4. Acceptance criteria

1. Synthetic data: a listed package shows its row with correct day counts and one listing over three downloads; a listing that ended shows as not listed now; a gap between downloads gives two listings; no VNR and no file are named; related products with a listed VNR are counted; a Kaupan change 1 → 0 appears as a recorded register change.
2. Real data (2026-11-21 release, 2026-11-20 shortage file): package 87902 (VNR 550343) shows Valid K, unavailable from 2026-11-06 (15 days ago), estimated end 2026-12-01 (in 10 days), and 0 of 13 same-substance products listed.
3. All tests, lint, format, type check and build pass; no contrast failures or horizontal overflow at 320–1440 px.
