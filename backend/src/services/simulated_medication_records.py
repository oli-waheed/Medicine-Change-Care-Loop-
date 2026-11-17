"""Load clearly simulated medication records from a JSON seed file.

The file format matches ``tests/fixtures/simulated-medication-records``:
``{"dataset": "SIMULATED ...", "records": [{"record_id": "SIM-...", ...}]}``.
Pakkaustunnus is the only match key; VNR-numero is kept as supporting data.
"""

import json
from pathlib import Path

from ..domain.review_case import SimulatedMedicationRecord


def load_simulated_medication_records(path: str | Path) -> tuple[SimulatedMedicationRecord, ...]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise ValueError("Simulated medication records file must contain a 'records' list.")
    dataset = data.get("dataset")
    if not isinstance(dataset, str) or "SIMULATED" not in dataset.upper():
        raise ValueError("The records file must declare itself as a SIMULATED dataset.")

    records = []
    seen_ids = set()
    for entry in data["records"]:
        if not isinstance(entry, dict):
            raise ValueError("Each simulated medication record must be an object.")
        record = SimulatedMedicationRecord(
            record_id=entry.get("record_id", ""),
            person_reference=entry.get("person_reference", ""),
            medicine_display=entry.get("medicine_display", ""),
            package_identifier=entry.get("Pakkaustunnus"),
            supporting_package_reference=entry.get("VNR-numero"),
        )
        if record.record_id in seen_ids:
            raise ValueError(f"Duplicate simulated record id: {record.record_id}")
        seen_ids.add(record.record_id)
        records.append(record)
    return tuple(records)
