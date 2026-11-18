"""T033: guard that every seeded, test and demo data file stays simulated.

Runs on every test run, so real patient or real medicine data cannot slip into
tests/fixtures/ or backend/seed/ unnoticed. See tests/fixtures/README.md.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
FIXTURES = ROOT / "tests" / "fixtures"
SEED = ROOT / "backend" / "seed"
RECORD_FILES = [
    FIXTURES / "simulated-medication-records" / "medication-records.json",
    SEED / "simulated-medication-records.json",
]
RELEASE_FIXTURES = sorted((FIXTURES / "fimea-basic-register").glob("*.xml"))
DATA_FILES = sorted(
    path
    for folder in (FIXTURES, SEED)
    for path in folder.rglob("*")
    if path.is_file() and path.name != ".gitkeep"
)

# Finnish personal identity code (henkilötunnus), e-mail addresses, Finnish phone numbers,
# and the formats of real ATC codes (e.g. N02BE01) and real CAS numbers (e.g. 103-90-2).
FORBIDDEN_PATTERNS = {
    "personal identity code": re.compile(r"\b[0-3]\d[01]\d\d{2}[-+A-FU-Y]\d{3}[0-9A-Y]\b"),
    "e-mail address": re.compile(r"[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    "phone number": re.compile(r"\+358|\b0[45]\d{7,8}\b"),
    "real-format ATC code": re.compile(r"\b[A-V]\d{2}[A-Z]{2}\d{2}\b"),
    "real-format CAS number": re.compile(r"\b\d{2,7}-\d{2}-\d\b"),
}


def _id(path: Path) -> str:
    return str(path.relative_to(ROOT))


def test_the_guard_sees_the_expected_files():
    assert len(RELEASE_FIXTURES) >= 4
    assert all(path.exists() for path in RECORD_FILES)


@pytest.mark.parametrize("path", DATA_FILES, ids=_id)
def test_no_personal_or_real_code_patterns(path):
    text = path.read_text(encoding="utf-8")
    for name, pattern in FORBIDDEN_PATTERNS.items():
        assert not pattern.search(text), f"{name} found in {_id(path)}"


@pytest.mark.parametrize("path", RECORD_FILES, ids=_id)
def test_medication_records_are_declared_and_identified_as_simulated(path):
    data = json.loads(path.read_text(encoding="utf-8"))

    assert "SIMULATED" in data["dataset"].upper()
    for record in data["records"]:
        assert record["record_id"].startswith("SIM-"), record
        assert record["person_reference"].startswith("SIM-"), record
        assert record["medicine_display"].startswith("Fictional"), record
        for key in ("Pakkaustunnus", "VNR-numero"):
            if key in record:
                assert record[key].startswith("SIM-"), record


def _values(text: str, tag: str) -> list[str]:
    return [value.strip() for value in re.findall(rf"<{tag}>([^<]*)</{tag}>", text)]


@pytest.mark.parametrize("path", RELEASE_FIXTURES, ids=_id)
def test_release_fixtures_are_synthetic(path):
    # Regular expressions instead of an XML parser, so the malformed fixture is checked too.
    text = path.read_text(encoding="utf-8")

    for tag in ("Pakkaustunnus", "VNR-numero", "CASnumero", "Aineistoera"):
        for value in _values(text, tag):
            assert value.startswith("SIM-"), f"{tag}={value!r} in {_id(path)}"
    for value in _values(text, "Kauppanimi"):
        assert value.startswith("Fictional"), f"Kauppanimi={value!r} in {_id(path)}"
    for value in re.findall(r'\b(?:id|listname|Laakevalmiste-ref|Laakeaine-ref)="([^"]*)"', text):
        assert value.startswith(("SIM-", "SYN-")), f"identifier {value!r} in {_id(path)}"
    for value in _values(text, "Ajopvm"):
        assert int(value[:4]) >= 2090, f"Ajopvm={value!r} looks like a real release in {_id(path)}"
