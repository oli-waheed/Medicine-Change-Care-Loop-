r"""Compare real Fimea Basic Register releases captured by the app (validation helper).

Reads the raw captures that the daily update, the "Check for new Fimea release"
button or an upload stored, orders them by each file's own Ajopvm, and compares
each consecutive pair with the app's own normalisation and comparison rules.
It reads files only: nothing is changed in the database or the captures.

The report answers the README's remaining validation questions: is the release
order strictly increasing, is every Pakkaustunnus unique within a release and
present in both releases of a pair, and what kinds of changes were found.

Usage, from the backend folder (each release takes about 15 s):

    python tools\compare_releases.py data\real\source-releases
    python tools\compare_releases.py data\real\source-releases --pairs 3 --out report.md

Without --pairs only the newest pair is compared.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.domain.source_field import SourceField  # noqa: E402
from src.services.detect_relevant_changes import project_snapshot_fields  # noqa: E402
from src.services.normalize_basic_register_release import (  # noqa: E402
    normalize_basic_register_release,
)
from src.services.source_cleanup_labels import cleanup_label  # noqa: E402

VNR_FIELD = "Pakkaus/VNR-numero"


@dataclass(frozen=True)
class CapturedFile:
    path: Path
    checksum: str
    retrieved_at: str
    ajopvm: str


def _ajopvm(path: Path) -> str:
    # Versiotiedot comes first in the file; the start is enough.
    with path.open("rb") as handle:
        head = handle.read(4096).decode("utf-8", errors="replace")
    start = head.find("<Ajopvm>")
    end = head.find("</Ajopvm>")
    if start < 0 or end < start:
        return ""
    return head[start + len("<Ajopvm>") : end].strip()


def find_captures(storage: Path) -> list[CapturedFile]:
    """Every captured Basic Register file, oldest Ajopvm first, each content once."""
    found: dict[str, CapturedFile] = {}
    for manifest_path in sorted(storage.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest.get("files", ()):
            path = manifest_path.parent / entry["contentReference"]
            if path.is_file() and entry["checksum"] not in found:
                found[entry["checksum"]] = CapturedFile(
                    path, entry["checksum"], manifest.get("retrievedAt", ""), _ajopvm(path)
                )
    return sorted(found.values(), key=lambda item: (item.ajopvm, item.retrieved_at))


def _plain(values: tuple[SourceField, ...]) -> list[dict]:
    return [
        {"state": v.state.value, "value": v.value, "attributes": dict(v.attributes)} for v in values
    ]


def _load(capture: CapturedFile):
    content = capture.path.read_bytes()
    _, snapshots = normalize_basic_register_release(
        content, file_name=capture.path.name, checksum=hashlib.sha256(content).hexdigest()
    )
    counts = Counter(s.pakkaustunnus for s in snapshots)
    fields = {s.pakkaustunnus: project_snapshot_fields(s) for s in snapshots}
    return counts, fields


def compare_pair(prior: CapturedFile, current: CapturedFile) -> list[str]:
    old_counts, old = _load(prior)
    new_counts, new = _load(current)
    duplicates = sum(1 for n in old_counts.values() if n > 1) + sum(
        1 for n in new_counts.values() if n > 1
    )
    both = old.keys() & new.keys()
    groups: Counter[str] = Counter()
    labels: Counter[str] = Counter()
    vnr = Counter()
    for key in both:
        before, after = old[key], new[key]
        changes = []
        for path in before.keys() | after.keys():
            a = before.get(path, (SourceField.missing(),))
            b = after.get(path, (SourceField.missing(),))
            if a != b:
                changes.append({"field": path, "before": _plain(a), "after": _plain(b)})
        if not changes:
            continue
        groups["changed"] += 1
        label = cleanup_label(changes)
        labels[label.value if label else "no label"] += 1
        vnr_change = next((c for c in changes if c["field"] == VNR_FIELD), None)
        if vnr_change:
            had = vnr_change["before"][0]["state"] == "value"
            has = vnr_change["after"][0]["state"] == "value"
            vnr["gained" if has and not had else "lost" if had and not has else "changed"] += 1
    order_ok = prior.ajopvm < current.ajopvm
    return [
        f"## {prior.ajopvm} → {current.ajopvm}",
        "",
        "| Check | Result |",
        "|---|---|",
        f"| Release order (Ajopvm) | {'strictly increasing' if order_ok else 'NOT increasing'} |",
        f"| Files | `{prior.checksum[:12]}…` ({prior.retrieved_at}) → "
        f"`{current.checksum[:12]}…` ({current.retrieved_at}) |",
        f"| Packages | {len(old_counts):,} → {len(new_counts):,} |",
        f"| Pakkaustunnus repeated within a release | {duplicates} |",
        f"| Pakkaustunnus in both releases | {len(both):,} |",
        f"| Changed packages | {groups['changed']:,} |",
        f"| No longer present | {len(old.keys() - new.keys()):,} |",
        f"| New packages (no case by design) | {len(new.keys() - old.keys()):,} |",
        f"| VNR gained / lost / changed | {vnr['gained']} / {vnr['lost']} / {vnr['changed']} |",
        f"| Label: spacing or letter case only | {labels['FORMATTING_ONLY']:,} |",
        f"| Label: active-substance fields only | {labels['ACTIVE_SUBSTANCE_ONLY']:,} |",
        f"| No label | {labels['no label']:,} |",
        "",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("storage", type=Path, help="the source-release capture folder")
    parser.add_argument("--pairs", type=int, default=1, help="newest consecutive pairs")
    parser.add_argument("--out", type=Path, help="also write the report to this file")
    args = parser.parse_args(argv)

    captures = find_captures(args.storage)
    lines = ["# Real-release comparison", "", f"Captured releases found: {len(captures)}", ""]
    lines += [f"- {c.ajopvm or 'no Ajopvm'}: `{c.checksum[:12]}…`" for c in captures]
    lines.append("")
    if len(captures) < 2:
        lines.append("At least two different releases are needed; wait for the next daily update.")
    else:
        pairs = list(zip(captures, captures[1:], strict=False))[-max(args.pairs, 1) :]
        for prior, current in pairs:
            print(f"Comparing {prior.ajopvm} → {current.ajopvm} ...", file=sys.stderr, flush=True)
            lines += compare_pair(prior, current)
    report = "\n".join(lines)
    print(report)
    if args.out:
        args.out.write_text(report + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
