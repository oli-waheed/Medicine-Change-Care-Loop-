# Feature 004: Implementation Plan

## 1. Overview

Implement the Interactive Medicine Catalogue as a read-only feature using the existing validated Fimea source-release and normalization architecture.

The implementation must follow the approved `spec.md`. It must not introduce a second ingestion pipeline or duplicate normalized medicine records.

## 2. Architecture

### 2.1 Data source

- Use `PipelineStore.comparison_baseline()` to select the latest validated source release with verified chronology.
- Use `reload_captured_release()` to reconstruct normalized medicine snapshots from the immutable captured source files.
- Exclude releases with missing or conflicting source chronology according to the existing baseline-selection rule.
- Do not modify the existing ingestion or comparison pipeline.

### 2.2 Backend service

Create a dedicated medicine catalogue service.

Responsibilities:
- Obtain the selected validated baseline.
- Reconstruct medicine snapshots through the existing source-release loader.
- Provide catalogue search and filtering.
- Resolve product and package details.
- Explore active substances.
- Compare two products using the approved source fields.
- Preserve source provenance and missing-value information.
- Expose VNR separately from package-record identity.

Do not create a new normalized database table unless a separate approved technical decision establishes that it is necessary.

### 2.3 Medicine identity

- `pakkaustunnus` remains the Fimea package-record identity.
- VNR remains a separate medicine/article identity.
- Do not assume VNR, GTIN, and NTIN are interchangeable.
- Do not infer missing VNR values.
- Do not merge records solely because names, strengths, or VNR values match.
- Group package records by VNR only where the source data supports that relationship.

### 2.4 API

Implement the approved read-only endpoints:

- `GET /api/medicine-catalogue`
- `GET /api/medicine-catalogue/products/{product_reference}`
- `GET /api/medicine-catalogue/packages/{pakkaustunnus}`
- `GET /api/medicine-catalogue/active-substances`
- `GET /api/medicine-catalogue/compare`
- `GET /api/medicine-catalogue/source`

Use response schemas that preserve source values, provenance, and explicit missing values.

### 2.5 Frontend

Add a Medicine Catalogue navigation entry and a working catalogue page.

The interface should support:
- Medicine search.
- Catalogue filters.
- Product details.
- Package details.
- Active-substance exploration.
- Comparison of two products.
- VNR visibility and search.
- Source-release and provenance information.

Follow the existing React, TypeScript, Tailwind, and application-shell conventions.

### 2.6 Performance

Inspect the size and loading cost of captured source releases before selecting a caching strategy.

If caching is needed, use a bounded, clearly invalidated cache keyed by the selected source-release identity. Do not introduce persistent duplicate medicine records without approval.

### 2.7 Safety

The catalogue is an information-inspection tool.

It must not:
- Recommend medicines or substitutions.
- Determine therapeutic equivalence.
- Make clinical decisions.
- Assign clinical urgency.
- Trigger automatic clinical actions.

### 2.8 Testing

Add backend tests for:
- Validated baseline selection.
- Missing or unavailable baseline.
- Catalogue search and filters.
- Product and package lookup.
- Active-substance exploration.
- VNR visibility and missing VNR.
- Package identity and VNR relationships.
- Provenance.
- Product comparison.
- Source integrity.

Add frontend tests for the catalogue navigation, search, filters, details, and comparison.

Run the existing backend and frontend test suites, TypeScript checks, and production build.

## 3. Implementation order

1. Inspect existing schemas, services, API conventions, and frontend routing.
2. Confirm the API response contracts.
3. Implement backend catalogue service and schemas.
4. Implement read-only API endpoints.
5. Add and run backend tests.
6. Implement frontend catalogue navigation and page.
7. Add and run frontend tests.
8. Run full regression checks.
9. Review the final Git diff and report results.

## 4. Constraints

- Follow `spec.md`.
- Preserve existing features and comparison rules.
- Do not modify unrelated code.
- Do not commit or push without explicit user approval.
