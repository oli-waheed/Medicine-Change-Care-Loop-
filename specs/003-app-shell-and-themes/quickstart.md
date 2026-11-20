# Quickstart: Verify Feature 003

## Prerequisites

Backend running with the two fixture releases ingested (see `specs/001-ingestion-case-pipeline/quickstart.md`), so Open Review Cases shows Fictional Product Amber and Fictional Product Cedar.

## Automated checks (from `frontend/`)

```
npx vitest run
npm run build
npm run lint
npm run format:check
```

## Manual checks

Run `npm run dev` and open the printed address.

1. **Navigation** (US1): at 1440 px, use both sidebar links; check address, tab title, current-link marking, back/forward. Open `/dashboard` → Page not found with a working link.
2. **Sidebar content** (FR-001, FR-002, FR-006): product name, two links, Fimea attribution with licence link; no version while it is `0.0.0`; no theme switch; nothing else.
3. **Review layouts** (US2): Amber → "Updated package", "2 fields", "Value changed" on `Laakevalmiste/Kauppanimi`, "Field removed" on `Pakkaus/JulkinenTarkenne`, "Before · Prior release" / "After · Current release". Cedar → "Removed package", "Package no longer present in the register" first, last known values, no Before/After or indicators.
4. **Evidence states** (FR-022, FR-023): Cedar shows "Not present in source", "Present but empty" and "No occurrences", each with its own border style; every source-evidence field visible without interaction.
5. **Search and queue keyboard** (US3): type "cedar", "SIM-PKG-100", "no longer"; check the "Showing n of 2" line and the no-match message; with focus on a case use Down/Up/Home/End and Enter.
6. **Palette and contrast** (FR-009, FR-010): handoff colours; every text and state-indicator pair meets AA; the page stays light when the OS uses dark mode.
7. **Responsive** (SC-004): at 320, 375, 768, 1023, 1024 and 1440 px no horizontal scrolling; drawer below 768, rail from 768 to 1023, persistent from 1024.
8. **Keyboard** (US4): skip link first; at 900 px open the rail with "Sidebar", at 375 px open "Menu"; focus lands on the first link, Tab stays inside, Escape closes and returns focus.
9. **Requests** (SC-008): in the browser's network panel, one `GET /api/open-review-cases` per display of Open Review Cases; none for search, selection or About the Data.
10. **Timed scan** (SC-001, and 002 SC-001): a team member acting as pharmacist tells changed from removed within 5 seconds and identifies the selected case, each change and each classification within 30 seconds.

## Results

### 2026-11-20 — verification after the review fix (branch `feature/application-shell-and-catalogue`, commit `16927e2` plus the fix)

Same checks repeated after restoring About the Data and the original evidence-unavailable wording: 54 tests passed; build, `tsc -b`, lint (0 warnings) and format clean; 24-view contrast and overflow scan 0 failures; keyboard checks on desktop, tablet and mobile pass; one GET per display of Open Review Cases in the production build.

### 2026-11-20 — implementation verification (Claude; headless Chrome via Playwright; backend with both fixture releases)

| Check | Result |
|---|---|
| Baseline before changes | `git diff --ignore-cr-at-eol` empty; 19 tests passed; build, lint and format clean |
| Automated checks | 8 test files, **54 tests passed** (19 existing + 35 new); `npm run build` ✓; `npm run lint` exit 0; `npm run format:check` clean; `tsc -b` clean |
| New tests fail on old code | 9 of the 10 new tests in `OpenReviewCasesPage.test.tsx` fail against `main` (`48abcc2`); the tenth is a regression guard that also passes on `main` |
| 1. Navigation | Pass. `/dashboard` → Page not found; reloading `/about-data` works in dev and `vite preview` |
| 2. Sidebar content | Pass. No version (placeholder), no theme switch |
| 3. Review layouts | Pass. Amber: "Value changed" and "Field removed" as expected; Cedar: removed layout with no Before/After |
| 4. Evidence states | Pass |
| 5. Search and queue keyboard | Pass. "cedar" → 1 of 2 ("Showing 1 of 2"); Down moves focus, Enter selects |
| 6. Palette and contrast | Pass. 54 token pairs meet AA: lowest text 5.02:1, lowest non-text 3.85:1. A rendered-page scan of every visible text node in 24 views (6 widths × 4 views, navigation opened below 1024 px) found 0 contrast failures. Amber is used only as fill/accent (2.4:1 on white) |
| 7. Responsive | Pass. 0 horizontal overflow in all 24 views |
| 8. Keyboard | Pass. Desktop order: skip link → 2 nav links → CC BY 4.0 → search → cases. Tablet (900 px): "Sidebar" opens the rail, focus to first link, Tab cycles inside, Escape returns focus. Mobile (375 px): same with "Menu" |
| 9. Requests | Pass (production build): one GET per display of Open Review Cases; search and selection add none. The dev server shows two per display because React StrictMode runs effects twice, as before this feature |
| 10. Timed scan | **Open**: needs a team member acting as pharmacist |

Issues found and fixed during verification: focus moved to the main area on first load in development mode (skip link not first); the drawer's visibility transition blocked moving focus into it; long field paths broke mid-word in narrow columns (now break after "/"); expanding the tablet sidebar squeezed the content behind it into the rail column (content now keeps its column).
