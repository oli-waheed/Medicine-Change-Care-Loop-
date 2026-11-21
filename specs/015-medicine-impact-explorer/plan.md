# Feature 015: Implementation Plan

- **Domain / normaliser**: `AuthorizationRegistrationFields.haltija` (default missing); the normaliser reads `Haltija`; `project_snapshot_fields()` skips it (`_NOT_COMPARED`).
- **Service** (`services/medicine_links.py`): `build_link_index()` (product, VNR, substance code, substance name, holder exact and folded, trade name), cached per release by `LinkIndexCache` on `app.state`; `links_for(index, anchors, shortages=…)` returns the groups.
- **API** (`api/medicine_catalogue.py`): two GET endpoints; shortage rows come from the Shortages page's checksum-verified reader. Backend scope guard allows them. Contract: `contracts/links-api.md`.
- **Frontend**: `LinkedRecordsCard` on the package and product pages (`fetchLinks`, types in `medicineCatalogue.ts`, styles); product page can open products; app scope test allows "Show more (n)" and "Show fewer".
- **Tests**: `tests/fixtures/fimea-basic-register/links-release.xml`; `tests/integration/medicine-links/`; `LinkedRecords.test.tsx` against responses captured from the real backend (`src/test/linkedRecordsResponses.json`, served by `catalogueFetch`).
