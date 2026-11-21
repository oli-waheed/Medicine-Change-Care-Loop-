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
# Feature 014: a field's share of packages with a value may fall this much at most.
MAX_COMPLETENESS_DROP = 0.02

VNR_FIELD = "Pakkaus/VNR-numero"


# Feature 014: fields whose completeness (share of packages with a value) is tracked.
COMPLETENESS_FIELDS = (
    ("VNR-numero", lambda s: s.vnr_numero),
    ("Kauppanimi", lambda s: s.product.kauppanimi),
    ("Vahvuus", lambda s: s.product.vahvuus),
    ("Laakemuoto", lambda s: s.product.laakemuoto),
    ("ATC-koodi", lambda s: s.product.atc_koodi),
    ("Pakkauskokoteksti", lambda s: s.package.pakkauskoko_teksti),
    ("Kaupan", lambda s: s.package.availability.kaupan),
    ("Active substance", lambda s: s.active_substances),
    ("Authorisation or registration", lambda s: s.authorizations),
)


def _present(value) -> bool:
    if isinstance(value, tuple):
        return len(value) > 0
    # A code-table field can carry its text in attributes with an empty value.
    return value.state is SourceFieldState.VALUE or (
        value.state is SourceFieldState.EMPTY and bool(value.attributes)
    )


def completeness(snapshots) -> dict[str, float]:
    """Share of packages (0–1) that have each tracked field."""
    total = len(snapshots)
    return {
        name: (sum(1 for s in snapshots if _present(get(s))) / total if total else 0.0)
        for name, get in COMPLETENESS_FIELDS
    }


def _structure_check(prior_release, current_release) -> dict:
    before = {path for path, _ in prior_release.structure}
    after = {path for path, _ in current_release.structure}
    added, removed = sorted(after - before), sorted(before - after)
    schema_changed = prior_release.schema_location != current_release.schema_location
    parts = [
        f"{len(after)} element paths",
        f"declares {current_release.schema_location or 'no schema'}",
    ]
    if schema_changed:
        parts.append(f"was {prior_release.schema_location or 'no schema'}")
    if added:
        parts.append("new: " + ", ".join(added[:5]) + (" …" if len(added) > 5 else ""))
    if removed:
        parts.append("gone: " + ", ".join(removed[:5]) + (" …" if len(removed) > 5 else ""))
    if not (added or removed or schema_changed):
        parts.append("same as the prior release")
    return {
        "id": "SOURCE_STRUCTURE",
        "label": "Source structure",
        "status": "ATTENTION" if added or removed or schema_changed else "PASSED",
        "detail": "; ".join(parts) + ".",
    }


def _completeness_check(prior_shares: dict, current_shares: dict) -> dict:
    drops = sorted(
        ((prior_shares[name] - current_shares[name], name) for name in prior_shares),
        reverse=True,
    )
    worst_drop, worst = drops[0]
    if worst_drop > MAX_COMPLETENESS_DROP:
        detail = (
            f"{worst} is present in {current_shares[worst]:.2%} of packages, "
            f"down from {prior_shares[worst]:.2%}; limit a drop of "
            f"{100 * MAX_COMPLETENESS_DROP:.0f} percentage points."
        )
        status = "ATTENTION"
    else:
        detail = (
            f"No tracked field lost more than {100 * MAX_COMPLETENESS_DROP:.0f} percentage "
            f"points (largest drop {100 * max(worst_drop, 0):.2f} points, {worst})."
        )
        status = "PASSED"
    return {
        "id": "FIELD_COMPLETENESS",
        "label": "Field completeness",
        "status": status,
        "detail": detail,
    }


# Version 2 (feature 014) added field completeness and source structure. Stored
# checks of an older version are made again by the daily update's backfill.
CHECK_VERSION = 2


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
    prior_shares = completeness(prior.snapshots)
    current_shares = completeness(current.snapshots)
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
        _completeness_check(prior_shares, current_shares),
        _structure_check(prior.source_release, current.source_release),
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
        "version": CHECK_VERSION,
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
        # Feature 014: share of packages (in %) with each tracked field.
        "completeness": [
            {
                "field": name,
                "prior": round(100 * prior_shares[name], 2),
                "current": round(100 * current_shares[name], 2),
            }
            for name, _ in COMPLETENESS_FIELDS
        ],
    }
