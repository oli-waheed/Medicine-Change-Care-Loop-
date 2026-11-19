# Implementation Plan: Open Review Case Readability

**Branch**: `002-case-review-readability` | **Date**: 2026-11-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-case-review-readability/spec.md`

## Summary

Restyle the existing Open Review Cases page so pharmacists can scan the selected case, changed values, evidence classifications, timestamps, and source references more easily. Preserve existing displayed text and case behavior except for the required readable timestamp presentation and simulated-record notice; keep the current API contract and simulated data, and update the browser tab title. Use plain CSS in `frontend/src/index.css` and `frontend/src/pages/open-review-cases/OpenReviewCasesPage.css`, set `color-scheme: light`, add no npm packages, and remove verified-unused Vite starter styles and assets.

## Technical Context

**Language/Version**: TypeScript 7.0.2; React 19.3.0; Node.js 24.15.0 or later

**Primary Dependencies**: Existing React and React DOM 19.3.0, Vite 8.3.3, Vitest 5.0.3, Testing Library, and Oxlint; no dependency additions

**Storage**: No changes; the page continues to read the existing `GET /api/open-review-cases` response

**Testing**: Existing Vitest and Testing Library suite (`npm test -- --run`), with a new `timestamp.test.ts` unit suite for valid UTC, valid `+02:00`, invalid, and missing inputs, plus coverage for all four evidence classifications; TypeScript/Vite build (`npm run build`), Oxlint (`npm run lint`), Prettier validation (`npm run format:check`), and manual responsive and visual checks. Existing tests remain unchanged and passing.

**Target Platform**: Current supported desktop and mobile browsers; mobile viewport widths 320–767 pixels, intermediate layouts at 768–1023 pixels, and wide layouts at 1024 pixels and above

**Project Type**: Web application frontend

**Performance Goals**: No new performance target or data-fetch behavior; keep existing page loading and case-selection interactions

**Constraints**: Plain CSS in `frontend/src/index.css` and `frontend/src/pages/open-review-cases/OpenReviewCasesPage.css`; set `color-scheme: light` and keep the page readable when OS dark mode is requested; no new npm packages; preserve existing displayed text and information, with timestamps formatted as `YYYY-MM-DD HH:MM UTC` and the exact recorded value shown as small muted text beside it and retained in `dateTime`; simulated records only; no new case actions, forms, or clinical wording; existing frontend tests pass unchanged and new tests cover timestamp fallback and all four evidence classifications

**Scale/Scope**: One pharmacist-facing page and its current load, error, empty, selected-case, and evidence-detail states; no backend, API, or persisted-data changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-research gate

- **Evidence-driven decision making**: Pass. The design is based on the current page, existing styles, tests, package manifest, and user-provided constraints. Remaining choices are recorded in [research.md](./research.md).
- **User-centered delivery**: Pass. The scope improves scanning and responsive use of the existing pharmacist review page.
- **Shared accountability and quality**: Pass. The plan includes test, build, lint, formatting, and browser validation.
- **Human-in-the-loop and clinical scope**: Pass. Existing review-only wording and behavior remain; no clinical decisions, new actions, or real data are introduced.
- **Evidence honesty and traceability**: Pass. Existing classifications, source values, and uncertainty remain visible; presentation must not change their meaning.
- **Prototype and simulated-data scope**: Pass. No production integrations or non-simulated records are added.

No constitution violations or unresolved gates were identified.

## Project Structure

### Documentation (this feature)

```text
specs/002-case-review-readability/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── open-review-cases-ui.md
```

### Source Code (repository root)

```text
frontend/
├── index.html
├── public/
│   └── favicon.svg
└── src/
    ├── index.css
    └── pages/
        └── open-review-cases/
            ├── OpenReviewCasesPage.tsx
            ├── OpenReviewCasesPage.css
            ├── openReviewCases.ts
            ├── changeSummary.ts
            ├── sourceValue.ts
            ├── timestamp.ts
            ├── timestamp.test.ts
            ├── OpenReviewCasesPage.test.tsx
            └── OpenReviewCasesPage.scope.test.tsx
```

Remove the unused `frontend/src/App.css` and the unreferenced Vite starter assets `frontend/src/assets/vite.svg`, `frontend/src/assets/react.svg`, and `frontend/src/assets/hero.png`. Keep `frontend/public/favicon.svg`, which is referenced by `frontend/index.html`.

**Structure Decision**: This is a presentation-only change in the existing frontend project. Replace the Vite global starter rules with a global light baseline in `frontend/src/index.css`; put page layout and component presentation in `frontend/src/pages/open-review-cases/OpenReviewCasesPage.css`; set the meaningful browser title in `frontend/index.html`. Remove only the confirmed-unused starter CSS and image assets listed above. Existing page markup may be adjusted for semantic timestamps, accessible access to exact values, classification styling, and distinct unavailable/missing/empty states, while preserving all other text, accessible case selection, and API behavior.

## Design Decisions

- Keep all existing visible labels and values except for the requested timestamp formatting; render valid timestamps exactly as `YYYY-MM-DD HH:MM UTC` and show the exact recorded value as small muted text next to it, with the original also retained in the `dateTime` attribute. Do not add a button, disclosure, or other interaction for the exact value. Invalid or missing values keep their existing fallback.
- Represent each evidence classification with an explicit text label and a distinct visual treatment. Color reinforces the label and is not its only distinguishing cue. When evidence is unavailable, preserve the existing qualification wording and mark it as a warning rather than as current verification.
- Distinguish the existing “Not present in source”, “Present but empty”, and “No occurrences” values visually from real source values.
- Keep the case-list selection as the existing native button interaction and `aria-pressed` state; add no actions or controls.
- Keep the case list and details stacked for 320–767 pixels, side by side in normal flow for 768–1023 pixels, and sticky-list/scrolling-details for 1024 pixels and wider.
- Use a consistent light presentation for the header, cards, loading, error, and empty states, with `color-scheme: light` so a dark OS preference does not make content unreadable.
- Retain the current loading, error, empty, source-unavailable, and case-detail wording and behavior. Keep the existing frontend tests unchanged; add focused test coverage for timestamp fallback and all four evidence classifications.
- Remove the confirmed-unused Vite starter styles/assets; preserve the referenced favicon and all assets with live references.

## Post-design Constitution Check

- **Quality and verification**: Pass. The quickstart specifies the existing test suite, build, lint, formatting validation, and manual viewport checks.
- **Traceability and evidence honesty**: Pass. [data-model.md](./data-model.md) maps the current display back to the existing case/evidence response; the UI contract preserves exact recorded values, classification, uncertainty, unavailable warnings, and missing/empty distinctions.
- **Scope and safety**: Pass. [contracts/open-review-cases-ui.md](./contracts/open-review-cases-ui.md) preserves the review-only boundary and simulated-data constraint and records that no API or case workflow changes are planned.

No post-design constitution violations remain.
