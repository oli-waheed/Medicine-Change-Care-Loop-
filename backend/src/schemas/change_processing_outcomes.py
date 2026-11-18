"""Read-view serialization for change processing outcomes (T031)."""

from ..services.change_processing_outcomes import ChangeProcessingOutcome, OutcomeReason
from .open_review_cases import _source

_NOTES = {
    OutcomeReason.UNIQUE_EXACT_PACKAGE_MATCH: (
        "Exactly one simulated medication record has this Pakkaustunnus."
    ),
    OutcomeReason.NO_SIMULATED_RECORD: (
        "No simulated medication record has this Pakkaustunnus, so no review case was created."
    ),
    OutcomeReason.MULTIPLE_SIMULATED_RECORDS: (
        "More than one simulated medication record has this Pakkaustunnus. The match is "
        "ambiguous, so no review case was created."
    ),
}


def change_processing_outcome_payload(outcome: ChangeProcessingOutcome) -> dict:
    match = outcome.match
    change_set = match.change_set
    note = _NOTES[outcome.reason]
    if outcome.reason is OutcomeReason.UNIQUE_EXACT_PACKAGE_MATCH and not outcome.case_ids:
        note += " No review case was created because the change evidence is not verified."
    prior_evidence, current_evidence = match.source_references
    return {
        "outcomeId": outcome.outcome_id,
        "result": match.result.value,
        "reason": outcome.reason.value,
        "note": note,
        "medicineIdentifier": change_set.medicine_key,
        "comparedIdentifier": match.compared_identifier,
        "identifierGranularity": match.identifier_granularity.value.lower(),
        "changeSetId": change_set.change_set_id,
        "changeKind": change_set.kind.value,
        "changedFields": [change.field_name for change in change_set.field_changes],
        "simulatedRecords": [
            {
                "recordId": record.record_id,
                "personReference": record.person_reference,
                "medicineDisplay": record.medicine_display,
            }
            for record in match.simulated_record_references
        ],
        "caseIds": list(outcome.case_ids),
        "evidenceClass": match.evidence_classification.value,
        "sources": {
            "prior": _source(prior_evidence),
            "current": _source(current_evidence),
        },
        "sourceOrder": {
            "prior": change_set.prior_source_order,
            "current": change_set.current_source_order,
            "basis": change_set.source_order_basis,
            "evidenceClass": change_set.change_evidence_class.value,
        },
        "detectedAt": change_set.detected_at.isoformat(),
    }
