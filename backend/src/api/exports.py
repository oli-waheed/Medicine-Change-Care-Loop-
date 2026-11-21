"""Feature 011: CSV exports of review cases and their review history.

Read-only. Files use semicolons and a UTF-8 byte-order mark, so Excel with
Finnish settings opens them in columns (like Fimea's own Shortages.txt).
A text that starts with = + - @ or a tab is prefixed with an apostrophe, so a
spreadsheet shows it as text and never runs it as a formula.
"""

import csv
import io
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import Response

from ..schemas.open_review_cases import with_evidence_availability

router = APIRouter(prefix="/api/exports", tags=["exports"])

_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")
_KIND_LABELS = {
    "FIELDS_CHANGED": "Updated package",
    "NO_LONGER_PRESENT": "No longer in the register",
    "SHORTAGE_STARTED": "Shortage started",
    "SHORTAGE_CHANGED": "Shortage changed",
    "SHORTAGE_ENDED": "Shortage ended",
}
_STATUS_LABELS = {
    "NEW": "New",
    "IN_PROGRESS": "In progress",
    "REVIEWED_NO_ACTION": "Reviewed – no action needed",
    "REVIEWED_FOLLOW_UP": "Reviewed – follow-up needed",
}
_CLEANUP_LABELS = {
    "FORMATTING_ONLY": "Spacing or letter case only",
    "ACTIVE_SUBSTANCE_ONLY": "Active-substance fields only",
}

CASE_COLUMNS = [
    "Case ID",
    "Case type",
    "Status",
    "Package ID (Pakkaustunnus)",
    "Simulated record",
    "Simulated person",
    "Medicine (record)",
    "Change",
    "Changed fields",
    "Clean-up label",
    "Prior source",
    "Current source",
    "Source evidence",
    "Case created (UTC)",
    "Last review step (UTC)",
    "Last reviewer",
    "Last note",
    "Review steps",
]
HISTORY_COLUMNS = [
    "Case ID",
    "Package ID (Pakkaustunnus)",
    "Medicine (record)",
    "Step time (UTC)",
    "From status",
    "To status",
    "Reviewer",
    "Note",
]


def _cell(value) -> str:
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(_FORMULA_START) else text


def _csv(columns: list[str], rows: list[list]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(columns)
    writer.writerows([_cell(value) for value in row] for row in rows)
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def _download(content: bytes, name: str) -> Response:
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    return Response(
        content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{name}-{stamp}.csv"'},
    )


def _source(case: dict, side: str) -> str:
    source = case["sources"][side]
    if case["caseType"] == "SHORTAGE":
        return f"Shortages.txt downloaded {source['retrievedAt']}, line {source['lineNumber']}"
    date = source["releaseDate"].get("value")
    return f"Basic Register Ajopvm {date}" if date else "Basic Register, date not recorded"


def _change(case: dict) -> tuple[str, str, str]:
    """(change, changed fields, clean-up label) in words."""
    if case["caseType"] == "SHORTAGE":
        change = case["shortageChange"]
        return (
            f"{_KIND_LABELS.get(change['kind'], change['kind'])} (VNR {change['vnr']})",
            ", ".join(change["changedColumns"]),
            "",
        )
    change_set = case["changeSet"]
    return (
        _KIND_LABELS.get(change_set["kind"], change_set["kind"]),
        ", ".join(change["field"] for change in change_set["changes"]),
        _CLEANUP_LABELS.get(change_set.get("cleanupLabel") or "", ""),
    )


def _cases(request: Request) -> list[dict]:
    store = request.app.state.store
    available = store.available_file_checksums()
    return [
        with_evidence_availability(case, available)
        for case in store.case_payloads(include_reviewed=True)
    ]


@router.get("/review-cases.csv")
def export_review_cases(request: Request) -> Response:
    rows = []
    for case in _cases(request):
        history = case.get("statusHistory") or []
        reviews = [event for event in history if event["fromStatus"] is not None]
        last = reviews[-1] if reviews else None
        change, fields, label = _change(case)
        record = case["matchedRecord"]
        rows.append(
            [
                case["caseId"],
                "Shortage" if case["caseType"] == "SHORTAGE" else "Release",
                _STATUS_LABELS.get(case["status"], case["status"]),
                case["medicineIdentifier"],
                record["recordId"],
                record["personReference"],
                record["medicineDisplay"],
                change,
                fields,
                label,
                _source(case, "prior"),
                _source(case, "current"),
                "Available" if case["evidenceAvailability"] == "AVAILABLE" else "Unavailable",
                case["createdAt"],
                last["occurredAt"] if last else "",
                last["reviewerInitials"] if last else "",
                last["note"] if last else "",
                len(reviews),
            ]
        )
    return _download(_csv(CASE_COLUMNS, rows), "review-cases")


@router.get("/review-history.csv")
def export_review_history(request: Request) -> Response:
    rows = []
    for case in _cases(request):
        for event in case.get("statusHistory") or []:
            rows.append(
                [
                    case["caseId"],
                    case["medicineIdentifier"],
                    case["matchedRecord"]["medicineDisplay"],
                    event["occurredAt"],
                    _STATUS_LABELS.get(event["fromStatus"], "") if event["fromStatus"] else "",
                    _STATUS_LABELS.get(event["toStatus"], event["toStatus"]),
                    event["reviewerInitials"] or ("System" if event["fromStatus"] is None else ""),
                    event["note"],
                ]
            )
    rows.sort(key=lambda row: (row[3], row[0]))
    return _download(_csv(HISTORY_COLUMNS, rows), "review-history")
