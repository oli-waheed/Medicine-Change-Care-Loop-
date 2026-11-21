"""Feature 007 (1a): review cases from changes in Fimea's shortage data.

When the active shortage file changes, the previous and current accepted files
are compared by VNR. Each change is matched, package by package, to simulated
records through the active catalogue release (VNR → Pakkaustunnus → record),
with the same rule as release changes: exactly one record per package makes a
case, several are ambiguous, none is no match. Every change gets an outcome;
cases and outcomes are written once per pair of files, so replays add nothing.
The first accepted file is a baseline only.
"""

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ..models import ShortageCaptureRow
from .medicine_shortages import ShortageRecord, parse_shortage_file

COMPARED_COLUMNS = (
    ("valid", "Valid"),
    ("unavailable_from", "UnavailableFrom"),
    ("ending_date", "EndingDate"),
    ("company", "Company"),
)
LICENCE = "CC BY 4.0"
NOTICE = (
    "Dates and status are the company's report to Fimea, shown as published; "
    "the end date is an estimate."
)


@dataclass(frozen=True, slots=True)
class ShortageChange:
    kind: str  # SHORTAGE_STARTED, SHORTAGE_CHANGED, SHORTAGE_ENDED
    vnr: str
    before: ShortageRecord | None
    after: ShortageRecord | None
    changed_columns: tuple[str, ...]


def detect_shortage_changes(
    prior: tuple[ShortageRecord, ...], current: tuple[ShortageRecord, ...]
) -> tuple[ShortageChange, ...]:
    """Started, changed and ended shortages, in the current file's order, then ended ones."""
    old = {record.vnr: record for record in prior}
    new = {record.vnr: record for record in current}
    changes = []
    for record in current:
        before = old.get(record.vnr)
        if before is None:
            changes.append(ShortageChange("SHORTAGE_STARTED", record.vnr, None, record, ()))
            continue
        changed = tuple(
            column
            for attribute, column in COMPARED_COLUMNS
            if getattr(before, attribute) != getattr(record, attribute)
        )
        if changed:
            changes.append(ShortageChange("SHORTAGE_CHANGED", record.vnr, before, record, changed))
    for record in prior:
        if record.vnr not in new:
            changes.append(ShortageChange("SHORTAGE_ENDED", record.vnr, record, None, ()))
    return tuple(changes)


def read_capture(capture: ShortageCaptureRow) -> tuple[ShortageRecord, ...]:
    data = Path(capture.file_path).read_bytes()
    if f"sha256-{hashlib.sha256(data).hexdigest()}" != capture.checksum:
        raise ValueError(f"Stored shortage file {capture.checksum} does not match its checksum.")
    return parse_shortage_file(data)


def _hash(*parts: str) -> str:
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()


def _row(record: ShortageRecord | None) -> dict | None:
    if record is None:
        return None
    return {
        "line": record.line,
        "valid": record.valid,
        "unavailableFrom": record.unavailable_from,
        "endingDate": record.ending_date,
        "notificationDate": record.notification_date,
        "updated": record.updated,
        "company": record.company,
    }


def _time(value: datetime) -> str:
    return (value.replace(tzinfo=UTC) if value.tzinfo is None else value).isoformat()


def _source(capture: ShortageCaptureRow, record: ShortageRecord | None) -> dict:
    return {
        "sourceName": "Fimea shortage data (Shortages.txt)",
        "sourceUrl": capture.source_url,
        "fileName": "Shortages.txt",
        "checksum": capture.checksum.removeprefix("sha256-"),
        "captureReference": capture.checksum,
        "retrievedAt": _time(capture.first_retrieved_at),
        "lineNumber": record.line if record is not None else None,
        "licence": LICENCE,
        "evidenceClass": "VERIFIED",
        "note": (
            "Row as published in this file."
            if record is not None
            else "No row with this VNR in this file."
        ),
    }


def _package(snapshot) -> dict:
    product = snapshot.product

    def value(field):
        return {
            "state": field.state.value,
            "value": field.value,
            "attributes": dict(field.attributes),
        }

    return {
        "pakkaustunnus": snapshot.pakkaustunnus,
        "productName": value(product.kauppanimi),
        "strength": value(product.vahvuus),
        "packageSizeText": value(snapshot.package.pakkauskoko_teksti),
    }


