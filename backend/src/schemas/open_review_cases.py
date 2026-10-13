"""Read-view serialization contract, ready for the T016 API; no endpoint yet."""

from ..domain.review_case import ReviewCase
from ..domain.source_field import SourceField


def _field(value: SourceField):
    return {"state": value.state.value, "value": value.value, "attributes": dict(value.attributes)}


def _source(evidence):
    release = evidence.source_release
    return {
        "sourceName": release.provenance.source_name,
        "releaseDate": _field(release.ajopvm),
        "releaseReference": _field(release.aineistoera),
        "fileName": release.provenance.raw_file_name,
        "checksum": release.provenance.raw_file_checksum,
        "recordIdentifier": evidence.source_record_identifier,
        "recordLocator": evidence.source_record_locator,
        "fieldReference": evidence.field_reference,
        "evidenceClass": evidence.classification.value,
        "note": evidence.note,
        "retrievedAt": None,
    }


def open_review_case_payload(case: ReviewCase):
    change = case.change
    return {
        "caseId": case.case_id,
        "createdAt": case.created_at.isoformat(),
        "status": case.status.value,
        "medicineIdentifier": change.medicine_key,
        "identifierGranularity": "package",
        "matchedRecord": {
            "recordId": case.medication_record.record_id,
            "personReference": case.medication_record.person_reference,
            "medicineDisplay": case.medication_record.medicine_display,
        },
        "change": {
            "changeId": change.change_id,
            "field": change.field_name,
            "before": [_field(v) for v in change.prior_value],
            "after": [_field(v) for v in change.current_value],
            "detectedAt": change.detected_at.isoformat(),
        },
        "sources": {
            "prior": _source(change.prior_evidence),
            "current": _source(change.current_evidence),
        },
        "sourceOrder": {
            "prior": change.prior_source_order,
            "current": change.current_source_order,
            "basis": change.source_order_basis,
            "evidenceClass": change.change_evidence_class.value,
        },
        "evidenceClass": case.evidence_class.value,
        "initialStatusEvent": {
            "eventId": case.initial_event.event_id,
            "caseId": case.case_id,
            "fromStatus": None,
            "toStatus": "NEW",
            "occurredAt": case.initial_event.occurred_at.isoformat(),
        },
    }
