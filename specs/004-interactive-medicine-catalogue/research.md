# Feature 004: Technical Inspection (T001–T005)

Inspected on 2026-11-20 against `main` at `b8bd732`. Each section records what exists today and what it means for the catalogue.

## T001 — Backend API schemas and router conventions

**Findings**

- One FastAPI `APIRouter` per resource in `backend/src/api/`, with the full prefix on the router (`/api/open-review-cases`, `/api/change-processing-outcomes`, `/api/source-releases`) and the collection route registered as `""`. All routers are added in `backend/src/main.py` with `app.include_router(...)`.
- Handlers take `request: Request` and read shared state from `request.app.state` (`store: PipelineStore`, `medication_records`, `source_release_config`). There is no dependency injection layer.
- Responses are plain `dict` / `list[dict]` values built by functions in `backend/src/schemas/` (for example `schemas/open_review_cases.py`). There are no Pydantic response models.
- Keys are camelCase (`sourceName`, `releaseDate`, `retrievedAt`, `evidenceClass`).
- Every source value is serialised as `{"state": "value" | "empty" | "missing", "value": str | null, "attributes": {...}}` (`_field` in `schemas/open_review_cases.py`). Code-table attributes (`listname`, `id`, `value`) stay in `attributes`.
- Query parameters use `Annotated[..., Query()]`. Invalid parameter values raise `HTTPException(status_code=422, detail="...")` with a readable message (`api/change_processing_outcomes.py`).
- All existing read endpoints are `GET` and read-only. Tests call handlers directly with a constructed `starlette.requests.Request` and the `isolated_app` fixture (`tests/conftest.py`).

**Implications for 004**

- Add `backend/src/api/medicine_catalogue.py` (router prefix `/api/medicine-catalogue`) and `backend/src/schemas/medicine_catalogue.py`, registered in `main.py`.
- Reuse the `{state, value, attributes}` source-value shape unchanged, so missing, empty and present values stay distinguishable in every response (FR-003, FR-007).
- Hold one `MedicineCatalogueService` on `app.state` so its baseline cache is shared across requests.

## T002 — Source-release loading and snapshot reconstruction

**Findings**

- `PipelineStore.comparison_baseline()` returns the latest capture that is `VALIDATED` and has a `source_order_key` (verified `Ajopvm` chronology). Ties on `Ajopvm` keep the first capture. Releases without verified chronology are never selected.
- `reload_captured_release(capture_directory)` rebuilds the `IngestionOutcome` from the immutable files on disk, re-checks each file against its recorded SHA-256 checksum, and raises `ValueError` if a file no longer matches.
- `MedicineCatalogueService` (T007, T008) uses both, caches one reconstructed release keyed by `release_id`, clears the cache when no baseline exists, and raises `ValueError` if the capture cannot be reconstructed as validated.
- Verified by the T027 integration tests: selection, replacement by a newer release, older and unverified releases, restart, cache reuse and clearing, and rejection of a tampered capture.

**Implications for 004**

- The API must turn "no baseline" into the explicit unavailable response of FR-009, and a reconstruction failure into an explicit error. It must never fall back to another release.
- Catalogue reads never write to the store, so FR-010 is met by construction as long as the API calls only `comparison_baseline()` and `reload_captured_release()`.

## T003 — Product reference, VNR and package identity fields

**Findings** (`backend/src/domain/medicine_snapshot/__init__.py`, `services/normalize_basic_register_release.py`)

- One `MedicineSnapshot` per `Pakkaus` element. `pakkaustunnus` is a required plain string and is the package-record identity.
- `vnr_numero` is a `SourceField` read from `Pakkaus/VNR-numero`. It is package-level, can be `missing` or `empty`, and is never inferred.
- `product_reference` is a `SourceField` holding the `Laakevalmiste-ref` of the package, which is the `id` of the `Laakevalmiste` element. The model's docstring states that references are scoped to their source release, so a product reference is not a stable identity across releases.
- Product fields (`ProductFields`): `kauppanimi`, `vahvuus`, `laakemuoto`, `atc_koodi`, `antoreitti` (repeated, source order).
- Active substances (`ActiveSubstanceFields`, repeated, source order): `aine` (code-table `id` and display `value` in attributes), `cas_numero`, `maara`, `maara_yksikko`, `jakamaton_vahvuus`.
- Package fields (`PackageFields`): `pakkauskoko_teksti`, `pakkauskoko`, `pakkauskoko_kerroin`, `pakkauskoko_yksikko`, `julkinen_tarkenne`, and `availability` (`kaupan`, `kauppaantulo_paiva`, `kaupasta_poistumis_paiva`).
- Authorizations: repeated `Myyntilupa` / `Erityislupa` / `Rekisterointi` branches with `tila`, `myontamis_paiva` and `paattymis_paiva`.
- Provenance: each snapshot carries its `SourceRelease` (`ajopvm`, `aineistoera`, source name, raw file name, checksum, retrieval time) and its `source_record_locator`.
- **Not normalised today:** GTIN, NTIN and `Reseptistatus` (the last one appears in the fixtures but is not read). Field paths used by change detection come from `project_snapshot_fields()` (for example `Laakevalmiste/Kauppanimi`, `Pakkaus/Kaupanolo/Kaupan`).

