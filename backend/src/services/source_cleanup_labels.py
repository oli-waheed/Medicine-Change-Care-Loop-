"""Feature 008: deterministic labels for likely source clean-ups.

A label only describes the shape of a detected difference. It never hides,
closes or changes a case, and every value stays visible exactly as published.

- A field change is *formatting only* when the before and after values have the
  same states and attributes and differ only in spaces or letter case.
- A release case is labelled ``FORMATTING_ONLY`` when every field change is
  formatting only, else ``ACTIVE_SUBSTANCE_ONLY`` when every changed field is an
  active-substance field (``Laakeaine/...``). Otherwise it has no label.

The rules work on the stored case view (``changeSet.changes`` with ``before`` and
``after`` source values), so cases created before this feature are labelled too.
"""

from enum import StrEnum

ACTIVE_SUBSTANCE_PREFIX = "Laakeaine/"


class CleanupLabel(StrEnum):
    FORMATTING_ONLY = "FORMATTING_ONLY"
    ACTIVE_SUBSTANCE_ONLY = "ACTIVE_SUBSTANCE_ONLY"


def _folded(value: str | None) -> str | None:
    return None if value is None else " ".join(value.split()).casefold()


def formatting_only(before: list[dict], after: list[dict]) -> bool:
    """True when the two lists differ, but only in spaces or letter case."""
    if before == after or len(before) != len(after):
        return False
    for old, new in zip(before, after, strict=True):
        if old["state"] != new["state"] or old.get("attributes") != new.get("attributes"):
            return False
        if _folded(old["value"]) != _folded(new["value"]):
            return False
    return True


def cleanup_label(changes: list[dict]) -> CleanupLabel | None:
    """The label for one package's field changes, or ``None``."""
    if not changes:
        return None
    if all(formatting_only(change["before"], change["after"]) for change in changes):
        return CleanupLabel.FORMATTING_ONLY
    if all(change["field"].startswith(ACTIVE_SUBSTANCE_PREFIX) for change in changes):
        return CleanupLabel.ACTIVE_SUBSTANCE_ONLY
    return None


def with_cleanup_labels(payload: dict) -> dict:
    """Return a copy of a release case view with its labels; others unchanged."""
    change_set = payload.get("changeSet")
    if payload.get("caseType", "RELEASE") != "RELEASE" or not change_set:
        return payload
    changes = [
        {**change, "formattingOnly": formatting_only(change["before"], change["after"])}
        for change in change_set["changes"]
    ]
    label = cleanup_label(change_set["changes"])
    return {
        **payload,
        "changeSet": {
            **change_set,
            "changes": changes,
            "cleanupLabel": label.value if label else None,
        },
    }
