"""Shared normalized fictional snapshots; XML normalization remains T022."""

import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))
from src.domain.evidence import EvidenceClassification
from src.domain.medicine_snapshot import (
    ActiveSubstanceFields,
    AuthorizationBranch,
    AuthorizationRegistrationFields,
    MedicineSnapshot,
    PackageAvailabilityFields,
    PackageFields,
    ProductFields,
)
from src.domain.review_case import SimulatedMedicationRecord
from src.domain.source_field import SourceField as F
from src.domain.source_release import SourceProvenance, SourceRelease
from src.services.detect_relevant_changes import (
    SourceOrderEvidence,
    detect_relevant_changes,
)


@pytest.fixture
def snapshot_pair():
    old_release = SourceRelease(
        F.of("2099-01-01"),
        F.of("SIM-001"),
        SourceProvenance("Synthetic Fimea Basic Register", "prior.xml", "old-checksum"),
        F.missing(),
        F.of("1"),
    )
    new_release = replace(
        old_release,
        ajopvm=F.of("2099-01-02"),
        aineistoera=F.of("SIM-002"),
        provenance=SourceProvenance(
            "Synthetic Fimea Basic Register", "current.xml", "new-checksum"
        ),
    )
    old = MedicineSnapshot(
        "SIM-PKG-100",
        F.of("000123"),
        F.of("PRODUCT-OLD"),
        ProductFields(
            F.of("Fictional Alpha"),
            F.of("10 mg"),
            F.of("tablet"),
            F.of("SIM-ATC"),
            (F.of("oral"),),
        ),
        (
            ActiveSubstanceFields(
                F.of("Fictional substance"),
                F.missing(),
                F.of("10"),
                F.of("mg"),
                F.missing(),
            ),
        ),
        PackageFields(
            F.of("20 tablets"),
            F.of("20"),
            F.of("1"),
            F.of("tablet"),
            F.empty(),
            PackageAvailabilityFields(F.of("1"), F.missing(), F.missing()),
        ),
        (
            AuthorizationRegistrationFields(
                AuthorizationBranch.MYYNTILUPA, F.of("active"), F.missing(), F.missing()
            ),
        ),
        old_release,
        "/Perusrekisteri/Pakkaus[1]",
    )
    new = replace(
        old,
        product=replace(old.product, kauppanimi=F.of("Fictional Alpha Updated")),
        source_release=new_release,
        product_reference=F.of("PRODUCT-NEW"),
    )
    order = SourceOrderEvidence(
        old_release,
        new_release,
        1,
        2,
        EvidenceClassification.VERIFIED,
        "Controlled fictional fixture release sequence, not retrieval time.",
    )
    return old, new, order


@pytest.fixture
def detected_change(snapshot_pair):
    old, new, order = snapshot_pair
    return detect_relevant_changes((old,), (new,), order=order).changes[0]


@pytest.fixture
def medication_record():
    return SimulatedMedicationRecord(
        "SIM-MED-100", "SIM-PERSON-100", "Fictional Alpha", "SIM-PKG-100", "000123"
    )