**Implications for 004**

- VNR is a package attribute. Product details (FR-004) show the VNRs of the product's packages, each with its own package identity.
- VNR grouping (FR-013) may only group packages whose VNR `state` is `value` and whose values are equal. Missing or empty VNRs are never grouped.
- Product lookups are valid only within the active release, so every response states the `releaseId` it refers to.
- GTIN and NTIN cannot be displayed without extending normalisation, which is outside this feature (FR-010 and the plan's "do not modify the existing ingestion" constraint). Requirement 8 ("GTIN and NTIN remain distinct from VNR") is met because the catalogue does not expose them. Adding them needs a separate, approved decision.
- Comparison (FR-007) should reuse the `project_snapshot_fields()` paths without modifying that function, so field names match the review workspace and T005 behaviour stays unchanged.

## T004 — Frontend routing, navigation and existing UI components

**Findings**

- Pages are chosen in `frontend/src/App.tsx` from the URL path via `frontend/src/app/navigation.ts` (`NAVIGATION_ITEMS`, `pageForPath`, `navigate`, `useCurrentPath`). There is no router package.
- Sidebar links come from `NAVIGATION_ITEMS` and are rendered in `frontend/src/app/Sidebar.tsx` with an icon map in `icons.tsx`.
- Styling is **plain CSS with design tokens** in `frontend/src/index.css` (light theme only) plus one stylesheet per page or component. **The project does not use Tailwind.** `plan.md` §2.5 said "Tailwind"; this is corrected in the plan.
- Reusable evidence components: `SourceValueDisplay` / `SourceValueInline` / `SourceValueParagraphs` (missing, empty, no-occurrences and value-unavailable states), `EvidenceClassificationLabel`, `TimestampDisplay` and `FieldPath` in `frontend/src/pages/open-review-cases/evidence/`.
- Guard tests:
  - `frontend/src/app/App.scope.test.tsx` allows only listed buttons, links and a single `input[type=search]` named "Search cases", and no `select`, `textarea` or `form`.
  - `src/test/clinicalWords.ts` forbids clinical wording on every page.
  - Feature 003 FR-001 and FR-002 limit the sidebar to Open Review Cases and About the Data.

**Implications for 004**

- Add `"medicine-catalogue"` to `PageId`, `NAVIGATION_ITEMS`, the icon map and `App.tsx` (FR-001).
- Feature 004 must state that it supersedes 003 FR-001/FR-002 (sidebar items) and FR-025 (allowed controls) in part. The App scope test must be updated deliberately, for example by allowing the catalogue's labelled search field and filter controls.
- Reuse the evidence components rather than writing new value renderers, so missing, empty and no-occurrences look the same as in the review workspace.

## T005 — Captured release size and loading performance

**Status: synthetic benchmark done; measurement on a real Fimea file pending.**

A real Basic Register download is not stored in the repository (the fixtures are 5 KB). As an indication, the fixture structure was replicated with unique identifiers and normalised with `normalize_basic_register_release()` in the project's Python 3.13 environment on a 2-core x86_64 machine:

| Synthetic packages | XML size | Normalisation time | One `search()` call |
|---|---|---|---|
| 2,000 | 2.6 MB | 0.4 s | 3 ms |
| 20,000 | 25.9 MB | 5.7 s | 23 ms |

**Findings**

- Search over cached snapshots is fast (tens of milliseconds even for 20,000 packages), so in-memory filtering needs no database index.
- Reconstruction is the expensive step: several seconds for a large release, and it grows faster than linearly (10× packages took 14× longer). The one-release cache in `MedicineCatalogueService` (T008) is therefore necessary. The first catalogue request after a restart or a new release pays this cost.
- The synthetic structure is simpler than the real register, so these numbers are indicative only.

**Remaining step (to complete T005)**

1. Save one real Basic Register XML download locally, outside the repository.
2. Record its size: `(Get-Item <file>).Length / 1MB`.
3. Time the reconstruction from the backend folder:
   `python -c "import time,hashlib,sys; sys.path.insert(0,'.'); from src.services.normalize_basic_register_release import normalize_basic_register_release as n; b=open(r'<file>','rb').read(); t=time.perf_counter(); r,s=n(b,file_name='real.xml',checksum=hashlib.sha256(b).hexdigest()); print(len(s),'packages',round(time.perf_counter()-t,2),'s')"`
4. Add the results to this section. If reconstruction takes more than about 10 s, consider warming the cache at startup or after ingestion (a plan decision, not part of this inspection).
