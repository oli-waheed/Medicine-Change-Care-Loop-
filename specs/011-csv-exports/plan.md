# Feature 011: Implementation Plan

- **API** (`backend/src/api/exports.py`): both endpoints read `PipelineStore.case_payloads(include_reviewed=True)` through `with_evidence_availability()` (so feature 008 labels and evidence availability are included) and write CSV with the standard `csv` module. Backend scope guard allows the two GETs. Contract: `contracts/exports-api.md`.
- **Frontend**: `EXPORT_CASES_URL` and `EXPORT_HISTORY_URL` in `openReviewCases.ts`; links with `download` in the page header; styles in `OpenReviewCasesPage.css`; app scope test allows the two links.
- **Tests**: `tests/integration/exports/` (columns and values, reviewed case and history, formula prefix, read-only, empty files, shortage cases from the captured 007 responses); `ExportLinks.test.tsx`.

## Risks

- A spreadsheet that does not read the byte-order mark may show "Ã¤" for "ä"; Excel and LibreOffice read it.
