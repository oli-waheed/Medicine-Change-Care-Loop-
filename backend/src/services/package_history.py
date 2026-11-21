"""Feature 013: each package's history across compared releases.

For every compared release pair the ingestion records, per package: fields
changed (with the values before and after, as published), no longer present,
or newly present. The catalogue shows these as a package timeline. Stored once
per pair; values are never rewritten.
"""

import hashlib
from dataclasses import dataclass

from ..domain.detected_change import PackageChangeKind
from .detect_relevant_changes import ComparisonResult
from .ingest_source_release import IngestionOutcome

NEWLY_PRESENT = "NEWLY_PRESENT"


@dataclass(frozen=True, slots=True)
class PackageHistory:
    pair: dict
    events: tuple[dict, ...]


def pair_id(prior_release_id: str, current_release_id: str) -> str:
    key = f"{prior_release_id}|{current_release_id}".encode()
    return "PH-" + hashlib.sha256(key).hexdigest()[:40]


def _event_id(pair: str, pakkaustunnus: str, kind: str) -> str:
    key = f"{pair}|{pakkaustunnus}|{kind}".encode()
    return "PE-" + hashlib.sha256(key).hexdigest()[:40]


def _plain(values) -> list[dict]:
    return [
        {"state": v.state.value, "value": v.value, "attributes": dict(v.attributes)} for v in values
    ]


def build_package_history(
    *,
    prior: IngestionOutcome,
    current: IngestionOutcome,
    prior_release_id: str,
    current_release_id: str,
    comparison: ComparisonResult,
) -> PackageHistory:
    pid = pair_id(prior_release_id, current_release_id)
    events = []
    for change_set in comparison.change_sets:
        kind = change_set.kind.value
        changes = (
            [
                {
                    "field": change.field_name,
                    "before": _plain(change.prior_value),
                    "after": _plain(change.current_value),
                }
                for change in change_set.field_changes
            ]
            if change_set.kind is PackageChangeKind.FIELDS_CHANGED
            else []
        )
        events.append(
            {
                "eventId": _event_id(pid, change_set.medicine_key, kind),
                "pakkaustunnus": change_set.medicine_key,
                "kind": kind,
                "changes": changes,
            }
        )
    prior_ids = {s.pakkaustunnus for s in prior.snapshots}
    for key in sorted({s.pakkaustunnus for s in current.snapshots} - prior_ids):
        events.append(
            {
                "eventId": _event_id(pid, key, NEWLY_PRESENT),
                "pakkaustunnus": key,
                "kind": NEWLY_PRESENT,
                "changes": [],
            }
        )
    pair = {
        "pairId": pid,
        "priorReleaseId": prior_release_id,
        "currentReleaseId": current_release_id,
        "priorReleaseDate": prior.source_order.value,
        "currentReleaseDate": current.source_order.value,
    }
    return PackageHistory(pair, tuple(events))
