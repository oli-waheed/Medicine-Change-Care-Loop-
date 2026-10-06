# Research: Medicine Change Ingestion-to-Case Pipeline

**Date**: 2026-10-06

## Fimea source selection

**Decision**: Use Fimea's Basic Register for the prototype's initial scheduled source snapshots.

**Rationale**: Fimea describes the Basic Register as a source for medicinal product catalog information, supplied as multiple ASCII files and updated twice monthly. Its release-to-release package-level change markings are a better fit for scheduled bulk snapshot comparison than scraping an interactive search page.

**Alternatives considered**:

- **FimeaWeb**: Provides search and access to product leaflets and summaries of product characteristics (SPCs), but it is an interactive service and no documented public API or stable automated retrieval contract was found. Dates shown in document titles are document revision dates, not verified record synchronization timestamps. Treat as a possible future/manual source, not this feature's ingestion feed.
- **Undocumented FimeaWeb requests**: Rejected because relying on private implementation details is brittle and source terms, rate limits, and automated reuse permission need confirmation.

**Evidence**:

- Fimea, [Basic register for medicinal products](https://fimea.fi/en/databases_and_registers/basic-register): official description of register contents, ASCII files, twice-monthly updates, and release changes.
- Fimea, [FimeaWeb](https://fimea.fi/en/databases_and_registers/fimeaweb): official description of searchable medicine and product information.
- Fimea, [Lääkehaku information](https://fimea.fi/laakehaut_ja_luettelot/laakehaku): Fimea's caveat that online information may contain errors and is not guaranteed complete, exact, or current.

## Source identity and ordering

**Decision**: Retain each raw release bundle and its file names/checksums, source identity, source-provided release/order metadata where available, and retrieval time. Use source release metadata to establish chronology; retrieval time records when the prototype fetched the files and is not evidence of when Fimea changed a record.

**Rationale**: The reviewed public description confirms a twice-monthly release cadence and release comparisons but does not document a per-record last-modified timestamp or full file schema. Honest provenance must preserve the distinction between source chronology and local retrieval time.

**Alternatives considered**:

- **Use retrieval time as the medicine update date**: Rejected because it would falsely imply source update chronology.
- **Assume an undocumented stable record identifier or API**: Rejected because no public commitment to such an interface was found.

**Validation required before live ingestion**: Verify direct availability and reuse/automation terms; obtain and inspect the current file layout; identify source-provided release identity/order fields; confirm stable product/package identifiers; confirm which fields can support this feature's relevant-change definition. If order cannot be established, keep chronology unknown and do not create verified changes.

## Change and matching semantics

**Decision**: Compare only explicitly selected fields present in the Basic Register, and use deterministic exact identifier matching at the same product/package granularity. Do not turn an identifier mismatch, missing identifier, or multiple plausible matches into a case.

**Rationale**: Exact deterministic matching is auditable and avoids implying a clinical inference. Fimea identifies MA-number at authorization level and Nordic article number at package level; these are distinct granularities and must not be conflated.

**Alternatives considered**:

- **Fuzzy or AI-based matching**: Excluded from this feature; unclear matches must remain unmatched for human awareness rather than autonomously creating a case.
- **Treat all source-file differences as clinically relevant**: Rejected because catalog changes are not equivalent to clinical significance. Relevant fields require team/stakeholder confirmation before implementation.

**Open prerequisite**: The team must select the exact included Basic Register files, stable key and granularity, and relevant fields. This is a domain configuration decision; this plan deliberately does not invent clinical relevance criteria.

## Architecture and workflow boundaries

**Decision**: Model the workflow as source acquisition/orchestration, evidence-preserving snapshot and comparison, deterministic matching/case creation, and a pharmacist-facing read-only open-case view. Use n8n for the scheduled orchestration because the feature request explicitly specifies it.

**Rationale**: This structure follows the required end-to-end vertical slice while maintaining clear evidence boundaries and avoiding extra clinical workflow or deployment scope.

**Alternatives considered**:

- **Separate infrastructure services per processing stage**: Rejected for the prototype absent demonstrated scale or isolation needs.
- **Autonomous case status or clinical decisioning**: Prohibited by the project constitution.

**Technology constraint**: No application code, dependency manifest, storage choice, API framework, UI framework, or test framework exists in the repository. The team must select those before implementation. The design contracts remain transport-neutral and no technology choice is presented as an existing project fact.
