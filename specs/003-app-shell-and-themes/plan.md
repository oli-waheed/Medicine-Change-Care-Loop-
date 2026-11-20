# Implementation Plan: Application Shell and Open Review Cases Workspace

**Branch**: `feature/application-shell-and-catalogue` | **Date**: 2026-11-20 (revised for the final design handoff) | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-app-shell-and-themes/spec.md`

## Summary

Wrap the existing Open Review Cases page in an application shell with a responsive sidebar (persistent from 1024 px, icon rail from 768 px, drawer below), add About the Data and Page not found, apply the handoff's light-only navy/teal palette through design tokens, add a read-only search and keyboard movement to the case queue, and split the 407-line page component into focused components with separate changed-package and removed-package layouts, prior/current release labels and field indicators. Data loading, selection, wording, evidence semantics and asserted CSS class names stay unchanged. No new dependencies and no backend changes.

## Technical Context

**Language/Version**: TypeScript 7.0.2; React 19.3.0; Node.js 24.15.0 or later

**Primary Dependencies**: Existing only (React, React DOM, Vite 8.3.3, Vitest 5.0.3, Testing Library, jsdom, Oxlint, Prettier). See research.md R1, R3, R4.

**Storage**: None added. The search query lives in component state. API unchanged (`GET /api/open-review-cases`).

**Testing**: Vitest + Testing Library in jsdom (`npx vitest run`), `npm run build`, `npm run lint`, `npm run format:check`, and the manual and browser checks in quickstart.md.

**Target Platform**: Current desktop, tablet and mobile browsers from 320 px.

**Project Type**: Web application — frontend only.

**Constraints**: Light theme only (`color-scheme: light`); handoff palette; global class names asserted by tests; no CSS modules, router, icon or UI packages; the search field is the only form control; no clinical wording; evidence always visible; WCAG 2.2 AA.

**Scale/Scope**: Three views, one shell, about 20 small components.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Evidence-driven decision making**: Pass. Based on `main` at `48abcc2`, the local Git state (working tree differs only by line endings), the existing tests, the README licence section, and the final design handoff with the decisions of 2026-11-20 (light only; add search; keep the removed-package wording; adopt exact colours, release labels, change indicators and the tablet rail).
- **User-centered delivery**: Pass. Every change traces to the handoff and spec user stories.
- **Quality before completion**: Pass. Tests, build, lint, format, browser checks and a convergence review are planned.
- **Human-in-the-loop and clinical scope**: Pass. No actions or decisions; the search only filters loaded cases; field indicators describe source presence only; the app-level guard test covers every page.
- **Evidence honesty and traceability**: Pass. All evidence stays visible; absence states keep their wording; the indicator rule (FR-020) is deterministic and documented.
- **Prototype and simulated data**: Pass.
- **Spec traceability**: Pass. 002 FR-002 and FR-010 are superseded only as listed, and 002 carries a note.

## Project Structure

### Documentation (this feature)

```text
specs/003-app-shell-and-themes/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
├── contracts/app-shell-ui.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
frontend/
├── vite.config.ts                               MODIFY  define __APP_VERSION__ from package.json
└── src/
    ├── App.tsx                                  MODIFY  AppShell + page by path + tab title
    ├── index.css                                MODIFY  light-only handoff tokens, base, focus, skip link, visually-hidden
    ├── env.d.ts                                 NEW     declares __APP_VERSION__
    ├── app/
    │   ├── AppShell.tsx / AppShell.css          NEW     skip link, top bar, sidebar (drawer / rail / persistent), main
    │   ├── Sidebar.tsx                          NEW     brand, rail toggle, nav links, attribution, version
    │   ├── navigation.ts                        NEW     routes, navigate(), useCurrentPath(), link click handler
    │   ├── useNavigationDrawer.ts               NEW     open/close, focus move, focus trap, Escape, resize
    │   ├── appVersion.ts                        NEW     version or null for 0.0.0
    │   ├── icons.tsx                            NEW     small decorative inline SVGs
    │   ├── navigation.test.ts, appVersion.test.ts, AppShell.test.tsx, App.scope.test.tsx   NEW
    ├── pages/
    │   ├── about-data/AboutDataPage.tsx, .css, .test.tsx                                   NEW
    │   ├── not-found/NotFoundPage.tsx                                                      NEW
    │   └── open-review-cases/
    │       ├── OpenReviewCasesPage.tsx          MODIFY  fetch, selection, states; root becomes div (shell owns <main>)
    │       ├── OpenReviewCasesPage.css          MODIFY  tokens only; merged duplicates; queue, search, layouts, indicators
    │       ├── CaseList.tsx                     NEW     queue with search and arrow-key movement
    │       ├── CaseDetail.tsx                   NEW     heading + kind badge, banner, record card, layout, provenance
    │       ├── UpdatedPackageReview.tsx         NEW     FIELDS_CHANGED: indicators, Before·Prior / After·Current
    │       ├── RemovedPackageReview.tsx         NEW     NO_LONGER_PRESENT: removal banner, last known values
    │       ├── ProvenancePanel.tsx              NEW     SourceOrder + Prior/Current SourceCard
    │       ├── changeIndicator.ts               NEW     added / removed / changed from source presence
    │       ├── evidence/SourceValueDisplay.tsx  NEW     value states, value-unavailable, empty-list fallback
    │       ├── evidence/EvidenceClassificationLabel.tsx, evidence/TimestampDisplay.tsx    NEW (extracted, unchanged)
    │       ├── evidence/FieldPath.tsx           NEW     wraps paths after "/" (<wbr>, no text change)
    │       ├── OpenReviewCasesPage.test.tsx     MODIFY  add tests only
    │       ├── OpenReviewCasesPage.scope.test.tsx MODIFY case buttons counted in the queue; one search input allowed
    │       └── openReviewCases.ts, changeSummary.ts, sourceValue.ts, timestamp.ts, timestamp.test.ts   unchanged
    └── test/clinicalWords.ts                    NEW     shared word list for the app-level tests

