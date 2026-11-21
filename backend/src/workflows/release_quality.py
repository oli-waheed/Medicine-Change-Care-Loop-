"""Features 010 and 013: complete the records of stored release pairs.

Releases compared before feature 010 or 013, or loaded out of date order, have
no stored quality check or package history. The daily update calls this after
its downloads; each pair takes about 25–40 s on real releases (both files are
read again from their captures, once for both records).
"""

import logging

from ..services.detect_relevant_changes import detect_relevant_changes
from ..services.ingest_source_release import ProcessingStatus, reload_captured_release
from ..services.package_history import build_package_history, pair_id
from ..services.pipeline_store import PipelineStore
from ..services.release_quality_checks import build_quality_check, check_id
from .ingestion_to_review import source_order_evidence

logger = logging.getLogger(__name__)


def backfill_release_pairs(store: PipelineStore, *, limit: int = 3) -> dict[str, int]:
    """Complete up to ``limit`` of the newest incomplete pairs.

    Returns how many quality checks and package histories were added.
    """
    incomplete = []
    for prior, current in store.compared_release_pairs():
        needs_check = not store.has_quality_check(check_id(prior.release_id, current.release_id))
        needs_history = not store.has_package_history(pair_id(prior.release_id, current.release_id))
        if needs_check or needs_history:
            incomplete.append((prior, current, needs_check, needs_history))
    added = {"qualityChecks": 0, "packageHistories": 0}
    for prior_row, current_row, needs_check, needs_history in incomplete[-limit:]:
        try:
            prior = reload_captured_release(prior_row.capture_directory)
            current = reload_captured_release(current_row.capture_directory)
            if any(
                outcome.processing_status is not ProcessingStatus.VALIDATED
                for outcome in (prior, current)
            ):
                continue
            pair = {
                "prior": prior,
                "current": current,
                "prior_release_id": prior_row.release_id,
                "current_release_id": current_row.release_id,
                "comparison": detect_relevant_changes(
                    prior.snapshots,
                    current.snapshots,
                    order=source_order_evidence(prior, current),
                ),
            }
            if needs_check:
                added["qualityChecks"] += store.record_quality_check(build_quality_check(**pair))
            if needs_history:
                added["packageHistories"] += store.record_package_history(
                    build_package_history(**pair)
                )
        except (OSError, ValueError):
            # A capture that can no longer be read stays incomplete; Source History shows it.
            logger.exception("Release pair %s could not be completed.", current_row.release_id)
    return added


def backfill_quality_checks(store: PipelineStore, *, limit: int = 3) -> int:
    """Feature 010 name kept for callers: the number of quality checks added."""
    return backfill_release_pairs(store, limit=limit)["qualityChecks"]
