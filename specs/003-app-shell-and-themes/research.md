# Research: Application Shell and Open Review Cases Workspace

## Starting point (evidence)

- Local repository on `main` at `48abcc2`, equal to `origin/main`.
- `git diff --ignore-cr-at-eol` is empty: the 14 files that `git status` lists as modified differ only in line endings.
- `localhost:5174/dashboard` is served by this project's Vite dev server; no source file mentions "dashboard". Vite serves the single-page app for every path, so `/dashboard` displayed Open Review Cases.
- Stashes `stash@{0}` and `stash@{1}` contain earlier styling attempts superseded by feature 002; this feature does not use or remove them.
- Final design handoff (2026-11-20): light theme only, handoff palette, searchable queue, prior/current release labels, added/removed/changed indicators, collapsible tablet sidebar. Decisions recorded the same day: light only; add search; keep "Package no longer present in the register"; adopt colours, release labels, indicators and tablet rail.

## R1 — Navigation without a router package

- **Decision**: `history.pushState`, `popstate` and `useSyncExternalStore` in `navigation.ts`; sidebar items are `<a href>`.
- **Rationale**: Two pages plus Page not found; a router would add a dependency and test wrappers. Native links keep new-tab and copy-link behaviour.
- **Alternatives**: `react-router` (unnecessary); hash routing (harder to read).

## R2 — Light-only theme and handoff palette

- **Decision**: Tokens on `:root` with `color-scheme: light`; exact handoff colours; darker derived shades where a handoff colour cannot meet WCAG on its own.
- **Rationale**: The handoff excludes a dark theme and theme switching. Amber `#D69B35` measures 2.4:1 on white and 2.2:1 on its pale fill, below the 3:1 non-text minimum, so it is used for fills and accent bars, with `#96641A` (4.6:1 on the pale fill) for borders and `#6A4A0E` (7.3:1) for text.
- **Alternatives**: Using amber for borders or text (fails contrast); dropping amber (departs from the handoff).

## R3 — Responsive navigation pattern

- **Decision**: Persistent sidebar from 1024 px; 72 px icon rail with a "Sidebar" disclosure toggle from 768 to 1023 px; drawer with a "Menu" toggle in a top bar below 768 px; shared focus handling (move to first link, trap Tab, Escape and scrim close, focus return, `inert` main).
- **Rationale**: Matches the handoff ("collapsible sidebar on tablets, drawer on mobile") and the WAI-ARIA disclosure navigation pattern; one hook serves both toggles by remembering which control opened the sidebar.
- **Note**: The drawer must become visible immediately when opening; otherwise the browser refuses to move focus into it during the visibility transition (found and fixed during verification).

## R4 — Case search

- **Decision**: Client-side filter of the already loaded cases by name, identifier and change summary; all typed words must match; no `<form>`; status line "Showing n of N"; selection unchanged.
- **Rationale**: The handoff requires a searchable queue; the backend has no search endpoint and API changes are out of scope; filtering loaded data needs no request and cannot change case data.
- **Alternatives**: Server-side search (API change, excluded); fuzzy matching (less predictable for identifiers).

## R5 — Field indicators

- **Decision**: Derive "Field added", "Field removed" or "Value changed" from source presence only: a side is absent when every value is `missing` or there are no occurrences; present otherwise (including `empty`).
- **Rationale**: Deterministic, uses only data already in the response, and keeps "Present but empty" distinct from absence. Labels say "Field"/"Value" to avoid confusion with "Removed package".
- **Alternatives**: Treating empty as absent (would merge "empty" with "missing", violating the data-semantics rule).

## R6 — Component split and class-name stability

- **Decision**: Extract components without changing rendered text or asserted class names; plain global CSS; tokens replace hard-coded colours; `<wbr>` after "/" in field paths for wrapping without changing text.
- **Rationale**: Existing tests assert class names and exact texts; CSS modules would hash names.

## R7 — Contrast verification

- **Decision**: Check every token pair used for text and for state indicators, plus a rendered-page scan of every visible text node at six widths with the navigation open and closed.
