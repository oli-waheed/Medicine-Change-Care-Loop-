# Feature 004: Interactive Medicine Catalogue

**Status:** Approved specification
**Branch:** feature/interactive-medicine-catalogue

## 1. Objective

Provide a searchable, interactive, read-only catalogue of medicine products and packages from the latest validated Fimea Basic Register source release with verified chronology.

Users can inspect product information, package information, active substances, source provenance, and source-recorded differences between two products.

The catalogue is an information-inspection tool, not a clinical decision-support system.

## 2. Scope

### In scope
- Search and filter medicine records.
- Browse product information.
- Inspect package details.
- Explore active substances.
- Compare two products using source fields.
- Inspect source provenance.
- Search and identify records using VNR.
- Prepare the catalogue for future medicine shortage intelligence.
- Add a working Medicine Catalogue navigation item.

### Out of scope
- Source ingestion or upload from the catalogue.
- A second normalization pipeline.
- Changes to medicine-change detection or matching.
- Changes to Open Review Cases.
- Therapeutic equivalence assessments.
- Medicine substitution recommendations.
- Clinical advice or patient-specific decisions.
- Actual shortage monitoring or supply-chain integrations.

## 3. Source data and baseline selection

The catalogue MUST use the existing `PipelineStore.comparison_baseline()` selection rule.

The active catalogue release MUST:
- Be successfully validated.
- Have verified source chronology.
- Use backend-derived `Ajopvm` chronology.
- Be the latest release according to the existing baseline ordering rule.

Releases with missing or conflicting chronology MUST NOT become the active catalogue dataset.

Normalized records MUST be reconstructed using the existing `reload_captured_release()` service.

The catalogue MUST NOT introduce another XML parser or independently normalize Fimea data.

The catalogue MUST NOT persist a duplicate copy of normalized snapshots merely to support browsing.

It MUST reuse the existing `MedicineSnapshot`, `ProductFields`, `PackageFields`, `ActiveSubstanceFields`, `AuthorizationRegistrationFields`, and source provenance structures.

## 4. Medicine identity and relationships

1. VNR MUST be treated as a first-class medicine identity attribute wherever available.
2. VNR MUST be searchable and filterable.
3. VNR MUST be clearly visible in product and package details.
4. The original VNR value and its source provenance MUST be preserved.
5. VNR MUST be available as a future integration key for medicine shortage intelligence and related supply-chain information.
6. `pakkaustunnus` MUST remain the identity of an individual Fimea package record.
7. VNR MUST NOT replace `pakkaustunnus` as the package-record identity.
8. GTIN and NTIN product codes MUST remain distinct from VNR.
9. The system MUST NOT assume a one-to-one relationship between VNR and GTIN/NTIN.
10. Missing VNR values MUST be represented explicitly; the system MUST NOT invent or infer them.
11. Relationships between VNR, product records and package records MUST preserve source evidence.
12. Records MUST NOT be silently merged based on names, strengths or VNR values.

## 5. Functional requirements

### FR-001: Catalogue access
The application MUST provide a working Medicine Catalogue navigation link. The catalogue MUST load information from the backend API.

### FR-002: Catalogue search
Users MUST be able to search using product name, package identifier and VNR.

### FR-003: Catalogue filtering
Users MUST be able to filter by available source fields, including:
- Active substance.
- ATC code.
- Pharmaceutical form.
- Administration route.
- Package availability.
- VNR.

Missing source values MUST remain distinguishable from known values.

### FR-004: Product details
Display available source values for:
- Product name.
- Strength.
- Pharmaceutical form.
- ATC code.
- Administration route.
- Active substances.
- VNR, when available.

### FR-005: Package details
Display available source values for:
- Package identifier.
- VNR, when available.
- Package size and unit.
- Public clarification.
- Availability status.
- Availability dates.
- Authorization and registration information.

### FR-006: Active-substance explorer
Users MUST be able to inspect:
- Substance name.
- CAS number.
- Quantity.
- Quantity unit.
- Undivided strength.

Original source ordering and repeated occurrences MUST be preserved.

### FR-007: Product comparison
Users MUST be able to select two products and inspect their available source fields side by side.

The comparison MUST:
- Display source-recorded values.
- Identify differences.
- Distinguish missing, empty and unavailable values.
- Avoid implying therapeutic equivalence.

It MUST NOT alter the existing T005 medicine-change comparison behavior.

