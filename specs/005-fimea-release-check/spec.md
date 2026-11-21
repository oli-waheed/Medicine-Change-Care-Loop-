# Feature 005: Check for a New Fimea Release from the App

**Status:** Approved specification (requested by Oli on 2026-11-21: button on About the Data, delivered as a Spec Kit feature)
**Branch:** feature/fimea-release-check

**Superseded in part by:** `specs/006-medicine-shortages` — §2 "Out of scope: Scheduling": the backend now also runs this check once a day (feature 006). The n8n workflow is no longer the only automatic route.

**Supersedes in part:** `specs/003-app-shell-and-themes` FR-025 (About the Data adds one button, "Check for new Fimea release"). No case actions, forms or clinical wording are added, and the rest of features 003 and 004 stays in force. Feature 004's out-of-scope item "Source ingestion or upload from the catalogue" is unchanged: the button is not on the catalogue page.

## 1. Objective

Let a user load the latest Fimea Basic Register release from the application, without the command line or n8n, and see plainly whether a new release was loaded.

The check does exactly what the daily n8n workflow does (`workflow/n8n/fimea-basic-register-ingestion.json`): download `Perusrekisteri.xml` from Fimea's open-data address and submit it to the existing ingestion. Duplicate detection, chronology, comparison and review-case creation follow the existing rules unchanged.

## 2. Scope

### In scope
- A "Check for new Fimea release" button on About the Data, with progress and the outcome.
- A backend operation that downloads the release and ingests it in the background, one check at a time.
- Preparing the Medicine Catalogue after a validated release, so the next catalogue visit is fast.

### Out of scope
- Scheduling (the n8n workflow remains the daily, automatic route).
- Choosing another source, uploading a file from the browser, or deleting releases.
- Any change to ingestion, chronology, comparison, matching or review-case rules.
- Changing or closing review cases.
- User accounts or access control (the prototype runs locally).

## 3. User scenario

1. The user opens About the Data and presses "Check for new Fimea release".
2. The page shows progress: downloading, checking and saving, preparing the catalogue.
3. The page then says one of:
   - a new release was loaded, with its release date (Ajopvm) and how many review cases were created;
   - there is no new release, because the file on Fimea's site is the one already loaded;
   - the check did not complete, with the reason (for example Fimea could not be reached, or the file did not validate).

## 4. Functional requirements

- **FR-001**: About the Data MUST show a "Fimea release updates" section with a "Check for new Fimea release" button and a short explanation that it does what the daily workflow does.
- **FR-002**: Pressing the button MUST start one check on the backend. While a check runs, the button MUST be disabled and the page MUST show the current phase in a status region.
- **FR-003**: The backend MUST download from the configured address (`FIMEA_RELEASE_URL`, default `https://data.pilvi.fimea.fi/avoin-data/Perusrekisteri.xml`), enforce `MAX_SOURCE_RELEASE_UPLOAD_BYTES`, and submit the file with the same metadata as the n8n workflow: source name "Fimea Basic Register", release reference = the address (VERIFIED), source order UNKNOWN, retrieval time = now.
- **FR-004**: The downloaded file MUST go through the same ingestion code as `POST /api/source-releases/ingest`, so an unchanged file is recognised and not stored twice, and a newer validated release is compared with the baseline and may create review cases.
- **FR-005**: Only one check MAY run at a time. A second start while one runs MUST report the running check instead of starting another.
- **FR-006**: After a validated release, the backend MUST prepare the catalogue baseline before reporting success. A failure to prepare it MUST NOT fail the check.
- **FR-007**: The outcome MUST distinguish: new release loaded (release date and number of review cases created), no new release (already captured), and not completed (download failure, file not accepted, or unexpected error, with a plain reason).
- **FR-008**: The page MUST NOT request anything until the button is pressed, and MUST stop polling when the check has finished.
- **FR-009**: The check MUST NOT change or close review cases other than creating new ones through the existing comparison. No clinical wording may appear in the section or the API responses.
- **FR-010**: The clinical-scope guards MUST be updated deliberately: the backend allows exactly the two new operations, and the frontend allows exactly the one new button.

## 5. Acceptance criteria

1. On an empty database, a check downloads a valid release and reports "New release loaded" with its release date; the catalogue then shows that release.
2. A second check with the same file reports "No new release" and stores no second copy.
3. A check with a newer release creates the same review cases an upload of that file would.
4. A download failure and a file that does not validate are reported as "The check did not complete" with the reason; nothing becomes the baseline.
5. Starting a check while one runs does not start a second download.
6. Backend and frontend tests, type check, lint, format check and build pass; the page has no contrast failures or horizontal overflow at 320–1440 px.
