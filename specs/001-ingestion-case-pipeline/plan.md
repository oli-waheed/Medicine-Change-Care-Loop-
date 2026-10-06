# Implementation Plan: Medicine Change Ingestion-to-Case Pipeline

**Branch**: `001-ingestion-case-pipeline` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-ingestion-case-pipeline/spec.md`

## Summary

Deliver a small end-to-end prototype slice that imports official Fimea Basic Register releases through a scheduled n8n workflow, retains source snapshots, compares successive releases for relevant catalog-field changes, deterministically matches those changes against simulated medication records, and presents traceable NEW review cases to a pharmacist. Preserve the raw source release and provenance throughout the flow. The Basic Register is updated twice monthly and is catalog-oriented; this plan does not claim to detect leaflet/SPC clinical-content changes or determine clinical significance.

The repository currently contains project guidance and Spec Kit artifacts, but no application code, dependency manifests, backend, frontend, test suite, or established runtime/storage stack. Keep the design and contracts technology-neutral where the team has not made a choice; select the implementation stack as a team before implementation.

## Technical Context

**Language/Version**: Not established; repository currently has no application code. Team selects before implementation.

**Primary Dependencies**: n8n for scheduled orchestration (explicitly requested); no backend or user-interface framework established.

**Storage**: Not established. Must retain immutable raw source releases, normalized snapshots, detected changes, simulated medication records, cases, and case status events.

**Testing**: Automated tests for normalization, release comparison, deterministic matching, case idempotency, and exposed contracts; manual end-to-end validation of ingestion through pharmacist case review. Test framework not established.

**Target Platform**: Prototype environment; production deployment is out of scope.

**Project Type**: End-to-end web prototype with scheduled ingestion, backend processing, persistent evidence, and pharmacist-facing review view; concrete module boundaries remain a team implementation decision.

**Performance Goals**: Process one selected source release and its included records in a single scheduled run without losing records or creating duplicate cases; no high-volume or real-time throughput target is defined.

**Constraints**: Simulated patient and medication data only. Human review is mandatory. No diagnoses, treatment recommendations, substitution selection, urgency decisions, automatic clinically relevant case closure, AI explanations, patient-facing views, communication/follow-up, external clinical systems, or production deployment. Unknown or conflicting source order and ambiguous matches must remain explicit and must not produce verified cases.

**Scale/Scope**: One selected official Fimea Basic Register feed, successive available releases, controlled simulated medication data, and pharmacist-facing open NEW cases. The source is published twice monthly; the prototype may check for releases on a scheduled basis but must not imply that Fimea content changes are available more frequently than the source publishes them.

## Constitution Check

**Pre-research gate: PASS**

- **Evidence-driven decisions**: Preserve raw source material, source release identity, retrieval time, and evidence references; distinguish source facts from assumptions and unknowns.
- **User-centered delivery**: Prioritize the pharmacist's traceable open-case review journey.
- **Shared accountability**: Record ownership and decisions in project artifacts and review changes through the team workflow.
- **Quality before completion**: Validate each vertical slice with automated business-logic/API tests and manual end-to-end testing.
- **Continuous improvement**: Checkpoint source suitability and relevant-field definitions before expanding scope.
- **Human-in-the-loop safety and scope**: Cases remain review items; no clinical decisions or prohibited integrations are introduced.
- **Simulated data and privacy**: Use fictional records in all environments and fixtures.
- **Small vertical slices**: Implement from a source fixture through a visible case before broadening coverage.

**Post-design gate: PASS**. The proposed entities/contracts preserve traceability, uncertainty and human review. No constitution violations or additional subsystems are proposed.

## Research Plan and Decisions

Phase 0 findings and decision rationale are recorded in [research.md](research.md). The selected source is the Fimea Basic Register. Before relying on live data, validate file access, current file layout, release ordering metadata, permitted reuse/automated access, and the exact fields included in the chosen release. If reliable release ordering cannot be established from source evidence, the pipeline must expose the order as unknown and refrain from claiming a verified change.

The Basic Register is a catalog source with package-level release changes; it is not a documented feed of leaflet/SPC clinical text. The team must agree which available catalog fields count as relevant changes before implementation. The feature must not describe catalog differences as clinical risk or medicine advice.

## Design

### Processing Flow

1. n8n checks for a new official Basic Register release on the agreed schedule and captures the raw release bundle without modifying its contents.
2. The ingestion boundary records source identity, any source-supplied release/order information, retrieval time, filenames, and content checksums. Retrieval time is not substituted for missing source update information.
3. The normalizer produces records for fields selected as relevant, retaining each value's source-record reference and evidence classification.
4. The comparison process pairs records for the same medicine/package using an agreed stable identifier, compares successive ordered snapshots, and emits changes only for agreed relevant fields.
5. A deterministic matcher checks each relevant change against simulated medication records at the same identifier granularity. Missing or ambiguous identifiers result in no match and an explicit uncertainty outcome.
6. A matched change creates one NEW review case per unique change and simulated medication record. Reprocessing the same release is idempotent.
7. The pharmacist-facing open-case view reads cases and presents their change, simulated match, source evidence, evidence quality, and current status. No case-closing or clinical-decision action is added in this feature.

### Project Structure

The repository has no existing source-code layout. Proposed logical boundaries below are implementation targets, not established paths or framework commitments.

```text
workflow/
└── n8n/                    # Scheduled release detection and ingestion orchestration
backend/                    # Snapshot, comparison, matching, case, and read-view behavior
frontend/                   # Pharmacist-facing open-case list and evidence view
tests/
├── unit/                   # Normalization, comparison, matching, idempotency
├── contract/               # Ingestion and case-view contract checks
└── integration/            # Fixture-to-case end-to-end flow
specs/001-ingestion-case-pipeline/
├── contracts/
├── data-model.md
├── quickstart.md
└── research.md
```

**Structure Decision**: Use logical workflow, backend, frontend, and test boundaries to make the ingestion-to-review journey testable as small vertical slices. The team must choose concrete languages, frameworks, storage, and directory conventions before code implementation; do not add services or layers without a demonstrated need.

## Complexity Tracking

No constitution violations or added architectural complexity require justification.
