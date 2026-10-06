# Quickstart: Validate the Ingestion-to-Case Flow

This guide defines the acceptance run for the prototype. It is not an installation guide: the repository
does not yet contain application code or an established runtime/toolchain. Run the scenarios after the
team selects and documents those prerequisites.

## Prerequisites

- A chosen implementation stack and local test/run instructions.
- A captured Fimea Basic Register release fixture, plus a prior release fixture, with source identity and
  source-provided order information preserved.
- A controlled set of simulated medication records; do not use real patient-identifiable data.
- An agreed list of relevant source fields and the medicine/package matching key and granularity.
- A configured n8n scheduled workflow, or its documented local/manual trigger for acceptance testing.

## Acceptance run

1. Load the prior and current source release fixtures through the same ingestion path used by the
   scheduled workflow.
2. Verify both source snapshots retain release provenance, retrieval time, raw file references, and
   checksums. Confirm retrieval time is not represented as source update chronology.
3. Include one changed relevant field with a unique exact simulated-record identifier match; include one
   change with no match and one with an ambiguous identifier.
4. Run the scheduled/manual workflow once.
5. Verify the unique match creates exactly one review case in `NEW`, and the pharmacist open-case view
   exposes its before/after evidence, source references, simulated record, and evidence classifications.
6. Verify the no-match and ambiguous scenarios create no cases and retain an honest outcome.
7. Run the same release through the workflow again. Verify that the existing case remains traceable and
   no duplicate review case is created for the same change and simulated medication record.
8. Simulate unavailable or malformed source input and verify the run is visibly failed/incomplete and
   no case is created from partial data.
9. Inspect the whole fixture set and view to confirm every patient and medication record is simulated and
   no clinical decision, treatment recommendation, substitution, urgency determination, or automatic
   case closure occurs.

## Expected result

The acceptance set produces one unique `NEW` case for the supported match, zero cases for no-match or
ambiguous-match records, no duplicates on replay, visible failure on invalid ingestion, and complete
source traceability for every stored snapshot, detected change, and case. The pharmacist remains the
decision-maker.

Refer to [data-model.md](data-model.md) for entity and state requirements and
[contracts/ingestion-and-case-view.md](contracts/ingestion-and-case-view.md) for boundary data
requirements.
