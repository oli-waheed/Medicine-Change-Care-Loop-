# Open Review Cases UI Contract

## Purpose and scope

This contract describes the existing pharmacist-facing Open Review Cases page after its presentation improvements. The page remains read-only except for its existing case-selection behavior. The API, case data, and workflow do not change.

## Page identity and header

- The browser tab title identifies the Open Review Cases page and Medicine Change Care Loop.
- The page retains its existing heading, project name, and descriptive text.
- A concise notice communicates that the displayed records are simulated.
- The background and page sections use a consistent light presentation.
- The page remains readable when the operating system requests dark colors; it does not switch to a dark theme.
- The browser tab title identifies the Open Review Cases page and Medicine Change Care Loop.

## Case list and selection

- The existing case list remains labeled “Open review cases” and shows each existing case's current information.
- The currently selected case is clearly distinguishable from other cases; the existing native selection buttons and `aria-pressed` state remain in use.
- At viewport widths of 1024 pixels and wider, the case list remains visible while the user scrolls through case details.
- At mobile widths, the case list and details use normal flow and remain usable without horizontal page scrolling.
- From 768 through 1023 pixels, the case list and details are side by side in normal flow, with no overlap or horizontal page scrolling.
- Keyboard focus remains visibly distinguishable from selected state.
- No new case actions, buttons, forms, or mutation requests are added.

## Case details and evidence

- Existing wording and information, including loading, error, empty, source-unavailable, and review-boundary text, remain present and unchanged except for the required readable timestamp representation; the exact original timestamp is shown as small muted text beside it.
- Each changed field remains grouped with its existing “Before” and “After” labels and values.
- Each evidence classification remains explicitly labeled `VERIFIED`, `INFERRED`, `UNKNOWN`, or `CONFLICTING`; visual differences are not conveyed by color alone.
- Valid timestamps appear as `YYYY-MM-DD HH:MM UTC` in a `<time>` element. Its `dateTime` attribute retains the exact original value, which is always visible as small muted text beside the formatted time.
- Missing or invalid timestamps retain their existing fallback and do not display a fabricated date or time zone.
- Checksums, file names, and record locators use monospace text.
- Missing, empty, populated, code-table, conflicting, unknown, and unavailable evidence retain their existing meaning.
- “Not present in source”, “Present but empty”, and “No occurrences” are visually distinct from real source values.
- Unavailable evidence retains its existing qualification wording and uses a warning appearance rather than the current-verification appearance.
- Loading, error, and empty states use the same visual design as the rest of the page.
- Long values wrap or otherwise remain readable on mobile without horizontal page overflow.

## Data and safety boundary

- The page continues to use only simulated patient and medication records.
- It presents source information for pharmacist review; it does not add clinical wording, diagnosis, treatment recommendations, urgency decisions, substitution decisions, or automatic case closure.
- The existing `GET /api/open-review-cases` request is unchanged; no new API contract is introduced.

## Compatibility

- Existing frontend tests and their current text assertions must pass without modification.
- New automated tests cover timestamp fallback and display of all four evidence classifications.
- The existing loading, error, empty, selected-case, and evidence-unavailable behavior remains unchanged.
- Remove the unused Vite starter CSS and unreferenced assets `frontend/src/App.css`, `frontend/src/assets/vite.svg`, `frontend/src/assets/react.svg`, and `frontend/src/assets/hero.png`. Keep the referenced `frontend/public/favicon.svg`.
