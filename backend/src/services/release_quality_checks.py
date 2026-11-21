"""Feature 010: automatic data-quality checks of each compared release pair.

When a newer Basic Register release is compared with the previous one, the
pair is checked: release order, package identity, how much changed, and how
much of it looks like source clean-up. A check only reports; it never blocks a
release, hides a change or touches a case. ``ATTENTION`` means "a person may
want to look at this pair", nothing more.

The limits are deliberately simple and kept here so the team can tune them.
On the real releases of 2026-10-06 and 2026-11-21: 99.99 % of package IDs
stayed, 0.01 % were removed and 1.4 % changed.
"""

import hashlib
from collections import Counter
from datetime import UTC, datetime

from ..domain.detected_change import PackageChangeKind
from ..domain.source_field import SourceFieldState
from .detect_relevant_changes import ComparisonResult
from .ingest_source_release import IngestionOutcome
from .source_cleanup_labels import CleanupLabel, cleanup_label

# A pair needs a person's attention when fewer IDs stay, or more change, than this.
MIN_PACKAGE_IDS_KEPT = 0.99
MAX_PACKAGES_REMOVED = 0.01
MAX_PACKAGES_CHANGED = 0.10

VNR_FIELD = "Pakkaus/VNR-numero"


def check_id(prior_release_id: str, current_release_id: str) -> str:
    key = f"{prior_release_id}|{current_release_id}".encode()
    return "QC-" + hashlib.sha256(key).hexdigest()[:40]


def _plain(values) -> list[dict]:
    return [
        {"state": v.state.value, "value": v.value, "attributes": dict(v.attributes)} for v in values
    ]


def _percent(part: int, whole: int) -> str:
    return f"{100 * part / whole:.2f} %" if whole else "–"


def build_quality_check(
    *,
    prior: IngestionOutcome,
    current: IngestionOutcome,
    prior_release_id: str,
    current_release_id: str,
    comparison: ComparisonResult,
    checked_at: datetime | None = None,
) -> dict:
    """The stored check of one compared pair (``contracts/source-history-api.md``)."""
    prior_ids = {s.pakkaustunnus for s in prior.snapshots}
    current_ids = {s.pakkaustunnus for s in current.snapshots}
    in_both = len(prior_ids & current_ids)
    changed = removed = 0
    labels: Counter[str] = Counter()
    vnr: Counter[str] = Counter()
    for change_set in comparison.change_sets:
        if change_set.kind is PackageChangeKind.NO_LONGER_PRESENT:
            removed += 1
            continue
        changed += 1
        changes = [
            {
                "field": c.field_name,
                "before": _plain(c.prior_value),
                "after": _plain(c.current_value),
            }
            for c in change_set.field_changes
        ]
        label = cleanup_label(changes)
        labels[label.value if label else "NONE"] += 1
        for c in change_set.field_changes:
            if c.field_name == VNR_FIELD:
                had = c.prior_value[0].state is SourceFieldState.VALUE
                has = c.current_value[0].state is SourceFieldState.VALUE
                vnr["gained" if has and not had else "lost" if had and not has else "changed"] += 1
    vnr_owners = Counter(s.vnr_numero.value for s in current.snapshots if s.vnr_numero.value)
    shared_vnrs = sum(1 for count in vnr_owners.values() if count > 1)
    cleanups = labels[CleanupLabel.FORMATTING_ONLY] + labels[CleanupLabel.ACTIVE_SUBSTANCE_ONLY]
    prior_date = prior.source_order.value
    current_date = current.source_order.value

    def status(ok: bool) -> str:
        return "PASSED" if ok else "ATTENTION"

    checks = [
        {
            "id": "RELEASE_ORDER",
            "label": "Release order",
            "status": status(bool(prior_date and current_date and prior_date < current_date)),
            "detail": f"Ajopvm {prior_date} → {current_date}, read from each file.",
        },
        {
            "id": "UNIQUE_PACKAGE_IDS",
            "label": "Package IDs unique within each release",
            "status": "PASSED",
            "detail": "No Pakkaustunnus repeats; a repeat would have rejected the release.",
        },
        {
            "id": "PACKAGE_IDS_KEPT",
            "label": "Package IDs kept",
            "status": status(bool(prior_ids) and in_both / len(prior_ids) >= MIN_PACKAGE_IDS_KEPT),
            "detail": (
                f"{in_both:,} of {len(prior_ids):,} package IDs of the prior release are "
                f"still present ({_percent(in_both, len(prior_ids))}); "
                f"limit {MIN_PACKAGE_IDS_KEPT:.0%}."
            ),
        },
        {
            "id": "PACKAGES_REMOVED",
            "label": "Packages no longer present",
            "status": status(bool(prior_ids) and removed / len(prior_ids) <= MAX_PACKAGES_REMOVED),
            "detail": (
                f"{removed:,} packages ({_percent(removed, len(prior_ids))}); "
                f"limit {MAX_PACKAGES_REMOVED:.0%}."
            ),
        },
        {
            "id": "PACKAGES_CHANGED",
            "label": "Packages with changed fields",
            "status": status(in_both > 0 and changed / in_both <= MAX_PACKAGES_CHANGED),
            "detail": (
                f"{changed:,} packages ({_percent(changed, in_both)}); "
                f"limit {MAX_PACKAGES_CHANGED:.0%}."
            ),
        },
        {
            "id": "SOURCE_CLEANUPS",
            "label": "Likely source clean-ups",
            "status": "INFO",
            "detail": (
                f"{cleanups:,} of {changed:,} changed packages carry a clean-up label "
                f"({_percent(cleanups, changed)})."
            ),
        },
        {
            "id": "SHARED_VNRS",
            "label": "VNRs shared by several packages",
            "status": "INFO",
            "detail": (
                f"{shared_vnrs:,} VNRs belong to more than one package in the current "
                "release; Medicine Shortages lists every such package."
            ),
        },
    ]
    return {
        "checkId": check_id(prior_release_id, current_release_id),
        "priorReleaseId": prior_release_id,
        "currentReleaseId": current_release_id,
        "priorReleaseDate": prior_date,
        "currentReleaseDate": current_date,
        "checkedAt": (checked_at or datetime.now(UTC)).isoformat(),
        "overall": ("ATTENTION" if any(c["status"] == "ATTENTION" for c in checks) else "PASSED"),
        "counts": {
            "priorPackages": len(prior_ids),
            "currentPackages": len(current_ids),
            "inBoth": in_both,
            "changed": changed,
            "noLongerPresent": removed,
            "new": len(current_ids - prior_ids),
            "vnrGained": vnr["gained"],
            "vnrLost": vnr["lost"],
            "vnrChanged": vnr["changed"],
            "formattingOnly": labels[CleanupLabel.FORMATTING_ONLY],
            "activeSubstanceOnly": labels[CleanupLabel.ACTIVE_SUBSTANCE_ONLY],
            "unlabelled": labels["NONE"],
            "sharedVnrs": shared_vnrs,
        },
        "checks": checks,
    }