README.md                                        MODIFY  Application Interface section
specs/002-case-review-readability/spec.md, plan.md, contracts/open-review-cases-ui.md   MODIFY  supersession note only
```

Unchanged: `frontend/index.html`, `package.json`, `package-lock.json`, `main.tsx`, test setup, TypeScript and lint configuration, all backend files. Nothing is deleted.

**Structure Decision**: Shell concerns live in `src/app/`; each page in `src/pages/<page>/`. `OpenReviewCasesPage` stays shell-free and router-free so its existing tests render it alone. Pure logic modules stay untouched.

## Spec Kit feature pointer

The branch name does not follow the `###-name` pattern. Spec Kit finds the feature through `.specify/feature.json` (ignored by Git, so each clone sets it once):

```
{"feature_directory":"specs/003-app-shell-and-themes"}
```

## Design Decisions

### Navigation (R1)
- `navigation.ts`: route table, trailing-slash normalising, `navigate()` (`history.pushState` plus a notification), and `useCurrentPath()` (`useSyncExternalStore` over `popstate`).
- Sidebar items are `<a href>`s. Plain left clicks are handled in-app; modified clicks keep their native behaviour.
- The current link gets `aria-current="page"`. `App.tsx` sets `document.title`.
- After moving to another page, focus goes to `<main>`, but not on first load.

### Light-only theme and handoff palette (R2)
- `index.css` defines tokens on `:root` with `color-scheme: light`, using the exact handoff colours.
- Amber `#D69B35` (2.4:1 on white) is used only for fills and accent bars. A darker amber, `#96641A`, carries the borders and `#6A4A0E` the text, so every pair meets FR-010.
- `index.html` is unchanged.

### Responsive shell (R3)
- **≥1024 px:** a grid with a 264 px sticky navy sidebar.
- **768–1023 px:** a 72 px icon rail.
  - Labels are visually hidden but keep their accessible names.
  - The footer is hidden.
  - The "Sidebar" toggle (`aria-expanded`, `aria-controls`) expands the full sidebar over the content.
- **<768 px:** a top bar with the product name and "Menu"; the sidebar is a drawer.
- **Shared behaviour (`useNavigationDrawer`):**
  - remembers which toggle opened the sidebar and moves focus to the first navigation link
  - traps Tab inside the sidebar
  - closes on Escape, the toggle or the scrim, and returns focus to the toggle
  - closes on link activation and at 1024 px
  - makes `<main>` `inert` while open
- **Visibility timing:** the drawer becomes visible immediately on opening, so focus can move into it, and fades out on closing.

### Case queue (R4)
- `CaseList` keeps the existing native `<button aria-pressed>` items.
- It adds a labelled `<input type="search">` (no `<form>`) and a `role="status"` line "Showing n of N".
- Matching: every lower-cased word must appear in the name, identifier or `changeSummary()`.
- Filtering never changes `selectedId`. When nothing matches, "No cases match this search." is shown.
- Arrow keys, Home and End on the queue move focus between visible buttons; native Enter and Space select.

### Review layouts and evidence (R5)
- `CaseDetail` adds a kind badge, "Updated package" or "Removed package", and chooses `UpdatedPackageReview` or `RemovedPackageReview`. The container gets `case-evidence--updated` or `case-evidence--removed`.
- **Changed layout:**
  - per field: the path (`FieldPath`), an indicator from `changeIndicator()`, and two sides
  - each side heading reads "Before" or "After" followed by "Prior release" or "Current release" (separate spans, so "Before" and "After" stay exact texts)
- **Removed layout:** keeps the existing heading and statement, the amber dashed banner, and the last-known table. It has no Before/After and no indicators.
- **Value states:** `SourceValueDisplay` keeps `source-value--missing`, `--empty`, `--no-occurrences` and `--value`, and adds `--value-unavailable`.
  - `SourceValueParagraphs` and `SourceValueInline` show "No occurrences" for empty lists.
  - States differ by border style (solid, dashed, dotted, double) as well as colour.
- All asserted class names are preserved.

### Tests
- **Page scope test:** count buttons inside the "Open review cases" navigation; assert that the page has no other buttons; allow exactly one `input`, which must be `type="search"`; type a search and re-check the wording.
- **App scope test:** allow-list buttons (cases, Menu, Sidebar), links and the single search field on `/`, `/about-data` and an unknown path, with a search active and with the navigation open; no switches, no other form controls, no clinical words, GET-only reads.

## Post-design Constitution Check

- **Quality and verification**: Pass. The automated suite, token contrast, rendered-page contrast and overflow scan, keyboard checks in a real browser, and request counting in a production build are all recorded in quickstart.md.
- **Traceability**: Pass. Tasks reference FR/SC IDs; 002 notes record exactly what is superseded.
- **Scope and safety**: Pass.

## Complexity Tracking

No constitution violations to justify.
