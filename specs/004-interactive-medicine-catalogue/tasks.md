# Feature 004: Implementation Tasks

## Phase 1 — Technical inspection

- [ ] T001 Inspect existing backend API schemas and router conventions.
- [ ] T002 Inspect source-release loading and snapshot reconstruction behaviour.
- [ ] T003 Inspect product reference, VNR, and package identity fields.
- [ ] T004 Inspect frontend routing, navigation, and existing UI components.
- [ ] T005 Inspect captured release size and assess loading performance.
- [ ] T006 Document the proposed API response contracts before implementation.

## Phase 2 — Backend catalogue service

- [ ] T007 Create the medicine catalogue service using the existing baseline selector.
- [ ] T008 Reconstruct snapshots using the existing captured-release loader.
- [ ] T009 Implement catalogue search.
- [ ] T010 Implement catalogue filters.
- [ ] T011 Implement product detail lookup.
- [ ] T012 Implement package detail lookup by pakkaustunnus.
- [ ] T013 Implement active-substance exploration.
- [ ] T014 Implement product comparison using approved source fields.
- [ ] T015 Implement source-release and provenance information.
- [ ] T016 Expose VNR explicitly and preserve missing values.
- [ ] T017 Implement VNR-based grouping only where source evidence supports it.
- [ ] T018 Handle missing or unavailable validated baseline.

## Phase 3 — Backend API

- [ ] T019 Add catalogue API response schemas.
- [ ] T020 Add GET /api/medicine-catalogue.
- [ ] T021 Add GET /api/medicine-catalogue/products/{product_reference}.
- [ ] T022 Add GET /api/medicine-catalogue/packages/{pakkaustunnus}.
- [ ] T023 Add GET /api/medicine-catalogue/active-substances.
- [ ] T024 Add GET /api/medicine-catalogue/compare.
- [ ] T025 Add GET /api/medicine-catalogue/source.
- [ ] T026 Register the catalogue router in the application.

## Phase 4 — Backend tests

- [ ] T027 Test validated baseline selection and unavailable baseline.
- [ ] T028 Test catalogue search and filters.
- [ ] T029 Test product and package detail lookup.
- [ ] T030 Test active-substance exploration.
- [ ] T031 Test VNR visibility, search, and missing values.
- [ ] T032 Test pakkaustunnus and VNR identity separation.
- [ ] T033 Test provenance and source-release information.
- [ ] T034 Test product comparison and existing comparison-field preservation.
- [ ] T035 Test source integrity and error handling.

## Phase 5 — Frontend catalogue

- [ ] T036 Add the Medicine Catalogue navigation entry.
- [ ] T037 Create the catalogue page and API client integration.
- [ ] T038 Implement search and filters.
- [ ] T039 Implement product detail view.
- [ ] T040 Implement package detail view.
- [ ] T041 Implement active-substance explorer.
- [ ] T042 Implement two-product comparison.
- [ ] T043 Display VNR clearly and distinguish it from package identity.
- [ ] T044 Display source and provenance information.
- [ ] T045 Implement loading, empty, and error states.
- [ ] T046 Verify responsive layouts and accessibility.

## Phase 6 — Frontend tests and regression

- [ ] T047 Test catalogue navigation and page loading.
- [ ] T048 Test search and filters.
- [ ] T049 Test product and package details.
- [ ] T050 Test active-substance exploration.
- [ ] T051 Test product comparison.
- [ ] T052 Test VNR and missing-value presentation.
- [ ] T053 Run backend tests.
- [ ] T054 Run frontend tests.
- [ ] T055 Run TypeScript checks.
- [ ] T056 Run the production build.
- [ ] T057 Review Git diff and confirm no unrelated changes.

## Phase 7 — Completion

- [ ] T058 Verify all Feature 004 acceptance criteria.
- [ ] T059 Summarize implementation and test results.
- [ ] T060 Obtain explicit approval before committing or pushing.
