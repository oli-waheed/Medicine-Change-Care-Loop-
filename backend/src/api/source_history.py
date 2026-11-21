"""Feature 010: Source History — every stored source file and the release checks.

Read-only. It lists what the app has stored and checked; it never downloads,
changes or deletes anything (contracts/source-history-api.md).
"""

from pathlib import Path

from fastapi import APIRouter, Request

from ..services.pipeline_store import PipelineStore, _as_utc
from ..services.release_quality_checks import CHECK_VERSION, check_id

router = APIRouter(prefix="/api/source-history", tags=["source-history"])


def _time(value) -> str | None:
    return _as_utc(value).isoformat() if value is not None else None


def _size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def _basic_register(store: PipelineStore) -> list[dict]:
    baseline = store.comparison_baseline()
    rows = store.captures()
    # Newest release date first; releases without a verified date last.
    rows.sort(
        key=lambda row: (row.source_order_key is not None, row.source_order_key or 0, row.sequence),
        reverse=True,
    )
    result = []
    for row in rows:
        files = store.capture_files(row)
        retrievals = [_as_utc(row.retrieved_at)] + [
            _as_utc(item.retrieved_at) for item in store.retrievals(row.release_id)
        ]
        checksum, path = files[0] if files else (None, None)
        result.append(
            {
                "releaseId": row.release_id,
                "releaseDate": row.source_order_value,
                "dateEvidence": row.source_order_evidence_class,
                "processingStatus": row.processing_status,
                "failureDetail": row.failure_detail,
                "fileName": path.name if path is not None else None,
                "checksum": checksum,
                "sizeBytes": _size(path) if path is not None else None,
                "evidenceAvailable": bool(files) and all(p.is_file() for _, p in files),
                "firstRetrievedAt": min(retrievals).isoformat(),
                "lastRetrievedAt": max(retrievals).isoformat(),
                "retrievalCount": len(retrievals),
                "isCatalogueRelease": baseline is not None
                and baseline.release_id == row.release_id,
            }
        )
    return result


def _shortage_files(store: PipelineStore) -> list[dict]:
    active = store.active_shortage_capture()
    return [
        {
            "checksum": row.checksum,
            "processingStatus": row.processing_status,
            "failureDetail": row.failure_detail,
            "recordCount": row.record_count,
            "sizeBytes": row.size_bytes,
            "evidenceAvailable": Path(row.file_path).is_file(),
            "firstRetrievedAt": _time(row.first_retrieved_at),
            "lastRetrievedAt": _time(row.last_retrieved_at),
            "retrievalCount": store.shortage_retrieval_count(row.sequence),
            "isActive": active is not None and active.sequence == row.sequence,
        }
        for row in store.shortage_captures()
    ]


@router.get("")
def get_source_history(request: Request) -> dict:
    store: PipelineStore = request.app.state.store
    # Feature 014: a check made by an older version is marked; the daily update
    # makes it again with the current checks.
    checks = [
        {**check, "upToDate": check.get("version", 1) >= CHECK_VERSION}
        for check in store.quality_check_payloads()
    ]
    checked = {item["checkId"] for item in checks}
    unchecked = [
        {
            "priorReleaseDate": prior.source_order_value,
            "currentReleaseDate": current.source_order_value,
        }
        for prior, current in reversed(store.compared_release_pairs())
        if check_id(prior.release_id, current.release_id) not in checked
    ]
    return {
        "basicRegister": _basic_register(store),
        "qualityChecks": checks,
        "uncheckedPairs": unchecked,
        "shortageFiles": _shortage_files(store),
    }
