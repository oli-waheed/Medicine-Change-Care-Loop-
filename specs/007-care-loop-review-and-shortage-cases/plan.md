# Feature 007: Implementation Plan

## Recorded reviews (1b)

- **Domain** (`backend/src/domain/case_status_event`): `CaseStatus` gains `IN_PROGRESS`, `REVIEWED_NO_ACTION`, `REVIEWED_FOLLOW_UP`; `HUMAN_TRANSITIONS` encodes FR-002; `CaseStatusEvent` validates system events (only None → NEW) and human events (allowed transition, initials, note rules).
- **Storage**: `case_status_events` gains nullable `reviewer_initials` and `note`. `PipelineStore` adds the columns to existing databases on first use (SQLite `ALTER TABLE ADD COLUMN`), so real-data and demo databases keep their captures. `record_status_event()` changes the status with a conditional `UPDATE … WHERE status = expected` and inserts the event in one transaction (FR-004). `case_payloads(include_reviewed)` returns the stored view with the current status and the full history.
- **API**: `POST /api/review-cases/{caseId}/status-events` (`api/review_cases.py`); `GET /api/open-review-cases?includeReviewed=true`. Contract: `contracts/review-api.md`.
- **Frontend**: `ReviewPanel` (status, steps allowed from the current status, initials kept for the session, note, history), status labels in the list, "Show reviewed cases", a status message after each step.

## Shortage review cases (1a)

- **Comparison and matching** (`services/shortage_review_cases.py`): `detect_shortage_changes()` by VNR (started, changed in Valid/UnavailableFrom/EndingDate/Company, ended); `build_shortage_review()` matches each change per catalogue package with that VNR using the release rule (one record → case, several → ambiguous, none → no match), and records an outcome for every change. Identifiers are hashes of both file checksums, VNR, kind (and package and record), so replays insert nothing.
- **Trigger** (`update_shortages(review=…)`): the active capture before and after storing a download are compared whenever they differ — a new file, or an older file that becomes active again. The first file has no previous capture and is a baseline. Used by the button and by the daily update (`start_shortage_update(app)`).
- **Storage**: shortage cases use the existing `review_cases` and `case_status_events` tables (`change_kind` `SHORTAGE_*`, payload `caseType: SHORTAGE`); outcomes use `change_processing_outcomes` with `source: SHORTAGES`. `available_file_checksums()` includes stored shortage files, so a removed file makes the case's evidence unavailable.
- **Frontend**: `ShortageChangeReview` (row before and after as published, changed columns, package, catalogue release, notice) and `ShortageProvenance` (files, checksums, lines, download times, licence); list label "Shortage started/changed/ended".

## Guards

Backend: the allowed operations add exactly the review endpoint; statuses are exactly the four; only `api/review_cases.py` calls `record_status_event`; later releases never change a reviewed status. Frontend: the page and app scope tests allow exactly the review buttons, the initials and note fields and the "Show reviewed cases" switch; still no `select` or `form`, and no clinical wording.

## Risks

- A free-text note is the reviewer's own text and is not checked for wording.
- Matching shortage changes uses the catalogue release active at the time of the update; the case records which one.
