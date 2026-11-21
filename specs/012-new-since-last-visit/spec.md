# Feature 012: What's New Since Your Last Visit

**Status:** Approved specification (requested by Oli on 2026-11-21: idea 3g, fourth in the order 4 → 2c+2d → 3f → 3g → 2e)
**Branch:** feature/new-since-last-visit

**Supersedes in part:**
- `specs/007-care-loop-review-and-shortage-cases` FR-010 and `specs/006-medicine-shortages` (page controls): one more button, "Mark all as seen", which changes only this browser's memory.

## 1. Objective

A pharmacist who opens the app every few days sees at once what arrived since last time, without accounts or sign-in.

## 2. Scope

### In scope
- The browser remembers its previous visit (local storage only).
- Open Review Cases: a line "N cases are new since your last visit (time)" and a "New since last visit" mark on cases created after it; "Mark all as seen".
- Medicine Shortages: a "Since last visit" mark on shortages whose published "Updated" date is on or after the day of the previous visit.
- Source History: the same line, and marks on releases and shortage files first downloaded after the previous visit and checks made after it.

### Out of scope
- Anything stored on the server, per-user tracking, or sharing between browsers.
- Hiding or sorting by newness; any change to cases.

## 3. Requirements

- **FR-001** A visit MUST be a session: page loads less than 30 minutes after the last one belong to the same visit and keep the same previous visit; a later load starts a new visit whose previous visit is the old one's last time.
- **FR-002** The first visit in a browser MUST show no line and no marks.
- **FR-003** "Mark all as seen" MUST set the previous visit to now in this browser and remove all marks; it MUST send nothing to the server.
- **FR-004** If local storage is blocked or unreadable, the app MUST work as on a first visit and never fail.
- **FR-005** Shortage marks MUST compare only dates in the published `YYYY-MM-DD` form; other forms are never marked.
- **FR-006** Wording MUST stay non-clinical; the mark says "New since last visit", distinct from the case status "New".

## 4. Acceptance criteria

1. With a stored earlier visit, cases created after it are marked and counted; "Mark all as seen" clears them and sends no request; a first visit shows nothing.
2. Source History marks the releases and shortage files first downloaded after the previous visit; Medicine Shortages marks rows by "Updated" date.
3. Visit rules, storage failures and date comparisons are covered by unit tests.
4. All tests, lint, format, type check and build pass; no contrast failures or horizontal overflow at 320–1440 px.
