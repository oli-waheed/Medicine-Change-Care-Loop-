# Feature 009: Faster, Lighter Catalogue

**Status:** Approved specification (requested by Oli on 2026-11-21: idea 4, first in the order 4 → 2c+2d → 3f → 3g → 2e)
**Branch:** feature/faster-lighter-catalogue

## 1. Objective

Reading a real Basic Register release took about 33 s and 2.3 GB of memory (`specs/004-interactive-medicine-catalogue/research.md`, T005). The first catalogue request after every restart waited that long, and loading a new release needed several gigabytes. Make reading a release several times faster and lighter without changing any result.

## 2. Scope

### In scope
- The normaliser (`normalize_basic_register_release`) used by ingestion, the catalogue and the comparison helper.

### Out of scope
- A stored copy of normalised records (for example a cache file). Measured: loading such a copy would take about 5 s against about 12 s for reading the XML, and would add a second copy that must be kept in step with the code. Not worth it now.
- Any change to snapshots, comparison, matching, cases, the API or the pages.

## 3. Requirements

- **FR-001** For every document, the normaliser MUST return snapshots equal to those of the previous normaliser, or raise the same kind of error for the same problem, with the same check order (document root, version, coverage, record identities, then each package in source order).
- **FR-002** The document MUST be read as a stream: each top-level record is normalised when it ends and then dropped, so the whole XML tree is never held in memory.
- **FR-003** Each product and active-substance record MUST be normalised once and shared by all its packages; equal source values MUST be shared as one immutable object.
- **FR-004** A malformed product or substance record MUST still only fail the release when a package uses it.

## 4. Acceptance criteria

1. On both real releases (2026-10-06 and 2026-11-21) the new and the previous normaliser give equal results.
2. Reading a real release takes under 15 s and under 500 MB (with the raw file in memory).
3. All tests, lint, format and the browser checks pass; the catalogue answers as before.

## 5. Results (2026-11-21, real releases, same machine)

| | Before | After |
|---|---|---|
| Normalise one real release | 31.5 s, peak about 2.3 GB | 11.6 s, about 410 MB including the 200 MB raw file |
| First catalogue request after a restart | about 35 s | 12.6 s |
| Backend memory with the catalogue loaded | about 2.3 GB | about 270 MB |
| Upload of the newer release (compare with the older one, create cases) | one to two minutes | 41 s, peak 614 MB |
| Snapshots | 146,042 and 146,868 | equal, field for field |
