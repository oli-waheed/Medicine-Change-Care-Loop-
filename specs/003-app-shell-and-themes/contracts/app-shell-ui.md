# Application Shell and Review UI Contract

> Superseded in part by feature 004: the sidebar and the page table also include Medicine Catalogue (`specs/004-interactive-medicine-catalogue/spec.md`).

## Pages and addresses

| Address | Page | Tab title | Sidebar link |
|---|---|---|---|
| `/` | Open Review Cases | `Open Review Cases \| Medicine Change Care Loop` | "Open Review Cases" |
| `/medicine-catalogue` | Medicine Catalogue (added by feature 004) | `Medicine Catalogue \| Medicine Change Care Loop` | "Medicine Catalogue" |
| `/about-data` | About the Data | `About the Data \| Medicine Change Care Loop` | "About the Data" |
| any other | Page not found | `Page not found \| Medicine Change Care Loop` | none current |

Trailing slashes are ignored. Sidebar links update the address without reloading; back and forward work.

## Theme

Light only (`color-scheme: light`). Palette: navy #102D3B, teal #176B65, pale mint #E8F3EF, page background #F3F6F7, surface #FFFFFF, amber #D69B35 (fills and accent bars only), error #B74747. No dark theme, no theme switch. *(Palette revised 2026-11-21 at Oli's request: navy #014178, pharmacy green #2DAF35 for stripes and markers, darker green #1C7F27 for text, buttons and focus; page background, surface, amber and error unchanged. See the comment in `frontend/src/index.css`.)*

## Sidebar

1. Product name "Medicine Change Care Loop".
2. "Main navigation" landmark with exactly two links, "Open Review Cases" and "About the Data"; the current one has `aria-current="page"`.
3. Attribution: "Source data: Basic register for medicinal products, Finnish Medicines Agency Fimea." with a "CC BY 4.0" licence link.
4. "Version x.y.z" only when the version is not `0.0.0`.

| Width | Sidebar | Toggle |
|---|---|---|
| ≥ 1024 px | Persistent | none |
| 768–1023 px | 72 px icon rail; link names kept for assistive technology; attribution hidden until expanded | "Sidebar" button in the rail, `aria-expanded`, `aria-controls="app-sidebar"` |
| < 768 px | Hidden drawer | "Menu" button in a top bar with the product name, `aria-expanded`, `aria-controls="app-sidebar"` |

Opening moves focus to the first navigation link; Tab and Shift+Tab stay inside; `<main>` is inert. Escape, the toggle or the scrim closes and returns focus to the toggle; a link closes it; reaching 1024 px closes it.

## Keyboard

"Skip to main content" is the first focusable element. All controls are reachable with a visible focus ring. In the case queue, Down/Up/Home/End move focus; Enter/Space select.

## Allowed interactive controls

Case-selection buttons; the "Search cases" field (`type="search"`, the only form control); the two sidebar links; the skip link; the "Menu" and "Sidebar" toggles; the licence and Fimea open-data links; the Page not found link. No `select`, `textarea`, `form` or switch.

## Case queue

- Heading "Cases (N)"; "Search cases" label and field; while searching, a status line "Showing n of N"; no match: "No cases match this search.".
- Each item: name, identifier (monospace), change summary, evidence-unavailable warning when applicable, status. The selected item has `aria-pressed="true"` and a teal border and fill. Removed packages have a dashed amber edge marker.
- Searching never changes the selection and sends no request.

## Review workspace

- **Heading**: "Open review case", medicine name, "identifier · granularity", kind badge ("Updated package" or "Removed package", dashed), status badge.
- **Changed package** (`case-evidence--updated`): "Detected source-data changes", "n field(s)"; per field: path, indicator, "Before · Prior release" and "After · Current release".
- **Field indicators** (source presence only):

  | Prior side | Current side | Indicator | Class |
  |---|---|---|---|
  | absent (missing or no occurrences) | present (including empty) | Field added | `change-indicator--added` (solid) |
  | present | absent | Field removed | `change-indicator--removed` (dashed) |
  | present | present | Value changed | `change-indicator--changed` (dotted) |

- **Removed package** (`case-evidence--removed`): amber banner with "Package no longer present in the register" and the existing statement; "Last known values (prior release)" table; no Before/After or indicators; no suggested reason.
- **Both**: evidence-unavailable banner when applicable, matched simulated record, source order with basis, Prior and Current source evidence, and the review-boundary note, all visible without interaction.

## Value and evidence states (unchanged wording)

| State | Text | Class |
|---|---|---|
| Missing element | Not present in source | `source-value--missing` (solid border) |
| Empty element, no code value | Present but empty | `source-value--empty` (dashed) |
| Empty element with code-table value | the code value | `source-value--value` |
| Zero occurrences (last-known or before/after) | No occurrences | `source-value--no-occurrences` (dotted) |
| Present but no value delivered | Value unavailable | `source-value--value-unavailable` (double) |
| Raw file no longer stored | "(no longer stored)", "… when recorded; source file now unavailable" | `evidence-missing`, `evidence-classification--warning` |
| Case evidence unavailable | banner, "Evidence unavailable", "… when recorded; source evidence now unavailable" | `evidence-unavailable`, `case-list-warning`, `evidence-classification--warning` |
| Classifications | VERIFIED, INFERRED, UNKNOWN, CONFLICTING | `evidence-classification--verified` … `--conflicting` |
| Other absences | Unknown, Not captured, Not in this release | unchanged |

## Data boundary

One `GET /api/open-review-cases` per display of Open Review Cases; nothing else from the shell, search, queue, About the Data or Page not found; no writes; no backend changes.
