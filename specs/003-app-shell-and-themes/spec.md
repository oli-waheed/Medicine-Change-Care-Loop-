# Feature Specification: Application Shell and Open Review Cases Workspace

**Feature Branch:** `application-shell-and-catalogue`
**Created:** 2026-11-20
**Revised:** 2026-11-20
**Status:** Approved

## 1. Purpose

Provide Medicine Change Care Loop with a professional, responsive application shell and improve the usability of the existing Open Review Cases workspace.

This feature is a frontend presentation and navigation improvement. It does not introduce new medicine-monitoring functionality or change backend behaviour.

## 2. Approved design direction

- Light theme only. No dark theme or theme switch.
- Application-wide responsive sidebar.
- Navy `#102D3B`, teal `#176B65`, pale mint `#E8F3EF`, background `#F3F6F7`, white surfaces, amber `#D69B35`, and error red `#B74747`.
- Clear typography and balanced information density.
- Responsive layouts for mobile, tablet and desktop.
- Accessible keyboard navigation and visible focus indicators.

## 3. Navigation and application shell

- Display the Medicine Change Care Loop product identity.
- Provide one working navigation destination: Open Review Cases.
- Keep Fimea Basic Register attribution and CC BY 4.0 licence link visible in the sidebar.
- Display the application version only when a real version is available; hide placeholder version `0.0.0`.
- Provide a skip-to-main-content link.
- Show a meaningful browser tab title.
- Support browser back and forward navigation.
- Display a Page not found view for unimplemented or unknown routes, with a link back to Open Review Cases.
- Do not display links to modules that are not implemented.

### Responsive behaviour

- Mobile, below 768 px: sidebar opens as a navigation drawer.
- Tablet, 768–1023 px: sidebar appears as a collapsible icon rail.
- Desktop, 1024 px and above: persistent sidebar.

The drawer and tablet navigation must support keyboard operation, focus management, Escape-to-close, and appropriate focus return.

## 4. Open Review Cases workspace

Preserve the existing review-case functionality and data.

### Case queue

- Display available cases.
- Provide a labelled search field.
- Search by medicine display name, identifier and change summary.
- Search must be case-insensitive.
- Support keyboard movement through the case queue using Arrow Up, Arrow Down, Home and End.
- Selecting a case must not trigger an additional API request.

### Changed package review

For `FIELDS_CHANGED` cases:

- Clearly identify the case as an updated/changed package.
- Display each changed field separately.
- Show prior-release and current-release values with clear Before and After labels.
- Identify each field as Field added, Field removed or Value changed.
- Display the number of changed fields.

### Removed package review

For `NO_LONGER_PRESENT` cases:

- Clearly identify the package as no longer present in the register.
- Explain that the source does not state why it is absent.
- Display last-known values from the prior release.
- Do not use Before and After labels for removed-package cases.

### Evidence and provenance

Keep the existing evidence and provenance information accessible without requiring expand, collapse or tab interactions.

Preserve:
- Matched simulated record information.
- Case identifier, status and creation time.
- Evidence classification.
- Prior and current source information.
- Release references and dates.
- Raw filenames, checksums and record locators.
- Source order and its basis.
- Evidence notes and availability information.

Preserve the distinctions between:
- Not present in source.
- Present but empty.
- No occurrences.
- Value unavailable.
- Unknown.
- Not captured.
- Not in this release.
- Raw source evidence unavailable.

Do not replace unavailable historical evidence with invented or inferred values.

## 5. Safety and data boundaries

- All displayed medicine and person records remain synthetic.
- The application presents source information for pharmacist review only.
- Do not add diagnoses, treatment recommendations, substitution advice, urgency, severity or clinical decisions.
- Do not add case actions or clinical workflow controls.
- Do not change backend APIs, ingestion, matching, database models or source-processing logic.

## 6. Explicit exclusions

The following are not part of Feature 003:

- Medicine Catalogue.
- Change Intelligence Dashboard.
- Medicine History.
- Data Quality and Provenance module.
- About the Data page.
- Dark theme or theme switching.
- Processing Outcomes.
- Non-functional navigation links.
- Backend or database changes.
- New clinical or pharmacist decision-making functionality.

These modules may be considered in separate future features with their own specifications.

## 7. Verification and acceptance criteria

Feature 003 is ready for acceptance when:

1. The application displays the approved light-only visual identity.
2. The responsive sidebar works at mobile, tablet and desktop widths.
3. Only Open Review Cases appears as a working application module.
4. Unknown and unimplemented routes display Page not found.
5. The case queue search works without additional API requests.
6. Keyboard navigation works in both the case queue and application navigation.
7. Changed and removed packages use their distinct review layouts.
8. Evidence classifications, source values and provenance remain accurate and accessible.
9. Existing Feature 002 behaviour and requirements remain satisfied unless explicitly superseded by this specification.
10. Synthetic-data and clinical-boundary tests pass.
11. Frontend tests, TypeScript checks and production build pass.
12. No horizontal page scrolling occurs at 320, 375, 768, 1023, 1024 and 1440 px viewport widths.

## 8. Preservation rule

Feature 003 must not silently alter existing behaviour or source-data meaning. Any requirement from Feature 002 that is not explicitly changed by this specification remains in force.
