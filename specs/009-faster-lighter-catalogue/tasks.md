# Feature 009: Tasks

**Status (2026-11-21)**: T001–T005 done; T006 is the user's approval and commit.

- [x] T001 Measure the current cost on the real releases: 31.5 s and about 2.3 GB per release; 3.9 million field occurrences, about 90,000 distinct; XML tree alone about 1.4 GB.
- [x] T002 Specify the feature (`spec.md`, `plan.md`); decide against a stored cache (loading it about 5 s, not worth a second copy).
- [x] T003 Stream the document, share equal values and shared records, keep the check order (FR-001–FR-004).
- [x] T004 Tests for sharing and unchanged checks; equality with the previous normaliser on both real releases.
- [x] T005 Verify: `python -m pytest` 315 passed; Ruff clean; `npx vitest run` 96 passed; real-data timings in `spec.md` §5; README and the 004 research note updated.
- [ ] T006 Obtain explicit approval before committing or pushing.
