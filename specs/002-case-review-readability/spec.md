# Feature Specification: Open Review Case Readability

**Feature Branch**: `Not created`

**Created**: 2026-11-19

**Status**: Draft

**Input**: User description: "Improve the visual design and readability of the Open Review Cases page so a pharmacist can scan a case quickly. Requirements: replace the leftover Vite starter styles with a consistent page style (app header with project name and a note that records are simulated, light background, card sections); make the selected case clearly visible in the case list and keep the list visible while scrolling on wide screens; show each changed field as a clearly separated "before" and "after" value; show evidence classifications (VERIFIED, INFERRED, UNKNOWN, CONFLICTING) as distinct visual labels; show timestamps in a readable form while keeping the exact recorded value available; show checksums, file names and record locators in a monospace font; make the page usable on mobile widths; make the browser tab title meaningful. Constraints: preserve existing wording and information except for readable timestamps; add new wording only in the header or simulated-records notice; use simulated data only; add no new case actions, buttons, forms or clinical wording; keep existing frontend tests passing unchanged. Follow-up requirements: unavailable evidence classifications must read as warnings rather than current verification, with existing qualification wording preserved; timestamps must state their time zone and exact values must be reachable by touch and keyboard without hover; the page must remain readable under a dark colour-scheme preference; missing, empty, and no-occurrence values must be visually distinct from real source values; loading, error, and empty states must match the page style; define the 768–1023 pixel layout; add automated tests for timestamp fallback and all four evidence classifications."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scan a case and its evidence (Priority: P1)

A pharmacist reviewing an open case can quickly understand which case is selected, what changed, and how the evidence is classified, without losing any of the information already shown on the page.

**Why this priority**: Clear, rapid reading of case evidence is the primary purpose of the page.

**Independent Test**: Display an existing simulated case with changed fields and evidence classifications; verify a reviewer can identify the selected case, each before-and-after value, and each classification without changing the displayed information.

**Acceptance Scenarios**:

1. **Given** the Open Review Cases page displays multiple cases, **When** a pharmacist views the case list, **Then** the selected case is visually distinguishable from the other cases.
2. **Given** a case contains one or more changed fields, **When** a pharmacist views its details, **Then** every changed field has clearly separated before and after values.
3. **Given** evidence is classified as VERIFIED, INFERRED, UNKNOWN, or CONFLICTING, **When** a pharmacist views that evidence, **Then** its classification is shown as a distinct, readable label.
4. **Given** the page already displays case and evidence information, **When** the updated page is shown, **Then** all existing wording and information remain unchanged except for the readable timestamp presentation and permitted header and simulated-records notice text.
5. **Given** case or source evidence is unavailable, **When** its classification is shown, **Then** the existing "when recorded; source evidence now unavailable" or "when recorded; source file now unavailable" qualification remains and the classification is visually marked as a warning, not as currently verified.
6. **Given** the browser or operating system requests a dark colour scheme, **When** the pharmacist views the page, **Then** all page content, labels, selected state, and warnings remain readable.

---

### User Story 2 - Keep case context while reading (Priority: P2)

A pharmacist can continue to see the case list while reading case details on a wide screen, and can use the page comfortably on a narrow mobile screen.

**Why this priority**: Maintaining list context supports efficient review, while responsive presentation keeps the same information usable on mobile devices.

**Independent Test**: View and scroll the page at wide and mobile viewport widths; verify the list remains visible during detail scrolling on wide screens and the page remains readable and usable on mobile.

**Acceptance Scenarios**:

1. **Given** the page is displayed at a wide viewport, **When** the pharmacist scrolls through case details, **Then** the case list remains visible.
2. **Given** the page is displayed at a mobile viewport, **When** the pharmacist views the list and details, **Then** the content fits the narrow layout without requiring horizontal page scrolling.
3. **Given** the page is displayed at a viewport from 768 through 1023 pixels wide, **When** the pharmacist views and scrolls the page, **Then** the case list and details remain side by side in normal page flow, without overlap or horizontal page scrolling.

---

### User Story 3 - Read source metadata and timestamps (Priority: P3)

