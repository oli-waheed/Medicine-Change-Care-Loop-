# Research: Open Review Case Readability

## Decision 1: Use the existing frontend and plain CSS

**Decision**: Implement the presentation in the existing React/TypeScript page using plain CSS in `frontend/src/index.css` and `frontend/src/pages/open-review-cases/OpenReviewCasesPage.css`; set `color-scheme: light` and add no npm packages. Replace the global Vite starter rules and remove only unreferenced starter CSS/assets.

**Rationale**: The repository already has page-specific CSS and a responsive grid. The global stylesheet contains Vite starter layout and a system dark-scheme override that conflicts with the requested light presentation. Explicit light page colors and `color-scheme: light` keep the selected palette legible under OS dark preferences. Media queries, CSS Grid, and sticky positioning cover the required layout without another dependency.

**Alternatives considered**: Adding a component library or CSS framework was rejected because it adds dependencies and is unnecessary for one page. Keeping the starter global styles was rejected because they impose centered content, fixed root width, and automatic dark styling.

**Sources**:
- [MDN: Using media queries](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_media_queries/Using_media_queries)
- [MDN: `color-scheme`](https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme)
- Repository evidence: `frontend/src/index.css`, `frontend/src/pages/open-review-cases/OpenReviewCasesPage.css`, and `frontend/package.json`.
- Repository search confirmed no references to `App.css`, `vite.svg`, `react.svg`, or `hero.png`; `frontend/public/favicon.svg` remains referenced by `frontend/index.html`.

## Decision 2: Keep the case list sticky only on wide layouts

**Decision**: Use CSS sticky positioning for the current case list at the wide-screen breakpoint, with an explicit top offset and a bounded list height when needed. Restore normal document flow in the narrow layout.

**Rationale**: Sticky positioning is constrained by its containing block and nearest scrolling ancestor. Keeping it inside the current case layout and limiting it to wide screens preserves list context without consuming the narrow detail viewport. Long lists must remain reachable without hiding the currently viewed details.

**Alternatives considered**: A permanently fixed case list was rejected because it can cover content and is poorly suited to narrow screens. Making the case list sticky at every width was rejected because it competes with case details on mobile.

**Source**:
- [MDN: `position`](https://developer.mozilla.org/en-US/docs/Web/CSS/position)

## Decision 3: Preserve text labels for evidence classifications

**Decision**: Keep each existing classification as text and apply distinct badge treatments that do not rely on color alone.

**Rationale**: The classification itself is important information and must remain understandable for users who cannot distinguish color. Existing wording and uncertainty must be retained while visual hierarchy improves.

**Alternatives considered**: Color-only indicators were rejected because they can obscure classification meaning and fail accessibility guidance. Replacing the words with icons or new wording was rejected because it would alter existing information.

**Source**:
- [WCAG 2.2: Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)

## Decision 4: Add readable timestamp context without removing recorded values

**Decision**: Format timestamps with a dedicated utility and render valid values in the exact UTC format `YYYY-MM-DD HH:MM UTC` inside a semantic `<time>` element. Retain the exact original recorded string in the `dateTime` attribute and show it as small muted text immediately beside the readable value; preserve existing fallbacks for absent or invalid timestamps.

**Rationale**: UTC makes the readable timestamp consistent for every reviewer. Keeping the original string in `dateTime` preserves source precision and offset, while adjacent visible text ensures it is available without hover or an interaction. A fallback prevents an absent or malformed value from being presented as a fabricated date. A small standalone formatter supports deterministic tests for UTC, offset, invalid, and missing inputs without a package.

**Alternatives considered**: Viewer-local formatting was rejected because it would show different times to different reviewers. Replacing the original string with only a formatted date was rejected because it hides source information. A focus/tap reveal was rejected because the exact value can remain visible adjacent to the formatted time. A package for date formatting was rejected because the required fixed UTC format is small and deterministic.

**Source**:
- [MDN: `<time>` element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/time)
- [WCAG 2.2: Keyboard](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html)
- [WCAG 2.2: Content on Hover or Focus](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html)

## Decision 5: Retain native case-selection controls and visible focus

**Decision**: Keep the current native buttons and `aria-pressed` selection state; add a clear `:focus-visible` treatment distinct from the selected-case treatment.

**Rationale**: Native buttons already provide keyboard activation and the current selected state. A visible keyboard focus indicator supports keyboard users without introducing new actions or changing the visible text.

**Alternatives considered**: Replacing buttons with non-interactive elements was rejected because it would reduce accessibility. Adding separate detail actions was rejected because it expands scope.

**Sources**:
- [WAI-ARIA APG: Button Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/)
- [WCAG 2.2: Focus Visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html)
- [WCAG 2.2: Contrast Minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)

## Resolved project facts

- The frontend is React 19.3.0 and TypeScript 7.0.2, built with Vite 8.3.3.
- Existing tests use Vitest 5.0.3, Testing Library, and jsdom.
- The page reads cases from the existing `GET /api/open-review-cases` endpoint; the feature does not change that API.
- The existing case list already uses native selection buttons with `aria-pressed`.
- The existing source-value formatter preserves distinctions between missing, empty, and populated values; the presentation change must retain those distinctions.
- The project uses simulated records and has explicit clinical-scope tests. Those tests and their text assertions remain unchanged.
- The Vite starter CSS and assets `frontend/src/App.css`, `frontend/src/assets/vite.svg`, `frontend/src/assets/react.svg`, and `frontend/src/assets/hero.png` have no references in the frontend; `frontend/public/favicon.svg` is referenced and is retained.

No unresolved technical questions remain.
