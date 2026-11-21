# Feature 012: Implementation Plan

- `frontend/src/app/lastVisit.ts`: `previousVisit()` (session rule, once per page load), `markAllSeen()`, `isNewSince()`, `isDateOnOrAfterVisit()`; storage key `mccl:visits`; every storage access wrapped in try/catch.
- `frontend/src/app/useLastVisit.ts`: `usePreviousVisit()` via `useSyncExternalStore`, so "Mark all as seen" updates every mark at once.
- `frontend/src/app/NewSinceVisit.tsx` (+ CSS): the summary line with its button, and `NewBadge`.
- Pages: `OpenReviewCasesPage` (line), `CaseList` (marks), `MedicineShortagesPage` (marks in the Updated column), `SourceHistoryPage` (line and marks).
- Tests: `app/lastVisit.test.ts`, `pages/open-review-cases/NewSinceVisit.test.tsx`, `pages/source-history/NewSinceVisit.history.test.tsx`; app scope test allows "Mark all as seen".
- No backend change.

## Risks

- Marks belong to one browser; a reviewer on two computers sees different marks. The line names the time it compares with.
