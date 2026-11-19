# Quickstart: Open Review Case Readability

## Prerequisites

- Node.js 24.15.0 or later and npm.
- Existing frontend dependencies installed in `frontend/`.
- For browser-based page checks, the backend and its simulated seed data, as described in the repository [README](../../README.md).

No new npm packages are required.

## Automated validation

From `frontend/`, run the existing frontend tests and quality checks:

```powershell
npm test -- --run
npm run build
npm run lint
npm run format:check
```

Expected: all existing Vitest files and tests pass unchanged; new automated coverage verifies invalid/missing timestamp fallback and display of `VERIFIED`, `INFERRED`, `UNKNOWN`, and `CONFLICTING`. The production build succeeds, Oxlint reports no errors, and Prettier reports that matched files use the repository style.

## Browser validation

Start the backend using the repository's existing setup instructions. In a separate PowerShell terminal:

```powershell
Set-Location frontend
npm run dev
```

Open the Vite URL printed in the terminal. Use only simulated records.

Verify:

1. The browser tab identifies Open Review Cases and Medicine Change Care Loop.
2. The project header, simulated-record notice, existing text, and existing case information remain visible.
3. The selected case is distinguishable; keyboard focus on existing case-selection buttons is visibly distinguishable from selection.
4. Changed fields remain separated under “Before” and “After”; each evidence classification remains labeled and visually distinct.
5. The timestamp utility tests in `frontend/src/pages/open-review-cases/timestamp.test.ts` cover valid UTC, valid `+02:00` offset, invalid, and missing inputs. Valid timestamps display as `YYYY-MM-DD HH:MM UTC` in a `<time>` element whose `dateTime` attribute contains the exact original value; that value is always visible as small muted text beside the formatted time. Missing or invalid timestamps keep their existing fallback.
6. Checksums, file names, and record locators are monospace. All four evidence classifications are visibly distinct without relying only on color.
7. Unavailable evidence retains its existing qualification text and is visibly marked as a warning, not as currently verified. “Not present in source”, “Present but empty”, and “No occurrences” are distinct from real values.
8. At 320 and 767 pixel widths, the case list and details are readable without horizontal overflow. At 768 and 1023 pixels, they remain side by side in normal flow. At 1024 and 1280 pixels, scroll long details and confirm the case list remains visible.
9. With the operating system set to dark color preference, confirm the page remains light and readable. Check that normal text has at least 4.5:1 contrast and large text has at least 3:1 contrast against its background, meeting WCAG 2.2 AA. Loading, error, and empty states use the same visual style as the rest of the page.
10. No new case actions, forms, clinical wording, real records, API requests, or npm dependencies have been introduced. The referenced favicon still loads after unused starter assets are removed.
11. Have a team member act as the pharmacist and, without assistance, identify the selected case, every changed field's before/after values, and all evidence classifications using a simulated case. Record pass if they complete this scan within 30 seconds.

## References

- [UI contract](./contracts/open-review-cases-ui.md)
- [Displayed data model](./data-model.md)
