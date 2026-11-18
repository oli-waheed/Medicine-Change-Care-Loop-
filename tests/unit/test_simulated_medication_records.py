import json
from pathlib import Path

import pytest

from src.services.simulated_medication_records import load_simulated_medication_records

ROOT = Path(__file__).parents[2]


@pytest.mark.parametrize(
    "path",
    [
        ROOT / "backend" / "seed" / "simulated-medication-records.json",
        ROOT / "tests" / "fixtures" / "simulated-medication-records" / "medication-records.json",
    ],
)
def test_seed_and_fixture_files_load(path):
    records = load_simulated_medication_records(path)

    assert records
    assert all(record.record_id.startswith("SIM-") for record in records)


def test_pakkaustunnus_is_the_match_key_and_vnr_is_supporting(tmp_path):
    path = tmp_path / "records.json"
    path.write_text(
        json.dumps(
            {
                "dataset": "SIMULATED test",
                "records": [
                    {
                        "record_id": "SIM-1",
                        "person_reference": "SIM-P1",
                        "medicine_display": "Fictional",
                        "Pakkaustunnus": "SIM-PKG-1",
                        "VNR-numero": "SIM-VNR-1",
                    },
                    {
                        "record_id": "SIM-2",
                        "person_reference": "SIM-P2",
                        "medicine_display": "Fictional, VNR only",
                        "VNR-numero": "SIM-VNR-1",
                    },
                ],
            }
        )
    )

    first, second = load_simulated_medication_records(path)

    assert first.package_identifier == "SIM-PKG-1"
    assert first.supporting_package_reference == "SIM-VNR-1"
    assert second.package_identifier is None


@pytest.mark.parametrize(
    "content",
    [
        {"dataset": "patients", "records": []},
        {
            "dataset": "SIMULATED",
            "records": [{"record_id": "123", "person_reference": "SIM-P", "medicine_display": "x"}],
        },
        {
            "dataset": "SIMULATED",
            "records": [
                {"record_id": "SIM-1", "person_reference": "SIM-P", "medicine_display": "x"},
                {"record_id": "SIM-1", "person_reference": "SIM-P", "medicine_display": "y"},
            ],
        },
    ],
)
def test_non_simulated_or_duplicate_records_are_rejected(tmp_path, content):
    path = tmp_path / "records.json"
    path.write_text(json.dumps(content))

    with pytest.raises(ValueError):
        load_simulated_medication_records(path)
