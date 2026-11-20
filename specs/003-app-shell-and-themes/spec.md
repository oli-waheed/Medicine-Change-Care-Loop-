# Feature Specification: Application Shell and Open Review Cases Workspace

**Feature Branch**: `feature/application-shell-and-catalogue` (Spec Kit folder `specs/003-app-shell-and-themes`)

**Created**: 2026-11-20 · **Revised**: 2026-11-20 (final design handoff; About the Data restored)

**Status**: Approved

**Input**: User description and the approved "Medicine Change Care Loop — final design handoff": a professional healthcare SaaS interface in a **light theme only**, with balanced information density; a persistent sidebar with branding, Open Review Cases, About the Data, Fimea Basic Register attribution and application information; a searchable, keyboard-navigable case queue; separate review layouts for changed packages (`FIELDS_CHANGED`) and removed packages (`NO_LONGER_PRESENT`), with prior/current release labels and added/removed/changed field indicators; evidence and provenance always visible; the handoff palette (navy #102D3B, teal #176B65, pale mint #E8F3EF, page background #F3F6F7, surface #FFFFFF, amber #D69B35, error #B74747); a collapsible sidebar on tablets and a drawer on mobile. Preserve all existing behaviour, wording, important CSS class names, and the distinctions between missing values, empty values, no occurrences and unavailable raw source evidence. No backend, API, ingestion or matching changes; no Processing Outcomes navigation; no dark theme or theme switching.

**Revision notes**: The first draft of this feature included a dark theme and a theme switch; the final design handoff excludes them, so they were removed. The folder name `003-app-shell-and-themes` is kept so Spec Kit paths stay stable. Commit `16927e2` briefly excluded About the Data; it is restored here because the design handoff's acceptance criteria require it ("About the Data page explains the Fimea Basic Register source") and it is a working page, not a placeholder.

**Supersedes in part**: `specs/002-case-review-readability` FR-002 (only the additions listed in FR-021 of this spec are new displayed text) and FR-010 (the navigation controls and the read-only case search of FR-025 are new controls). The light-only theme of 002 remains in force.

**Superseded in part by**: `specs/004-interactive-medicine-catalogue` — FR-001 and FR-002 (the sidebar also lists "Medicine Catalogue" at `/medicine-catalogue`) and FR-025 (the catalogue page's read-only search, filter and view controls).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Move around the review workspace (Priority: P1)

A pharmacist opens Medicine Change Care Loop and sees a persistent sidebar with the product name, the two available pages (Open Review Cases and About the Data) and the Fimea Basic Register attribution. They can move between the pages and always know which page they are on.

**Why this priority**: The sidebar is the frame every other part of the design lives in, and it keeps the data source and its licence visible.

**Independent Test**: At a wide viewport, use the sidebar to move between the two pages with mouse and keyboard, use back and forward, and confirm the current page is indicated and no other navigation items exist.

**Acceptance Scenarios**:

1. **Given** a viewport at least 1024 pixels wide, **When** any page is shown, **Then** the sidebar is visible and contains the product name, links to Open Review Cases and About the Data, and the Fimea Basic Register attribution with a licence link.
2. **Given** Open Review Cases is shown, **When** the pharmacist activates About the Data, **Then** that page is shown without a full reload, the address changes, and its link is marked as current.
3. **Given** the pharmacist moved to About the Data, **When** they use the browser's back button, **Then** Open Review Cases is shown again.
4. **Given** an address that matches no page, **When** it loads, **Then** "Page not found" is shown inside the workspace with a link to Open Review Cases.
5. **Given** the project defines a real application version, **When** the sidebar is shown, **Then** the version is displayed; with only the placeholder version, no version is displayed.

---

### User Story 2 - Review changed and removed packages with full evidence (Priority: P2)

A pharmacist selects a case and immediately recognises whether the package changed or is no longer in the register, because each kind has its own layout. For a changed package, each field shows its prior-release and current-release values and whether the field was added, removed or changed. All source evidence and provenance stay visible, and every kind of absent or unavailable information keeps its own meaning.

**Why this priority**: Recognising the kind of change is the core review task; the evidence rules protect the project's evidence-honesty principle.

**Independent Test**: Load the two simulated cases (Fictional Product Amber, changed; Fictional Product Cedar, removed) and fixtures covering every value state; confirm each case uses its own layout, each field shows the right indicator, and every evidence value and absence state keeps its wording.

**Acceptance Scenarios**:

1. **Given** a changed-package case (`FIELDS_CHANGED`), **When** it is selected, **Then** each changed field shows its field path, a field indicator, and "Before · Prior release" and "After · Current release" values side by side, with the number of changed fields.
2. **Given** a changed field that is absent (missing or no occurrences) in the prior release and present in the current release, **When** it is shown, **Then** its indicator reads "Field added"; absent in the current release but present in the prior: "Field removed"; present in both: "Value changed".
3. **Given** a removed-package case (`NO_LONGER_PRESENT`), **When** it is selected, **Then** the layout leads with "Package no longer present in the register" and the existing removal statement, then the last known values from the prior release, and shows no "Before" or "After" labels and no field indicators.
4. **Given** any case, **When** it is selected, **Then** the matched simulated record, the source order and its basis, and the prior and current source evidence (source, release reference, release date, raw file, checksum, record locator, retrieval time, classification, note) are all visible without any further interaction.
5. **Given** values that are missing, empty, have no occurrences, or whose raw source file is no longer stored, **When** they are shown, **Then** each keeps its existing wording and its own visual treatment, distinct from real values and from each other, and the historical classification stays visibly separate from the current availability of the raw file.

---

### User Story 3 - Find and move through cases quickly (Priority: P3)

A pharmacist narrows the case queue by typing part of a medicine name, identifier or change summary, and moves through the queue with the keyboard.

**Why this priority**: The handoff requires a searchable queue with keyboard navigation; it speeds up review as the number of cases grows.

**Independent Test**: With several cases loaded, type in the search field and confirm the queue filters without new requests; move through the queue with arrow keys, Home and End, and select with Enter.

**Acceptance Scenarios**:

1. **Given** cases are loaded, **When** the pharmacist types in "Search cases", **Then** only cases whose name, identifier or change summary contain every typed word (ignoring case) remain in the queue, and the number shown out of the total is announced.
2. **Given** a search matches nothing, **When** the queue is empty, **Then** "No cases match this search." is shown and the details of the selected case remain visible.
3. **Given** focus is on a case in the queue, **When** the pharmacist presses Down, Up, Home or End, **Then** focus moves to the next, previous, first or last visible case, without changing the selection; Enter or Space selects the focused case.
4. **Given** any search or keyboard movement, **When** it happens, **Then** no request for case data is made.

---

### User Story 4 - Use the workspace on a tablet, phone or keyboard (Priority: P4)

On a tablet the sidebar collapses to an icon rail that can be expanded; on a phone it becomes a drawer behind a "Menu" button. Keyboard users can reach every control, see where focus is, and skip to the main content.

**Why this priority**: Required by the handoff's responsive and accessibility requirements; builds on User Story 1.

**Independent Test**: At 320, 768, 1023 and 1440 pixels, open and close navigation with mouse and keyboard; tab through every page; confirm focus handling, Escape behaviour and no horizontal page scrolling.

**Acceptance Scenarios**:

1. **Given** a viewport from 768 to 1023 pixels, **When** any page is shown, **Then** the sidebar shows as an icon rail with a "Sidebar" toggle that reports whether it is expanded, and the case queue and review workspace sit side by side.
2. **Given** a viewport narrower than 768 pixels, **When** any page is shown, **Then** the sidebar is hidden and a top bar shows the product name and a "Menu" toggle; the case queue and details are a single column.
3. **Given** the navigation is collapsed on a tablet or phone, **When** its toggle is activated, **Then** the full sidebar opens over the content, the toggle reports it is expanded, and focus moves to the first navigation link.
4. **Given** the navigation is open, **When** the pharmacist presses Escape, activates the toggle again, follows a link or clicks outside, **Then** it closes and, except after following a link, focus returns to the toggle.
5. **Given** the navigation is open, **When** Tab is pressed repeatedly, **Then** focus stays within the sidebar and the content behind it cannot be reached.
6. **Given** any page, **When** the pharmacist uses the keyboard only, **Then** "Skip to main content" is the first focusable element and every control is reachable with a visible focus indicator.

### Edge Cases

- The OS or browser requests dark colours: the light theme stays and remains readable.
- The viewport grows to 1024 pixels while navigation is open: the persistent sidebar is shown and nothing stays blocked.
- The case list is loading, failed or empty: the sidebar and About the Data stay usable; the existing loading, error and empty messages are unchanged and the search field is not shown.
- The selected case is hidden by a search: its details stay visible; clearing the search shows it in the queue again.
- Very long field paths, checksums and values at 320 pixels: they wrap (field paths after each "/") without horizontal page scrolling.
- A changed field with an empty before or after list: that side reads "No occurrences" and the indicator treats it as absent.
- A field that is present but empty on one side and absent on the other: treated as present ("Field added" or "Field removed").
- A field reported as present without a delivered value: "Value unavailable", with its own treatment.
- Placeholder version `0.0.0`: no version shown.
- An address with a trailing slash: same page.

## Requirements *(mandatory)*

### Functional Requirements

**Workspace and navigation**

- **FR-001**: From 1024 pixels wide, every page MUST show a persistent sidebar containing, in order: the product name; navigation links "Open Review Cases" and "About the Data"; a short Fimea Basic Register attribution with a link to the CC BY 4.0 licence; and the application version when FR-006 allows it.
- **FR-002**: The sidebar MUST NOT contain any other navigation item, including Processing Outcomes, or any item without a working page.
- **FR-003**: Open Review Cases MUST be at `/` and About the Data at `/about-data`. Following a sidebar link MUST change the address and page without a full reload; back and forward MUST work.
- **FR-004**: The link of the shown page MUST be marked as current, visually and for assistive technology.
- **FR-005**: Any other address MUST show "Page not found" with a link to Open Review Cases, inside the workspace.
- **FR-006**: The version MUST come from the project's version metadata; the placeholder `0.0.0` MUST NOT be displayed.
- **FR-007**: The tab title MUST be "Open Review Cases | Medicine Change Care Loop", "About the Data | Medicine Change Care Loop" or "Page not found | Medicine Change Care Loop".

**About the Data**

- **FR-008**: About the Data MUST state, consistent with the README "Data Source and Licence" section: all patient and medication records are simulated; the source is the Basic register for medicinal products (Perusrekisteri) of the Finnish Medicines Agency Fimea, open data under CC BY 4.0, with links to the licence and Fimea's open-data page; how to attribute (licensor, material, release date); that the project normalises selected fields and compares releases and these comparisons are the project's, not Fimea's; that Fimea does not guarantee completeness or currency; that the test fixtures are synthetic; and that the application presents source information for pharmacist review only and makes no clinical decisions.

**Visual design**

- **FR-009**: The application MUST use a light theme only, with the handoff palette: navy #102D3B, teal #176B65, pale mint #E8F3EF, page background #F3F6F7, surface #FFFFFF, amber #D69B35 and error #B74747, and Inter or the system sans-serif. Monospace MUST be used only for identifiers, checksums, file names, record locators and field paths. There MUST be no dark theme and no theme switch, and the page MUST stay readable when the OS or browser requests dark colours.
- **FR-010**: Text MUST meet WCAG 2.2 AA contrast (4.5:1 normal, 3:1 large); focus indicators, the selected-case indication and state-label borders MUST meet 3:1. Where amber does not reach these ratios, it MUST be used only as a fill or accent next to text and borders that do. Every state distinction MUST remain recognisable without colour.

**Responsive layout and keyboard access**

- **FR-011**: From 768 to 1023 pixels, the sidebar MUST be an icon rail with a toggle named "Sidebar" that reports whether it is expanded; expanding shows the full sidebar over the content. Link names MUST remain available to assistive technology in the rail.
- **FR-012**: Below 768 pixels, the sidebar MUST be hidden behind a "Menu" toggle in a top bar that also shows the product name; the toggle MUST report whether the navigation is expanded.
- **FR-013**: When the navigation opens (rail expanded or drawer), focus MUST move to the first navigation link; Tab and Shift+Tab MUST stay within the sidebar; the content behind MUST NOT be reachable; Escape, the toggle and a click outside MUST close it and return focus to the toggle; following a link MUST close it.
- **FR-014**: Every page MUST start with a "Skip to main content" link as the first focusable element, and every control MUST be keyboard operable with a visible focus indicator.
- **FR-015**: From 320 pixels, no page MUST scroll horizontally. The case queue and review workspace MUST be side by side from 768 pixels and a single column below; from 1024 pixels the queue MUST stay visible while the details scroll.

**Case queue**

- **FR-016**: The case queue MUST show, for each case, the medicine name, identifier, change summary, status and any evidence-unavailable warning, and MUST mark the selected case clearly.
- **FR-017**: The case queue MUST include a search field labelled "Search cases" that filters the loaded cases to those whose name, identifier or change summary contain every typed word, ignoring case. While a search is active, the queue MUST announce "Showing n of N"; with no match it MUST show "No cases match this search.". Searching MUST NOT change the selected case or cause any request.
- **FR-018**: With focus on a case in the queue, Down, Up, Home and End MUST move focus to the next, previous, first and last visible case without changing the selection; Enter and Space MUST select it.

**Review workspace and evidence**

- **FR-019**: Changed-package cases (`FIELDS_CHANGED`) and removed-package cases (`NO_LONGER_PRESENT`) MUST each use their own layout, with a kind badge reading "Updated package" or "Removed package". The changed layout MUST show the number of changed fields and, per field, the field path, a field indicator, and "Before · Prior release" and "After · Current release" values side by side. The removed layout MUST lead with "Package no longer present in the register" and the existing removal statement, followed by "Last known values (prior release)", and MUST NOT show "Before", "After" or field indicators. Neither layout MUST suggest a reason for the change or a clinical conclusion.
- **FR-020**: Field indicators MUST be derived only from source presence: a side is absent when all its values are missing or it has no occurrences, and present otherwise (including empty values). Absent → present: "Field added"; present → absent: "Field removed"; otherwise "Value changed".
- **FR-021**: The only new displayed text on Open Review Cases MUST be: the kind badges (FR-019), "Prior release" and "Current release", the field indicators (FR-020), the search label, status and no-match messages (FR-017), the "No occurrences" fallback (FR-024), the search placeholder "Name, identifier or change", the sidebar tooltips "Expand sidebar", "Collapse sidebar" and the navigation link names, and the shell texts of FR-001, FR-005 and FR-014.
- **FR-022**: All case information and evidence currently shown MUST remain visible without any expand, collapse or tab interaction: case heading, identifier and granularity, status, evidence-unavailable banner, matched simulated record, case creation time, case classification, changed fields or last known values, source order and basis, and both source-evidence cards with all fields and notes.
- **FR-023**: The value and availability states MUST keep their wording and remain visually distinct from real values and each other: "Not present in source" (missing), "Present but empty" (empty without a code value), "No occurrences" (zero occurrences), unavailable raw source evidence ("Evidence unavailable", the evidence-unavailable banner, "(no longer stored)", and "… when recorded; source file now unavailable" / "… when recorded; source evidence now unavailable"), "Unknown", "Not captured", "Not in this release" and "Value unavailable". A code-table value of an otherwise empty field MUST still be shown as a real value. The historical classification and the current availability of the raw file MUST stay separately visible.
- **FR-024**: A changed field whose before or after list is empty MUST show "No occurrences" for that side.

**Scope, safety and preservation**

- **FR-025**: The application MUST NOT add case actions, forms or clinical wording anywhere. The only interactive controls MUST be: case-selection buttons; the "Search cases" field; the two sidebar links; the skip link; the "Menu" and "Sidebar" toggles; the licence and Fimea open-data links; and the Page not found link.
- **FR-026**: Data loading MUST remain unchanged: one read of the open cases each time Open Review Cases is shown; searching, selecting, moving focus, opening navigation, and showing About the Data or Page not found MUST NOT request case data. No backend, API, ingestion or matching change is part of this feature.
- **FR-027**: All 002 requirements not listed under "Supersedes in part" MUST remain satisfied, including readable UTC timestamps with exact values, the simulated-records notice, wording, and the loading, error and empty states.
- **FR-028**: All displayed records MUST remain simulated.

**Verification**

- **FR-029**: Existing frontend tests MUST keep passing. The clinical-scope test MUST check the case-selection buttons specifically and allow exactly one form control, the read-only search field. A new application-level test MUST verify the FR-025 control list and the absence of clinical wording on every page, with the navigation open and with a search active.
- **FR-030**: New automated tests MUST cover navigation and current-page marking, Page not found, About the Data, the version rule, the navigation toggles' keyboard and focus behaviour, the two review layouts, the field indicators, the release labels, the empty before/after fallback, search filtering and keyboard movement in the queue.

### Key Entities *(include if feature involves data)*

- **Page**: Open Review Cases, About the Data or Page not found; identified by its address.
- **Navigation state**: collapsed or expanded; relevant below 1024 pixels.
- **Case search query**: the text typed in "Search cases"; held only on the page, never sent anywhere.
- **Review layout**: changed package or removed package, from the case's change kind.
- **Field indicator**: Field added, Field removed or Value changed, from source presence of the before and after values.
- **Application version**: the project's declared version; displayed unless it is the placeholder.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A team member acting as pharmacist can tell whether each simulated case is a changed or removed package within 5 seconds of selecting it.
- **SC-002**: All texts in FR-023 and all evidence fields in FR-022 are present for both simulated cases with no interaction beyond selecting the case.
- **SC-003**: 100% of checked text and state-indicator colour pairs meet FR-010.
- **SC-004**: At 320, 375, 768, 1023, 1024 and 1440 pixels, no page scrolls horizontally; the sidebar is a drawer below 768, a rail from 768 to 1023 and persistent from 1024 pixels.
- **SC-005**: Every page can be operated with the keyboard alone, including the navigation toggles and the case queue, with a visible focus indicator at every step.
- **SC-006**: Typing a medicine name or identifier narrows the queue to the matching cases with zero additional requests.
- **SC-007**: All existing frontend tests pass, the new tests in FR-030 pass, and build, lint and format checks pass.
- **SC-008**: Searching, selecting and moving between pages produce zero case-data requests beyond one per display of Open Review Cases.
- **SC-009**: No page contains clinical wording matched by the project's clinical-scope word list, and the only form control is the search field.

## Out of Scope

The following are not part of feature 003 and may become separate features with their own specifications: Medicine Catalogue; Change Intelligence Dashboard; Medicine History; a Data Quality and Provenance module; Processing Outcomes; dark theme or theme switching; non-functional navigation links; backend, API, database, ingestion, matching or source-processing changes; any clinical or pharmacist decision-making functionality.

**Preservation rule**: Feature 003 must not silently alter existing behaviour or source-data meaning. Any feature 002 requirement not explicitly changed by this specification remains in force.

## Assumptions

- `localhost:5174/dashboard` showed the existing Open Review Cases page because the development server serves the application for every address; after this feature it shows Page not found.
- The current version is the placeholder `0.0.0`, so no version is shown until the team sets one.
- About the Data reuses facts already recorded in the README.
- The handoff's proposed component names map to this implementation as: CaseQueue → `CaseList`, CaseQueueItem → the case button in `CaseList`, ReviewWorkspace → `CaseDetail`, EvidenceLabel → `EvidenceClassificationLabel`, AboutTheDataPage → `AboutDataPage`; UpdatedPackageReview, RemovedPackageReview, ProvenancePanel, AppShell and Sidebar keep their names.
- The removed-package heading keeps the existing wording "Package no longer present in the register" (decision of 2026-11-20), not the handoff's "Package absent from current register".
- The backend and the open-review-cases response do not change.
