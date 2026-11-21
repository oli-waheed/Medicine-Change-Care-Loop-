# Feature 009: Implementation Plan

- `backend/src/services/normalize_basic_register_release.py`:
  - `_Fields` builds source fields and keeps one object per distinct (text, attributes) pair; a real release has about 3.9 million field occurrences and about 90,000 distinct values.
  - `ET.iterparse` replaces `ET.fromstring`. When a top-level `Pakkaus`, `Laakevalmiste`, `Laakeaine` or `Versiotiedot` ends, its fields are extracted and the element is removed from the root.
  - `_Deferred` holds a record's result or its `ValueError`; errors are raised only when the record is used, and all checks run after reading in the previous order (FR-001, FR-004).
  - Products (with their authorisations) and substances are normalised once and shared (FR-003).
- Tests: `tests/unit/basic-register-normalization/test_normalization_sharing.py` (sharing, equality, lazy errors, link and identity errors, root and version). The existing normalisation, ingestion and comparison tests cover unchanged results.
- Equality on real data was checked with the previous normaliser side by side (not committed: the real files are not in the repository).

## Risks

- Shared objects are immutable dataclasses, so sharing cannot change a value; code that compares by identity (`is`) would see more sharing, and there is none.