### FR-008: Provenance
Where available, provenance MUST include:
- Source name.
- Source release reference.
- Source release date or chronology evidence.
- Retrieval timestamp.
- Source filename.
- Raw file checksum.
- Source record identifier or locator.
- Relevant source field reference.
- Evidence classification.

### FR-009: No validated baseline
If no validated release with verified chronology exists, the API MUST return an explicit unavailable state.

The frontend MUST display a clear unavailable message. It MUST NOT silently fall back to an unverified release.

### FR-010: Source integrity
Catalogue operations MUST be read-only.

They MUST NOT:
- Trigger ingestion.
- Modify source captures.
- Create review cases.
- Change processing outcomes.
- Modify the comparison baseline.
- Modify simulated medication records.

### FR-011: VNR-based identification
Users MUST be able to search the catalogue using a VNR.

### FR-012: VNR visibility
VNR MUST be prominently displayed wherever a source record provides it.

### FR-013: VNR-based grouping
Where source evidence supports the relationship, users MUST be able to find package records associated with the same VNR without losing individual package identities.

### FR-014: Future shortage integration readiness
The catalogue data model and API MUST expose VNR as an explicit identification attribute suitable for future medicine shortage intelligence.

Actual shortage monitoring, shortage status, predictions and supply-chain integrations remain outside Feature 004.

## 6. Proposed API

Read-only endpoints under `/api/medicine-catalogue`:

- `GET /api/medicine-catalogue` — searchable and filterable catalogue records.
- `GET /api/medicine-catalogue/products/{product_reference}` — product information and associated packages.
- `GET /api/medicine-catalogue/packages/{pakkaustunnus}` — package information.
- `GET /api/medicine-catalogue/active-substances` — searchable active-substance records.
- `GET /api/medicine-catalogue/compare?productA={reference}&productB={reference}` — side-by-side source-field comparison.
- `GET /api/medicine-catalogue/source` — active catalogue release and provenance summary.

Endpoint names and response contracts are proposals subject to technical review before implementation.

The API MUST preserve source evidence semantics and expose VNR explicitly.

## 7. Frontend requirements

The catalogue MUST use the existing responsive application shell.

The interface MUST provide:
1. Catalogue search and filters.
2. Search results.
3. Product details.
4. Package details.
5. Active-substance exploration.
6. Two-product comparison.
7. VNR visibility and identification.
8. Source provenance.

Loading, empty, error and unavailable-baseline states MUST be provided.

## 8. Safety and terminology

The application MUST describe information as source-recorded facts.

It MUST NOT:
- Claim therapeutic equivalence.
- Recommend substitution.
- Recommend starting, stopping or changing medication.
- Classify medicine changes as clinically urgent.
- Generate patient-specific medical advice.
- Present missing source information as a negative clinical finding.

Product comparison is a comparison of source fields only.

## 9. Testing and verification

Automated tests MUST cover:
- Baseline selection and unavailable-baseline behavior.
- Rebuilding snapshots from the selected captured release.
- Exclusion of unverified chronology.
- Catalogue search and filters.
- Product and package relationships.
- VNR search, visibility and grouping.
- VNR missing-value behavior.
- Active-substance ordering and repeated occurrences.
- Missing and empty source values.
- Product comparison without equivalence claims.
- Provenance completeness and traceability.
- API error and empty states.
- Frontend loading, empty, error and unavailable states.
- Responsive navigation and catalogue behavior.

Existing ingestion, comparison, review-case and provenance tests MUST continue to pass.

## 10. Preservation constraints

Feature 004 MUST NOT change:
- Existing source normalization rules.
- Existing package identity rules.
- Existing VNR source handling.
- Source capture and checksum behavior.
- Baseline-selection behavior.
- Medicine-change detection.
- Review-case creation and persistence.
- Open Review Cases functionality.

Changes to these areas require a separately reviewed specification.

## 11. Acceptance criteria

Feature 004 is accepted when:
1. The catalogue displays records from the latest validated release with verified chronology.
2. Records are reconstructed through the existing normalization service.
3. Search and filters operate on source-recorded fields.
4. VNR is searchable, visible and preserved as a first-class identity attribute.
5. Product and package information remain distinguishable.
6. Active-substance records retain source ordering.
7. Two products can be compared without therapeutic-equivalence claims.
8. Source provenance is inspectable.
9. Unverified releases are not presented as the active catalogue.
10. Catalogue operations do not modify ingestion, matching or review-case data.
11. Existing and new automated tests pass.
12. The application remains responsive and the review workspace continues to work.
