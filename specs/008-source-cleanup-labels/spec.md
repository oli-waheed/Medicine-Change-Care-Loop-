# Feature 008: Labels for Likely Source Clean-ups

**Status:** Approved specification (requested by Oli on 2026-11-21: "Label Fimea's data clean-ups", roadmap §2 item 3)
**Branch:** feature/source-cleanup-labels

**Supersedes in part:**
- `specs/007-care-loop-review-and-shortage-cases` FR-010: the case list gets one more reading control, "Set aside likely source clean-ups".

## 1. Objective

The comparison of two real Fimea releases (`docs/validation/2026-11-21-real-release-comparison.md`, finding 3) found that 848 of 1,915 changed packages differed only in active-substance fields, mostly because Fimea restructured its strength data, and 113 only in spaces or letter case. Each would become a review case. Reviewers need to recognise these quickly, without the app hiding, closing or judging anything.

## 2. Scope

### In scope
- A deterministic label on release review cases: **Spacing or letter case only** or **Active-substance fields only**.
- A per-field marker for a field whose values differ only in spaces or letter case.
- A reviewer-controlled switch in the case list that sets labelled cases aside for the moment; off by default.

### Out of scope
- Hiding, closing, deleting or changing the status of any case automatically.
- Not creating cases for labelled changes. Every difference is still detected and every case is still created.
- Normalising or rewriting source values. Values are shown exactly as published.
- Labels on shortage cases or on the change-processing outcomes list.
- Any statement about the clinical importance of a change.

## 3. Requirements

- **FR-001** A field change is *formatting only* when the before and after lists have the same number of occurrences and, for each pair, the same state, the same attributes, and values that are equal after collapsing runs of whitespace, trimming and case-folding, while the lists as published differ.
- **FR-002** A release case with field changes gets the label `FORMATTING_ONLY` when every field change is formatting only; otherwise `ACTIVE_SUBSTANCE_ONLY` when every changed field path starts with `Laakeaine/`; otherwise no label. Cases for packages no longer in the register have no label.
- **FR-003** Labels MUST be worked out when a case is read, from the stored before and after values, so cases created before this feature are labelled too, and stored case data is never rewritten.
- **FR-004** The case API (`GET /api/open-review-cases`, the answer of `POST /api/review-cases/{caseId}/status-events`) MUST return `changeSet.cleanupLabel` (`FORMATTING_ONLY`, `ACTIVE_SUBSTANCE_ONLY` or `null`) and `formattingOnly` on each field change of a release case. Shortage cases are unchanged.
- **FR-005** The case list MUST show the label as a neutral badge on labelled cases. The case page MUST show a notice explaining the label and that it never changes the case's status, and mark each formatting-only field.
- **FR-006** When at least one case in the list is labelled, the list MUST offer "Set aside likely source clean-ups", off by default. Turning it on removes labelled cases from the visible list only; the count, search and "Show reviewed cases" keep working, and nothing is sent to the server.
- **FR-007** All wording MUST stay non-clinical and pass the clinical-wording guards.

## 4. Acceptance criteria

1. With the synthetic fixtures (`cleanup-release.xml` after `current-release.xml`), the case for SIM-PKG-100 is `FORMATTING_ONLY`, SIM-PKG-200 is `ACTIVE_SUBSTANCE_ONLY` and SIM-PKG-500 (substance and package fields) has no label; values are returned exactly as published.
2. Labels never change a status and every case is still listed.
3. The switch is off by default, sets aside only labelled cases, sends no request, and is not shown when no case is labelled.
4. All backend and frontend tests, type check, lint, format check and build pass; the case page has no contrast failures or horizontal overflow at 320–1440 px.

## 5. Decisions (2026-11-21)

- D1 Labels describe; they never hide by default or change a case. (Validation report finding 3)
- D2 The substance label covers all active-substance-only changes, including renames, and says so; the values are always shown. (Oli)
