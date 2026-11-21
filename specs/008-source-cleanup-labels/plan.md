# Feature 008: Implementation Plan

- **Rules** (`backend/src/services/source_cleanup_labels.py`): pure functions `formatting_only()`, `cleanup_label()` and `with_cleanup_labels()` on the stored case view (FR-001–FR-003). No database change.
- **API**: `with_evidence_availability()` in `schemas/open_review_cases.py`, used by both case endpoints, adds the labels as the last step (FR-004). Contract: `contracts/cleanup-labels.md`.
- **Fixture**: `tests/fixtures/fimea-basic-register/cleanup-release.xml`, the synthetic current release with one formatting-only, one substance-only and one mixed package change.
- **Frontend**: `CLEANUP_LABELS` and `cleanupLabel()` in `changeSummary.ts`; badge in `CaseList`, the set-aside switch (local state, FR-006); notice in `CaseDetail`; per-field marker in `UpdatedPackageReview`; neutral styles in `OpenReviewCasesPage.css`.
- **Guards**: the app scope test allows the one new checkbox; no new API operation, no `select` or `form`; clinical-word checks on the new text.

## Risks

- Case-folding treats "STADA" and "Stada" as the same; that is the purpose, and the values stay visible.
- The substance label also covers real renames (for example a substance recoded as its monohydrate); the notice says the values are shown and must be read.
