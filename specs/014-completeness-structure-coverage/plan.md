# Feature 014: Implementation Plan

- `domain/source_release`: `schema_location` and `structure` on `SourceRelease`, both `compare=False`, so identity and every existing comparison are unchanged.
- `services/normalize_basic_register_release.py`: reads `xsi:noNamespaceSchemaLocation` from the root and counts element paths of each top-level record before it is dropped (about +1–3 s on a real release).
- `services/release_quality_checks.py`: `completeness()`, `_completeness_check()`, `_structure_check()`; `CHECK_VERSION = 2`; `completeness` rows in the payload.
- `services/pipeline_store.py`: a newer-version check replaces an older one; `has_quality_check(check_id, version)`.
- `workflows/release_quality.py`: backfill treats an older-version check as missing.
- `api/source_history.py`: `upToDate` on each check.
- Frontend: completeness table and earlier-version note on Source History; coverage notice on Medicine Shortages.
- Docs: roadmap rewritten after the reviews (direction A/B, features from 015, verified legal points).