def build_shortage_review(
    *,
    prior_capture: ShortageCaptureRow,
    prior_records: tuple[ShortageRecord, ...],
    current_capture: ShortageCaptureRow,
    current_records: tuple[ShortageRecord, ...],
    baseline,
    packages_by_vnr: dict | None,
    records: tuple,
    now: datetime,
) -> tuple[list[dict], list[dict]]:
    """Return ``(cases, outcomes)`` as storable dicts for one pair of files."""
    records_by_package: dict[str, list] = defaultdict(list)
    for record in records:
        if record.package_identifier:
            records_by_package[record.package_identifier].append(record)
    catalogue = (
        {"releaseId": baseline.release_id, "releaseDate": baseline.capture.source_order_value}
        if baseline is not None
        else None
    )
    cases: list[dict] = []
    outcomes: list[dict] = []
    detected_at = now.isoformat()

    for change in detect_shortage_changes(prior_records, current_records):
        sources = {
            "prior": _source(prior_capture, change.before),
            "current": _source(current_capture, change.after),
        }
        base = {
            "source": "SHORTAGES",
            "changeKind": change.kind,
            "changedFields": list(change.changed_columns),
            "evidenceClass": "VERIFIED",
            "sources": sources,
            "detectedAt": detected_at,
            "vnr": change.vnr,
        }
        pair = (prior_capture.checksum, current_capture.checksum, change.vnr, change.kind)

        def outcome(key, result, reason, note, identifier, granularity, matched=(), case_ids=()):
            outcomes.append(
                {
                    **base,
                    "outcomeId": _hash(*pair, key),
                    "result": result,
                    "reason": reason,
                    "note": note,
                    "medicineIdentifier": identifier,
                    "comparedIdentifier": identifier,
                    "identifierGranularity": granularity,
                    "simulatedRecords": [
                        {
                            "recordId": r.record_id,
                            "personReference": r.person_reference,
                            "medicineDisplay": r.medicine_display,
                        }
                        for r in matched
                    ],
                    "caseIds": list(case_ids),
                }
            )

        if packages_by_vnr is None:
            outcome(
                "",
                "NO_MATCH",
                "NO_CATALOGUE_RELEASE",
                "No catalogue release was available to find the packages with this VNR.",
                change.vnr,
                "vnr",
            )
            continue
        packages = packages_by_vnr.get(change.vnr, ())
        if not packages:
            outcome(
                "",
                "NO_MATCH",
                "NO_CATALOGUE_PACKAGE",
                "No package of the active catalogue release has this VNR.",
                change.vnr,
                "vnr",
            )
            continue
        for snapshot in packages:
            matched = records_by_package.get(snapshot.pakkaustunnus, [])
            if not matched:
                outcome(
                    snapshot.pakkaustunnus,
                    "NO_MATCH",
                    "NO_SIMULATED_RECORD",
                    "No simulated medication record has this Pakkaustunnus, "
                    "so no review case was created.",
                    snapshot.pakkaustunnus,
                    "package",
                )
                continue
            if len(matched) > 1:
                outcome(
                    snapshot.pakkaustunnus,
                    "AMBIGUOUS",
                    "MULTIPLE_SIMULATED_RECORDS",
                    "More than one simulated record has this Pakkaustunnus, "
                    "so no review case was created.",
                    snapshot.pakkaustunnus,
                    "package",
                    matched,
                )
                continue
            (record,) = matched
            key = _hash(*pair, snapshot.pakkaustunnus, record.record_id)
            case_id = f"CASE-{key}"
            created = now.isoformat()
            cases.append(
                {
                    "case_id": case_id,
                    "idempotency_key": key,
                    "created_at": now,
                    "medicine_key": snapshot.pakkaustunnus,
                    "record_id": record.record_id,
                    "change_set_id": _hash(*pair),
                    "change_kind": change.kind,
                    "prior_file_checksum": sources["prior"]["checksum"],
                    "current_file_checksum": sources["current"]["checksum"],
                    "event_id": f"EVENT-{key}",
                    "payload": {
                        "caseId": case_id,
                        "caseType": "SHORTAGE",
                        "createdAt": created,
                        "status": "NEW",
                        "medicineIdentifier": snapshot.pakkaustunnus,
                        "identifierGranularity": "package",
                        "matchedRecord": {
                            "recordId": record.record_id,
                            "personReference": record.person_reference,
                            "medicineDisplay": record.medicine_display,
                        },
                        "shortageChange": {
                            "changeSetId": _hash(*pair),
                            "kind": change.kind,
                            "vnr": change.vnr,
                            "changedColumns": list(change.changed_columns),
                            "before": _row(change.before),
                            "after": _row(change.after),
                            "detectedAt": detected_at,
                            "package": _package(snapshot),
                            "catalogue": catalogue,
                            "notice": NOTICE,
                        },
                        "sources": sources,
                        "evidenceClass": "VERIFIED",
                        "initialStatusEvent": {
                            "eventId": f"EVENT-{key}",
                            "caseId": case_id,
                            "fromStatus": None,
                            "toStatus": "NEW",
                            "occurredAt": created,
                        },
                    },
                }
            )
            outcome(
                snapshot.pakkaustunnus,
                "MATCHED",
                "UNIQUE_EXACT_PACKAGE_MATCH",
                "Exactly one simulated record has this Pakkaustunnus; a review case was created.",
                snapshot.pakkaustunnus,
                "package",
                matched,
                (case_id,),
            )
    return cases, outcomes
