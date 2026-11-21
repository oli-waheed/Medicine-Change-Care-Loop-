# Feature 011: CSV Exports of Review Cases and Review History

**Status:** Approved specification (requested by Oli on 2026-11-21: idea 3f, third in the order 4 → 2c+2d → 3f → 3g → 2e; CSV only, as decided for feature 007)
**Branch:** feature/csv-exports

**Supersedes in part:**
- `specs/007-care-loop-review-and-shortage-cases` FR-010: the case page gets two download links (no new control that changes anything).

## 1. Objective

Let a reviewer or the team take the review work out of the app: for a report, the course, or a pharmacy's own records.

## 2. Scope

### In scope
- `review-cases.csv`: one row per case (open and reviewed): status, package, simulated record, change, changed fields, clean-up label, sources, evidence availability, creation time, the last review step and the number of steps.
- `review-history.csv`: one row per status event of every case, oldest first.
- Two download links on the Open Review Cases page.

### Out of scope
- Other formats (Excel, PDF); filtering the export; exporting the catalogue, shortages or outcomes.
- Any change to cases through an export.

## 3. Requirements

- **FR-001** `GET /api/exports/review-cases.csv` and `GET /api/exports/review-history.csv` MUST return `text/csv` as an attachment named with the date, and MUST NOT change anything.
- **FR-002** Files MUST be UTF-8 with a byte-order mark, semicolon-separated, CRLF line ends, with a header row, so Excel with Finnish settings opens them in columns. Values with semicolons, quotes or line breaks MUST be quoted.
- **FR-003** A value starting with `=`, `+`, `-`, `@`, a tab or a carriage return MUST be prefixed with an apostrophe, so a spreadsheet never treats it as a formula.
- **FR-004** Statuses and change kinds MUST use the app's labels ("Reviewed – follow-up needed", "Shortage started", …); field paths, values and notes MUST be kept as recorded.
- **FR-005** The case page MUST show both downloads as plain links, also when no case is open.

## 4. Acceptance criteria

1. With synthetic cases: every case is exported once; a reviewed case shows its last reviewer, note (line breaks and semicolons kept) and step count; the history lists the system's NEW event and each review step.
2. Notes that look like formulas are exported as text.
3. Empty databases give header-only files.
4. All tests, lint, format, type check and build pass; the page has no contrast failures or horizontal overflow at 320–1440 px; the browser downloads `review-history-<date>.csv`.
