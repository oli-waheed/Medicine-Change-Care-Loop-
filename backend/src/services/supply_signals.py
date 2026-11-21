"""Feature 016: supply signals — shortage and register facts side by side.

Everything here is a fact from Fimea's files as published, or simple date
arithmetic on published dates. Nothing is forecast, scored or ranked:

- the rows of the active shortage file for the record's VNRs, with the number of
  days since "unavailable from" and until the estimated end (the company's report);
- earlier listings: runs of consecutive downloads that listed the VNR;
- register facts of the active release: on the market, marketed until,
  authorisation status;
- recorded register changes of those fields (feature 013's package history);
- products with the same active substances whose VNRs the active file lists.
"""

import hashlib
import threading
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..domain.medicine_snapshot import MedicineSnapshot
from ..domain.source_field import SourceField, SourceFieldState
from .medicine_links import LinkIndex, _product_item
from .medicine_shortages import ShortageRecord, parse_shortage_file
from .pipeline_store import PipelineStore, _as_utc

# Package-history fields that say something about supply (feature 013 events).
SUPPLY_FIELDS = (
    "Pakkaus/Kaupanolo/Kaupan",
    "Pakkaus/Kaupanolo/Kauppaantulopaiva",
    "Pakkaus/Kaupanolo/Kaupastapoistumispaiva",
    "Pakkaus/VNR-numero",
)
RELATED_LIMIT = 20

NOTICE = (
    "Facts from Fimea's files as published, side by side. Dates and status in the "
    "shortage file are the company's report; the end date is an estimate. Nothing "
    "here is a forecast, and a medicine not listed is not shown to be available."
)


def _source_value(field: SourceField) -> dict:
    return {"state": field.state.value, "value": field.value, "attributes": dict(field.attributes)}


def _days(start: str, end: date) -> int | None:
    try:
        return (end - date.fromisoformat(start[:10])).days
    except ValueError:
        return None


