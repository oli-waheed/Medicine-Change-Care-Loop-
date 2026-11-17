"""Read-view serialization for one review case and its package change set."""

from ..domain.detected_change import PackageChangeKind
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


def _last_known_fields(snapshot):
    # Imported lazily: services depend on schemas through the store.
    from ..services.detect_relevant_changes import project_snapshot_fields

    return [
        {"field": path, "values": [_field(v) for v in values]}
        for path, values in sorted(project_snapshot_fields(snapshot).items())
    ]


def open_review_case_payload(case: ReviewCase):
    change_set = case.change_set
    removed = change_set.kind is PackageChangeKind.NO_LONGER_PRESENT
    return {
        "caseId": case.case_id,
        "createdAt": case.created_at.isoformat(),
        "status": case.status.value,
        "medicineIdentifier": change_set.medicine_key,
        "identifierGranularity": "package",
        "matchedRecord": {
            "recordId": case.medication_record.record_id,
            "personReference": case.medication_record.person_reference,
            "medicineDisplay": case.medication_record.medicine_display,
        },
        "changeSet": {
            "changeSetId": change_set.change_set_id,
            "kind": change_set.kind.value,
            "detectedAt": change_set.detected_at.isoformat(),
            "changes": [
                {
                    "changeId": change.change_id,
                    "field": change.field_name,
                    "before": [_field(v) for v in change.prior_value],
                    "after": [_field(v) for v in change.current_value],
                }
                for change in change_set.field_changes
            ],
            "lastKnownFields": (
                _last_known_fields(change_set.prior_snapshot) if removed else None
            ),
        },
        "sources": {
            "prior": _source(change_set.prior_evidence),
            "current": _source(change_set.current_evidence),
        },
        "sourceOrder": {
            "prior": change_set.prior_source_order,
            "current": change_set.current_source_order,
            "basis": change_set.source_order_basis,
            "evidenceClass": change_set.change_evidence_class.value,
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
