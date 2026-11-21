# Feature 007: Close the Care Loop — Recorded Reviews and Shortage Review Cases

**Status:** Approved specification (requested and approved by Oli on 2026-11-21: ideas 1b and 1a, three review outcomes, reopening with a note, first shortage file as baseline)
**Branch:** feature/care-loop-review-and-shortage-cases

**Supersedes in part:**
- `specs/001-ingestion-case-pipeline`: NEW stops being the only case status; a pharmacist can record a review (§4, FR-001–FR-010). Later releases still never change or close a case.
- `specs/003-app-shell-and-themes` FR-025 and `specs/002` FR-010: the case page gets review controls (three outcome buttons and a note field), the first form controls on that page.
- `specs/006-medicine-shortages` §3 "Out of scope: linking shortages to review cases": shortage changes now create review cases (§5).

## 1. Objective

Make the loop "source change → matched record → pharmacist review → recorded outcome" complete:

1. A pharmacist can record what they did with a case, with a note, and every step is kept as history.
2. A change in Fimea's shortage data that concerns a package used by a simulated record creates a review case, in the same queue and with the same evidence standard as release changes.

## 2. Scope

### In scope
- Three review outcomes on any case, a required note for the two "Reviewed" outcomes, a status history on every case.
- Case list shows open cases (New and In progress) by default and can show reviewed cases.
- Shortage review cases from consecutive accepted shortage files, matched to simulated records through the catalogue (VNR → package → record).

### Out of scope
- Automatic status changes of any kind (the system never sets a review outcome or closes a case).
- User accounts or sign-in; reviews are attributed by the reviewer's initials typed with the note.
- Deleting cases or status history; editing a recorded note (a correction is a new status event).
- Suggesting other products, judging the effect of a shortage, or clinical wording.
- VNR change detection in Basic Register comparisons (decision T018 of feature 006 is separate).

## 3. Users and scenarios

- **Pharmacist reviewer:** opens a NEW case, marks it "In progress", checks the evidence, then records "Reviewed – no action needed" or "Reviewed – follow-up needed" with a note. The case leaves the open list and stays findable under "Show reviewed". Its history shows who did what and when.
- **A shortage begins for a package in a simulated record:** the next shortage update creates a NEW "Shortage started" case with the shortage row as published, its source file, checksum and download time, and the matching record.

## 4. Requirements — recorded reviews (1b)

- **FR-001** Case statuses MUST be exactly: `NEW` (created by the system), `IN_PROGRESS`, `REVIEWED_NO_ACTION`, `REVIEWED_FOLLOW_UP` (set only by a person).
- **FR-002** Allowed human transitions: NEW → IN_PROGRESS, NEW → either Reviewed outcome, IN_PROGRESS → either Reviewed outcome, a Reviewed outcome → IN_PROGRESS (reopen). Any other transition MUST be rejected (409) and change nothing.
- **FR-003** Every transition MUST be recorded as a status event with from-status, to-status, time (UTC), reviewer initials (1–10 letters, required) and note (required for the Reviewed outcomes and for reopening, at most 1,000 characters). Events MUST never be edited or deleted.
- **FR-004** A transition request MUST name the status it expects the case to have; if the case has changed meanwhile, the request MUST be rejected (409) so two reviewers cannot overwrite each other.
- **FR-005** The system MUST NOT change a status by itself: ingestion, comparisons, shortage updates and the daily update only create NEW cases.
- **FR-006** The case list MUST show NEW and IN_PROGRESS cases by default, with a "Show reviewed" option; the count and search apply to what is shown.
- **FR-007** Each case MUST show its current status and its full history (oldest first) with time, initials, transition and note.
- **FR-008** The case page MUST offer only the transitions allowed from the current status, as labelled buttons, with an initials field and a note field; it MUST show the server's answer and refresh the case.
- **FR-009** Review wording MUST stay non-clinical: the outcomes describe the review, not a clinical judgement; the clinical-wording guards still apply to all text the app shows (the free-text note is the reviewer's own and is shown as typed).
- **FR-010** The scope guards MUST be updated deliberately: exactly one new API operation (record a status event), the three outcome buttons, the initials and note fields, and the "Show reviewed" control.

## 5. Requirements — shortage review cases (1a)

- **FR-011** When a newly downloaded shortage file is accepted and differs from the previous accepted file, the backend MUST compare the two by VNR and detect: `SHORTAGE_STARTED` (VNR not in the previous file), `SHORTAGE_CHANGED` (any of Valid, UnavailableFrom, EndingDate, Company changed), `SHORTAGE_ENDED` (VNR no longer in the file). The first accepted file is a baseline only and creates no cases.
- **FR-012** A shortage change MUST be matched to simulated records whose Pakkaustunnus is a package of the active catalogue release with that VNR. One case per change and record, never duplicated when the same files are processed again.
- **FR-013** If no catalogue release is available, or the VNR has no package, the change MUST be recorded as an outcome (`NO_MATCH`, with the reason) and create no case, like release changes.
- **FR-014** A shortage case MUST carry, as created and never rewritten: the before and after rows exactly as published (or "not in file"), the changed columns, both files' checksums, download times and line numbers, the source address and licence, the matched record and package, and the catalogue release used for matching.
- **FR-015** Shortage cases MUST appear in the same case list, labelled "Shortage started", "Shortage changed" or "Shortage ended", with their own layout, and use the same review outcomes as release cases.
- **FR-016** Shortage case wording MUST state that dates and status are the company's report to Fimea and the end date an estimate, and MUST NOT point to other products.

## 6. Acceptance criteria

1. A NEW case can be set In progress and then Reviewed with initials and a note; it leaves the default list, appears under "Show reviewed", and its history lists both events. Reopening needs a note and returns it to the list.
2. A disallowed transition, a missing note or initials, or a stale expected status is rejected with no change; nothing in ingestion, shortage updates or the daily update ever changes a status.
3. With the synthetic fixtures: a first shortage file creates no cases; a later file creates exactly one STARTED, CHANGED and ENDED case for the records whose packages have those VNRs; processing the same files again creates nothing new; a VNR without a package records NO_MATCH.
4. Shortage cases show the published values, sources and the non-clinical notice; release cases are unchanged.
5. All backend and frontend tests, type check, lint, format check and build pass; the case page has no contrast failures or horizontal overflow at 320–1440 px; the demo database with real releases still works.

## 7. Decisions (2026-11-21)

- D1 Three human statuses with the names above; reviewers identified by initials, no accounts. (Oli)
- D2 Reopening a reviewed case is allowed, with a note. (Oli)
- D3 The first accepted shortage file is a baseline only. (Oli)