class StoredShortageFiles:
    """Parsed stored shortage files by checksum, verified once (files are small)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._files: dict[str, dict[str, ShortageRecord] | None] = {}

    def records(self, capture) -> dict[str, ShortageRecord] | None:
        """``{vnr: record}``, or None if the stored file is gone or changed."""
        with self._lock:
            if capture.checksum not in self._files:
                try:
                    data = Path(capture.file_path).read_bytes()
                    if f"sha256-{hashlib.sha256(data).hexdigest()}" != capture.checksum:
                        raise ValueError("checksum")
                    self._files[capture.checksum] = {
                        record.vnr: record for record in parse_shortage_file(data)
                    }
                except (OSError, ValueError):
                    self._files[capture.checksum] = None
            return self._files[capture.checksum]


@dataclass(frozen=True, slots=True)
class _Listing:
    vnr: str
    first_seen: str
    last_seen: str
    downloads: int
    first_record: ShortageRecord
    last_record: ShortageRecord


def _listings(store: PipelineStore, files: StoredShortageFiles, vnrs: list[str]):
    """Runs of consecutive downloads that listed each VNR, oldest first."""
    timeline = store.shortage_timeline()
    readable = [(when, files.records(capture)) for when, capture in timeline]
    unreadable = sum(1 for _, records in readable if records is None)
    runs: list[_Listing] = []
    for vnr in vnrs:
        current: dict | None = None
        for when, records in readable:
            if records is None:
                continue
            record = records.get(vnr)
            if record is not None:
                if current is None:
                    current = {"first": when, "last": when, "n": 0, "a": record, "b": record}
                current["last"], current["b"] = when, record
                current["n"] += 1
            elif current is not None:
                runs.append(_close(vnr, current))
                current = None
        if current is not None:
            runs.append(_close(vnr, current))
    return timeline, runs, unreadable


def _close(vnr: str, run: dict) -> _Listing:
    return _Listing(
        vnr, run["first"].isoformat(), run["last"].isoformat(), run["n"], run["a"], run["b"]
    )


def _register(anchors: tuple[MedicineSnapshot, ...]) -> list[dict]:
    return [
        {
            "pakkaustunnus": snapshot.pakkaustunnus,
            "vnr": _source_value(snapshot.vnr_numero),
            "onMarket": _source_value(snapshot.package.availability.kaupan),
            "marketedFrom": _source_value(snapshot.package.availability.kauppaantulo_paiva),
            "marketedUntil": _source_value(snapshot.package.availability.kaupasta_poistumis_paiva),
            "authorisations": [
                {
                    "branch": authorization.branch.value,
                    "status": _source_value(authorization.tila),
                    "endDate": _source_value(authorization.paattymis_paiva),
                }
                for authorization in snapshot.authorizations
            ],
        }
        for snapshot in anchors
    ]


def _register_changes(store: PipelineStore, anchors) -> list[dict]:
    changes = []
    for snapshot in anchors:
        for pair, event in store.package_history_events(snapshot.pakkaustunnus):
            if event.kind != "FIELDS_CHANGED":
                changes.append(
                    {
                        "pakkaustunnus": snapshot.pakkaustunnus,
                        "priorReleaseDate": pair.prior_release_date,
                        "currentReleaseDate": pair.current_release_date,
                        "kind": event.kind,
                        "field": None,
                        "before": [],
                        "after": [],
                    }
                )
                continue
            for change in event.changes:
                if change["field"] in SUPPLY_FIELDS or "/Tila" in change["field"]:
                    changes.append(
                        {
                            "pakkaustunnus": snapshot.pakkaustunnus,
                            "priorReleaseDate": pair.prior_release_date,
                            "currentReleaseDate": pair.current_release_date,
                            "kind": event.kind,
                            "field": change["field"],
                            "before": change["before"],
                            "after": change["after"],
                        }
                    )
    return changes


def supply_signals(
    *,
    store: PipelineStore,
    files: StoredShortageFiles,
    index: LinkIndex,
    anchors: tuple[MedicineSnapshot, ...],
    active,
    today: date,
) -> dict:
    """Supply facts for one package, or all packages of one product.

    ``active`` is the active shortage file (``ShortageFile``) or None.
    """
    vnrs = sorted(
        {
            a.vnr_numero.value
            for a in anchors
            if a.vnr_numero.state is SourceFieldState.VALUE and a.vnr_numero.value
        }
    )
    if not vnrs:
        status = "NO_VNR"
    elif active is None:
        status = "NO_FILE"
    else:
        status = "LISTED" if any(record.vnr in vnrs for record in active.records) else "NOT_LISTED"
    current = []
    if active is not None:
        for record in active.records:
            if record.vnr in vnrs:
                since = _days(record.unavailable_from, today)
                until = _days(record.ending_date, today)
                current.append(
                    {
                        "line": record.line,
                        "vnr": record.vnr,
                        "valid": record.valid,
                        "unavailableFrom": record.unavailable_from,
                        "endingDate": record.ending_date,
                        "notificationDate": record.notification_date,
                        "updated": record.updated,
                        "company": record.company,
                        "daysSinceUnavailableFrom": since,
                        "daysUntilEstimatedEnd": None if until is None else -until,
                    }
                )

    timeline, runs, unreadable = _listings(store, files, vnrs) if vnrs else ([], [], 0)
    active_checksum = active.capture.checksum if active is not None else None
    last_download = timeline[-1][0].isoformat() if timeline else None
    listings = [
        {
            "vnr": run.vnr,
            "firstSeen": run.first_seen,
            "lastSeen": run.last_seen,
            "downloads": run.downloads,
            "listedNow": run.last_seen == last_download and status == "LISTED",
            "unavailableFromFirst": run.first_record.unavailable_from,
            "endingDateLast": run.last_record.ending_date,
            "listedDays": _days(run.first_seen, date.fromisoformat(run.last_seen[:10])),
        }
        for run in runs
    ]

    # Products with the same active substances whose VNRs are listed now.
    references = {a.product_reference.value or "" for a in anchors}
    codes = set().union(*(index.codes_by_product.get(ref, frozenset()) for ref in references))
    same = sorted(
        ref
        for ref, ref_codes in index.codes_by_product.items()
        if codes and ref_codes == frozenset(codes) and ref not in references
    )
    listed_vnrs = {record.vnr for record in active.records} if active is not None else set()
    related = []
    for ref in same:
        product_vnrs = sorted(
            {
                p.vnr_numero.value
                for p in index.packages_by_product[ref]
                if p.vnr_numero.value in listed_vnrs
            }
        )
        if product_vnrs:
            related.append({**_product_item(index, ref), "listedVnrs": product_vnrs})

    return {
        "asOf": today.isoformat(),
        "notice": NOTICE,
        "vnrs": vnrs,
        "status": status,
        "shortageFile": (
            {
                "captureReference": active_checksum,
                "lastRetrievedAt": _as_utc(active.capture.last_retrieved_at).isoformat(),
            }
            if active is not None
            else None
        ),
        "current": current,
        "listings": listings,
        "downloadsChecked": len(timeline),
        "unreadableDownloads": unreadable,
        "register": _register(anchors),
        "registerChanges": _register_changes(store, anchors),
        "related": {
            "sameSubstanceProducts": len(same),
            "listedNow": len(related),
            "items": related[:RELATED_LIMIT],
            "available": active is not None and bool(codes),
        },
    }
