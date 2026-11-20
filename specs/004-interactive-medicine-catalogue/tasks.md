# Feature 004: Implementation Tasks

**Status (2026-11-20)**:

- T001–T059 are done. T005 was measured on a real Fimea release (190 MB, 146,042 packages; first request after a restart about 36 s, later requests under 1 s). T060 is the user's approval and commit.
- Backend: catalogue service (filters, product and package lookup, substances, comparison, source summary), schemas and six read-only GET endpoints under `/api/medicine-catalogue`; 503 for an unavailable or unreadable baseline, never a fallback. 18 API integration tests; full backend suite 227 passed; Ruff check and format clean.
- Frontend: Medicine Catalogue page with search and filters, package and product details, active-substance explorer, two-product comparison, release and provenance, and loading, empty, error and unavailable states. 14 page tests plus a catalogue scope test; 69 frontend tests passed; TypeScript, Oxlint, Prettier and the production build clean.
- Feature 003 FR-001/FR-002 and FR-025 are superseded in part (see `spec.md`); the clinical-wording guards are unchanged.
- Earlier: T009 in `c9ad6e9`, T007/T008 verified by T027 (`tests/integration/medicine-catalogue/test_medicine_catalogue_baseline.py`).

**Process note**: The service was committed before T060 ("obtain explicit approval before committing or pushing"). From here on, commit only after the related tests pass, and record evidence next to each task.


## Phase 1 — Technical inspection

- [x] T001 Inspect existing backend API schemas and router conventions. *(`research.md` §T001.)*
- [x] T002 Inspect source-release loading and snapshot reconstruction behaviour. *(`research.md` §T002.)*
- [x] T003 Inspect product reference, VNR, and package identity fields. *(`research.md` §T003; GTIN/NTIN are not normalised today.)*
- [x] T004 Inspect frontend routing, navigation, and existing UI components. *(`research.md` §T004; corrected the Tailwind reference in `plan.md`.)*
- [x] T005 Inspect captured release size and assess loading performance. *(`research.md` §T005: real release 2026-10-06, 190 MB, 146,042 packages; reconstruction 32.8 s and about 2.3 GB; warm requests 0.05–0.7 s. The substance explorer was changed to pages of 25 with occurrences on request.)*
- [x] T006 Document the proposed API response contracts before implementation. *(`contracts/catalogue-api.md`; proposed, for review before T019.)*

## Phase 2 — Backend catalogue service

- [x] T007 Create the medicine catalogue service using the existing baseline selector. *(`75ea1a2`; verified by T027.)*
- [x] T008 Reconstruct snapshots using the existing captured-release loader. *(`75ea1a2`, in-memory cache of one release; verified by T027.)*
- [x] T009 Implement catalogue search. *(`c9ad6e9`; 8 unit tests. FR-002.)*
- [x] T010 Implement catalogue filters. *(`backend/src/services/medicine_catalogue.py` `filter()` with `CatalogueFilters` (active substance, ATC prefix, form, route, availability, VNR, `missing`); verified by T028.)*
- [x] T011 Implement product detail lookup. *(`backend/src/services/medicine_catalogue.py` `product()` / `ProductView`; substances are package-level, so a product lists them only when all its packages agree. Verified by T029.)*
- [x] T012 Implement package detail lookup by pakkaustunnus. *(`backend/src/services/medicine_catalogue.py` `package()` / `PackageView`; verified by T029.)*
- [x] T013 Implement active-substance exploration. *(`backend/src/services/medicine_catalogue.py` `active_substances()` using the change-detection substance identity; source order and repeats kept. Verified by T030.)*
- [x] T014 Implement product comparison using approved source fields. *(`backend/src/services/medicine_catalogue.py` `compare()` over `project_snapshot_fields()` paths under `Laakevalmiste/` and `Laakeaine/`; change detection unchanged. Verified by T034.)*
- [x] T015 Implement source-release and provenance information. *(`backend/src/services/medicine_catalogue.py` `source_summary()`; release and per-package provenance in `backend/src/schemas/medicine_catalogue.py`. Verified by T033.)*
- [x] T016 Expose VNR explicitly and preserve missing values. *(VNR is a SourceValue in every package response; missing stays `missing`. Verified by T031.)*
- [x] T017 Implement VNR-based grouping only where source evidence supports it. *(`same_vnr_packages()`: only equal VNR values of state `value`; packages never merged. Verified by T032.)*
- [x] T018 Handle missing or unavailable validated baseline. *(`CatalogueUnavailableError` and `None` map to `503 CATALOGUE_UNAVAILABLE`; unreadable capture to `503 CATALOGUE_SOURCE_UNREADABLE`. Verified by T035.)*

## Phase 3 — Backend API

- [x] T019 Add catalogue API response schemas. *(`backend/src/schemas/medicine_catalogue.py`; `contracts/catalogue-api.md` updated to match.)*
- [x] T020 Add GET /api/medicine-catalogue. *(`backend/src/api/medicine_catalogue.py`.)*
- [x] T021 Add GET /api/medicine-catalogue/products/{product_reference}. *(`backend/src/api/medicine_catalogue.py`.)*
- [x] T022 Add GET /api/medicine-catalogue/packages/{pakkaustunnus}. *(`backend/src/api/medicine_catalogue.py`.)*
- [x] T023 Add GET /api/medicine-catalogue/active-substances. *(`backend/src/api/medicine_catalogue.py`.)*
- [x] T024 Add GET /api/medicine-catalogue/compare. *(`backend/src/api/medicine_catalogue.py`.)*
- [x] T025 Add GET /api/medicine-catalogue/source. *(`backend/src/api/medicine_catalogue.py`.)*
- [x] T026 Register the catalogue router in the application. *(`backend/src/main.py`; the clinical-scope guard lists the six GET operations deliberately.)*