A pharmacist can read timestamps in a familiar format while still accessing their exact recorded values, and can distinguish technical identifiers and source references from surrounding text.

**Why this priority**: Legible dates and consistently presented source references help a reviewer verify details without changing their recorded meaning.

**Independent Test**: View a case with timestamps, checksums, file names, and record locators; verify the timestamp has a readable presentation and its exact recorded value remains available, and that each specified reference uses a monospace presentation.

**Acceptance Scenarios**:

1. **Given** a case displays a valid timestamp, **When** a pharmacist reads it, **Then** a readable form states its time zone and the exact recorded value is reachable using touch or keyboard without relying on mouse hover.
2. **Given** a timestamp is missing or cannot be parsed, **When** it is displayed, **Then** the existing fallback or exact recorded value remains available and no date or time zone is fabricated.
3. **Given** a case displays a checksum, file name, or record locator, **When** a pharmacist reads it, **Then** the value is visually presented in monospace text.
4. **Given** the page is open in a browser tab, **When** the pharmacist identifies the tab among other tabs, **Then** its title clearly identifies the Open Review Cases page and project.

### Edge Cases

- A case has a long changed value, file name, checksum, or record locator: the value remains readable at mobile widths without causing horizontal page overflow.
- A timestamp cannot be rendered in a readable date form: the exact recorded value remains visible and is not replaced with a misleading value.
- A timestamp is absent or malformed: retain the existing fallback or exact value and do not invent a date or time zone.
- Evidence can have any of the four supported classifications, including UNKNOWN or CONFLICTING: each remains explicitly labeled and distinguishable without relying on colour alone.
- A case or source's evidence is unavailable: preserve its existing "when recorded; ... now unavailable" qualification and show it with warning styling rather than the current-verification styling.
- A source field is missing, empty, or has no occurrences: its existing "Not present in source", "Present but empty", or "No occurrences" text is visually distinguishable from a real source value.
- The page is scrolled through lengthy case details on a wide display: the case list remains visible without obscuring the details.
- At 768–1023 pixels, the list and details remain side by side in normal flow; narrower inner content may reflow without horizontal page overflow.
- Loading, error, and empty states remain visually consistent with the rest of the page.
- A browser or operating system requests a dark colour scheme: text and state distinctions remain readable.
- The case list contains no selected case: the page does not visually imply that an unselected case is selected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Open Review Cases page MUST replace leftover starter-page styling with a consistent visual presentation that includes a project-name header, a notice that records are simulated, a light background, and card-based sections.
- **FR-002**: The page MUST preserve all existing displayed wording and information, including case and evidence content. The only permitted displayed-text changes are a readable timestamp presentation under FR-006 and new text in the app header or simulated-records notice.
- **FR-003**: The case list MUST make the currently selected case clearly distinguishable. At wide screen sizes, the list MUST remain visible while the pharmacist scrolls through case details.
- **FR-004**: The page MUST present each changed field with clearly separated before and after values.
- **FR-005**: The page MUST present VERIFIED, INFERRED, UNKNOWN, and CONFLICTING as explicit, visually distinct evidence-classification labels; colour MUST NOT be the sole means of distinguishing them.
- **FR-006**: The page MUST show each valid timestamp in a readable form that states its time zone, while keeping the exact recorded value reachable by touch and keyboard without relying on mouse hover. Missing or unparseable timestamps MUST retain their existing fallback or exact value without inventing a date or time zone.
- **FR-007**: The page MUST present checksums, file names, and record locators in a monospace font.
- **FR-008**: The page MUST remain usable at mobile viewport widths, including when case values and source references are long, without horizontal page scrolling.
- **FR-009**: The browser tab title MUST meaningfully identify the Open Review Cases page and the project.
- **FR-010**: The page MUST NOT add new case actions, buttons, forms, or clinical wording. Existing case-list selection MUST remain available.
- **FR-011**: All records shown by the page MUST remain simulated; the feature MUST NOT introduce or display real patient or medication data.
- **FR-012**: All existing frontend tests MUST continue to pass unchanged.
- **FR-013**: When case or source evidence is unavailable, its classification MUST be visually marked as a warning and MUST NOT look like a currently verified label. Existing qualification wording MUST remain unchanged, including "when recorded; source evidence now unavailable" for case evidence and "when recorded; source file now unavailable" for source evidence.
- **FR-014**: The page MUST visually distinguish "Not present in source", "Present but empty", and "No occurrences" from real source values without changing those existing phrases.
- **FR-015**: Loading, error, and empty states MUST use the same consistent visual style as the rest of the page.
- **FR-016**: Page text, content, and state distinctions MUST remain readable when the browser or operating system uses a dark colour-scheme preference. Text MUST meet WCAG 2.2 AA minimum contrast ratios of 4.5:1 for normal text and 3:1 for large text.
- **FR-017**: New automated tests MUST cover the timestamp fallback and the display of all four evidence classifications.
- **FR-018**: At viewport widths from 768 through 1023 pixels, the case list and case details MUST remain side by side in normal page flow, without overlap or horizontal page scrolling.

