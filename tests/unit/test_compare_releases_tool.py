"""The validation helper backend/tools/compare_releases.py on synthetic releases."""

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
RELEASES = ROOT / "tests" / "fixtures" / "fimea-basic-register"
spec = importlib.util.spec_from_file_location(
    "compare_releases", ROOT / "backend" / "tools" / "compare_releases.py"
)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def _capture(storage: Path, name: str, retrieved_at: str) -> None:
    content = (RELEASES / name).read_bytes()
    checksum = hashlib.sha256(content).hexdigest()
    folder = storage / f"sha256-{checksum}"
    (folder / "files" / "0001").mkdir(parents=True)
    (folder / "files" / "0001" / "Perusrekisteri.xml").write_bytes(content)
    (folder / "manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    {"checksum": checksum, "contentReference": "files/0001/Perusrekisteri.xml"}
                ],
                "retrievedAt": retrieved_at,
            }
        ),
        encoding="utf-8",
    )


def test_orders_by_ajopvm_and_compares_newest_pairs(tmp_path, capsys):
    storage = tmp_path / "source-releases"
    # Captured out of order on purpose: the report must follow Ajopvm.
    _capture(storage, "cleanup-release.xml", "2099-01-05T06:00:00+00:00")
    _capture(storage, "prior-release.xml", "2099-01-03T06:00:00+00:00")
    _capture(storage, "current-release.xml", "2099-01-04T06:00:00+00:00")
    assert [c.ajopvm for c in tool.find_captures(storage)] == [
        "2099-01-01",
        "2099-01-02",
        "2099-01-03",
    ]

    out = tmp_path / "report.md"
    assert tool.main([str(storage), "--pairs", "2", "--out", str(out)]) == 0
    report = out.read_text(encoding="utf-8")
    assert report == capsys.readouterr().out
    first, second = report.split("## ")[1:]
    assert first.startswith("2099-01-01 → 2099-01-02")
    assert "| Release order (Ajopvm) | strictly increasing |" in first
    assert "| No longer present | 1 |" in first
    assert "| New packages (no case by design) | 1 |" in first
    assert second.startswith("2099-01-02 → 2099-01-03")
    assert "| Changed packages | 3 |" in second
    assert "| Label: spacing or letter case only | 1 |" in second
    assert "| Label: active-substance fields only | 1 |" in second
    assert "| No label | 1 |" in second
    assert "| Pakkaustunnus repeated within a release | 0 |" in second


def test_one_release_is_not_enough(tmp_path, capsys):
    storage = tmp_path / "source-releases"
    _capture(storage, "current-release.xml", "2099-01-04T06:00:00+00:00")
    assert tool.main([str(storage)]) == 0
    assert "At least two different releases are needed" in capsys.readouterr().out