## Phase 4 — Backend tests

- [x] T027 Test validated baseline selection and unavailable baseline, including cache reuse, cache reset when the baseline disappears, and the error when a capture cannot be reconstructed as validated. *(10 integration tests in `tests/integration/medicine-catalogue/`.)*
- [x] T028 Test catalogue search and filters. *(`test_medicine_catalogue_api.py`: listing order, search, every filter, `missing` vs empty, paging and 422s.)*
- [x] T029 Test product and package detail lookup. *(`test_medicine_catalogue_api.py`: product with empty route and registrations; package details; 404s.)*
- [x] T030 Test active-substance exploration. *(`test_medicine_catalogue_api.py`: substance order and repeated occurrences.)*
- [x] T031 Test VNR visibility, search, and missing values. *(`test_medicine_catalogue_api.py`: VNR search, explicit and missing VNR.)*
- [x] T032 Test pakkaustunnus and VNR identity separation. *(`test_medicine_catalogue_api.py`: shared VNR grouping without merging identities.)*
- [x] T033 Test provenance and source-release information. *(`test_medicine_catalogue_api.py`: provenance and source summary.)*
- [x] T034 Test product comparison and existing comparison-field preservation. *(`test_medicine_catalogue_api.py`: comparison paths cover the product paths of `project_snapshot_fields()`; parameter errors; notice.)*
- [x] T035 Test source integrity and error handling. *(`test_medicine_catalogue_api.py`: reads change no captures, cases, outcomes or baseline; no clinical wording; 503 unavailable and unreadable.)*

## Phase 5 — Frontend catalogue

- [x] T036 Add the Medicine Catalogue navigation entry. *(`navigation.ts`, `Sidebar.tsx`, `icons.tsx`, `App.tsx`; app-level tests updated deliberately.)*
- [x] T037 Create the catalogue page and API client integration. *(`frontend/src/pages/medicine-catalogue/``MedicineCataloguePage.tsx`, `medicineCatalogue.ts`.)*
- [x] T038 Implement search and filters. *(`CatalogueSearch.tsx` (debounced search, filters, paging).)*
- [x] T039 Implement product detail view. *(`ProductDetailPanel.tsx`.)*
- [x] T040 Implement package detail view. *(`PackageDetailPanel.tsx`.)*
- [x] T041 Implement active-substance explorer. *(`SubstanceExplorer.tsx`.)*
- [x] T042 Implement two-product comparison. *(`ProductComparison.tsx` with the factual notice.)*
- [x] T043 Display VNR clearly and distinguish it from package identity. *(`IdentityBlock` shows Package ID and VNR as separate values; VNR on every result.)*
- [x] T044 Display source and provenance information. *(`ReleaseSummary` and `ProvenanceCard`.)*
- [x] T045 Implement loading, empty, and error states. *(`CatalogueStates.tsx`: loading, no matches, unavailable, unreadable and not-found.)*
- [x] T046 Verify responsive layouts and accessibility. *(Browser check of 42 catalogue views at 320–1440 px: no text-contrast failures, no horizontal overflow; keyboard reaches search, filters and results, and opening a record moves focus to the detail.)*

## Phase 6 — Frontend tests and regression

- [x] T047 Test catalogue navigation and page loading. *(`MedicineCataloguePage.test.tsx`: navigation, release summary, listing; unavailable and unreadable states. `App.scope.test.tsx`: controls and GET-only requests.)*
- [x] T048 Test search and filters. *(`MedicineCataloguePage.test.tsx`: query string for search and every filter, missing-VNR filter, no-match message, debouncing.)*
- [x] T049 Test product and package details. *(`MedicineCataloguePage.test.tsx`: package fields, substances, provenance; product with empty route; not-found message.)*
- [x] T050 Test active-substance exploration. *(`MedicineCataloguePage.test.tsx`: occurrences in source order with repeats; search; opening a package.)*
- [x] T051 Test product comparison. *(`MedicineCataloguePage.test.tsx`: two products, Same/Different per field, no occurrences, notice.)*
- [x] T052 Test VNR and missing-value presentation. *(`MedicineCataloguePage.test.tsx`: missing VNR shown as missing and never grouped; shared VNR linked, identities kept apart.)*
- [x] T053 Run backend tests. *(`python -m pytest`: 227 passed. Ruff check and format clean.)*
- [x] T054 Run frontend tests. *(`npx vitest run`: 69 passed (9 files). Oxlint and Prettier clean.)*
- [x] T055 Run TypeScript checks. *(`npx tsc -b`: no errors.)*
- [x] T056 Run the production build. *(`npm run build`: built.)*
- [x] T057 Review Git diff and confirm no unrelated changes. *(Diff limited to the catalogue backend, frontend, tests, the 003/004 specs and README; no BOMs or CRLF.)*

## Phase 7 — Completion

- [x] T058 Verify all Feature 004 acceptance criteria. *(Acceptance criteria 1–12 of `spec.md` §11 checked against the tests above and against the real release of T005.)*
- [x] T059 Summarize implementation and test results. *(Summary in the status block above.)*
- [x] T060 Obtain explicit approval before committing or pushing. *(Approved by Oli on 2026-11-20; committed in 3da9f04 and f3a06a2.)*