### Key Entities *(include if feature involves data)*

- **Review Case**: An existing simulated case shown in the list and detail view, with its currently selected state.
- **Changed Field**: A field whose prior and updated values are shown separately as before and after evidence.
- **Evidence Classification**: One of VERIFIED, INFERRED, UNKNOWN, or CONFLICTING, displayed alongside its associated evidence.
- **Recorded Timestamp**: A timestamp with a readable presentation and an exact recorded value that remains available.
- **Source Reference**: A checksum, file name, or record locator associated with case evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In an acceptance review, a reviewer acting as the pharmacist can identify the selected case, each changed field's before and after values, and each evidence classification within 30 seconds without assistance.
- **SC-002**: All existing wording and information remains unchanged, except for readable timestamp presentation and new header or simulated-records notice text; no new case actions, buttons, forms, or clinical wording are added, and existing case selection remains available.
- **SC-003**: At viewport widths from 320 pixels through 767 pixels, the case list and case details remain readable without horizontal page scrolling.
- **SC-004**: At viewport widths of 1024 pixels and wider, the case list remains visible while the case details are scrolled.
- **SC-005**: Every valid timestamp has a readable presentation with its time zone stated, and its exact recorded value is reachable by touch and keyboard without hover; every checksum, file name, and record locator is presented in monospace.
- **SC-006**: All existing frontend tests complete successfully without modification.
- **SC-007**: Every record displayed remains simulated, with zero real patient or medication records introduced.
- **SC-008**: At viewport widths from 768 through 1023 pixels, the case list and details remain side by side, unobscured, and free of horizontal page overflow.
- **SC-009**: Automated tests verify the timestamp fallback and the display of VERIFIED, INFERRED, UNKNOWN, and CONFLICTING.
- **SC-010**: Unavailable case and source evidence retain their existing qualification wording and are visually identifiable as warnings rather than current verification.
- **SC-011**: "Not present in source", "Present but empty", and "No occurrences" are each visually distinguishable from a real source value.
- **SC-012**: Loading, error, and empty states use the page's consistent visual style.
- **SC-013**: When the browser or operating system requests a dark colour scheme, page text meets WCAG 2.2 AA minimum contrast ratios of 4.5:1 for normal text and 3:1 for large text, and content and state distinctions remain readable.

## Assumptions

- The existing Open Review Cases page and its current case data are the source of truth for wording and displayed information; this feature changes presentation, not case behavior or data.
- Mobile usability is evaluated from 320 through 767 pixels. From 768 through 1023 pixels, the case list and details remain side by side in normal flow. At 1024 pixels and wider, the case list remains visible while details are scrolled.
- The simulated-record notice is a brief statement of the existing prototype data boundary, not new clinical wording.
- Existing case selection behavior, if present, is retained; the feature does not introduce new case actions or controls.
- Readable timestamps are shown in UTC and labelled "UTC", so they are consistent for every reviewer. The exact recorded value remains available through touch and keyboard, without mouse hover.
- The page remains readable under a dark colour-scheme preference; this requirement does not require the page to change its chosen palette.
