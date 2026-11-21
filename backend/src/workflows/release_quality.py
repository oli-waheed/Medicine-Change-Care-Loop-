"""Feature 010: check stored release pairs that have no quality check yet.

Releases compared before feature 010, or loaded out of date order, have no
stored check. The daily update calls this after its downloads; each pair takes
about 25 s on real releases (both files are read again from their captures).
"""

import logging

from ..services.detect_relevant_changes import detect_relevant_changes
from ..services.ingest_source_release import ProcessingStatus, reload_captured_release
from ..services.pipeline_store import PipelineStore
from ..services.release_quality_checks import build_quality_check, check_id
from .ingestion_to_review import source_order_evidence

logger = logging.getLogger(__name__)


def backfill_quality_checks(store: PipelineStore, *, limit: int = 3) -> int:
    """Check up to ``limit`` of the newest unchecked pairs; returns how many were added."""
    missing = [
        (prior, current)
        for prior, current in store.compared_release_pairs()
        if not store.has_quality_check(check_id(prior.release_id, current.release_id))
    ][-limit:]
    added = 0
    for prior_row, current_row in missing:
        try:
            prior = reload_captured_release(prior_row.capture_directory)
            current = reload_captured_release(current_row.capture_directory)
            if any(
                outcome.processing_status is not ProcessingStatus.VALIDATED
                for outcome in (prior, current)
            ):
                continue
            comparison = detect_relevant_changes(
                prior.snapshots, current.snapshots, order=source_order_evidence(prior, current)
            )
            payload = build_quality_check(
                prior=prior,
                current=current,
                prior_release_id=prior_row.release_id,
                current_release_id=current_row.release_id,
                comparison=comparison,
            )
            added += store.record_quality_check(payload)
        except (OSError, ValueError):
            # A capture that can no longer be read stays unchecked; Source History shows it.
            logger.exception("Quality check of %s failed.", current_row.release_id)
    return added
