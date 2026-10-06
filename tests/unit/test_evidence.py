import pytest

from src.domain.evidence import EvidenceClassification, EvidenceProvenance
from src.domain.source_field import SourceField, SourceFieldState
from src.domain.source_release import SourceProvenance, SourceRelease


def make_source_release() -> SourceRelease:
    return SourceRelease(
        ajopvm=SourceField.of("2099-01-01"),
        aineistoera=SourceField.of("SIM-2099-001"),
        provenance=SourceProvenance(
            source_name="Fimea Basic Register",
            raw_file_name="synthetic-release.xml",
            raw_file_checksum="synthetic-checksum",
        ),
        kkera=SourceField.missing(),
        kattavuus=SourceField.of("1"),
    )


@pytest.mark.parametrize(
    "classification",
    [
        EvidenceClassification.VERIFIED,
        EvidenceClassification.INFERRED,
        EvidenceClassification.UNKNOWN,
        EvidenceClassification.CONFLICTING,
    ],
)
def test_evidence_provenance_supports_all_classifications(
    classification: EvidenceClassification,
) -> None:
    evidence = EvidenceProvenance(
        source_release=make_source_release(),
        source_record_identifier="SIM-PKG-100",
        classification=classification,
    )

    assert evidence.classification is classification


def test_evidence_provenance_retains_release_and_record_traceability() -> None:
    evidence = EvidenceProvenance(
        source_release=make_source_release(),
        source_record_identifier="SIM-PKG-100",
        source_record_locator="/Perusrekisteri/Pakkaus[1]",
        field_reference="Pakkaus/Pakkauskoko",
        classification=EvidenceClassification.VERIFIED,
        source_value=SourceField.of("10"),
        note="Synthetic fixture value copied from the source-shaped test record.",
    )

    assert evidence.source_release.provenance.source_name == "Fimea Basic Register"
    assert evidence.source_release.aineistoera.value == "SIM-2099-001"
    assert evidence.source_release.ajopvm.value == "2099-01-01"
    assert evidence.source_record_identifier == "SIM-PKG-100"
    assert evidence.source_record_locator == "/Perusrekisteri/Pakkaus[1]"
    assert evidence.field_reference == "Pakkaus/Pakkauskoko"
    assert evidence.source_value == SourceField.of("10")
    assert evidence.classification is EvidenceClassification.VERIFIED
    assert evidence.note.startswith("Synthetic")


def test_evidence_provenance_can_record_unknown_source_release_metadata() -> None:
    release = SourceRelease(
        ajopvm=SourceField.missing(),
        aineistoera=SourceField.missing(),
        provenance=SourceProvenance(source_name="Synthetic source"),
        kkera=SourceField.missing(),
        kattavuus=SourceField.missing(),
    )

    evidence = EvidenceProvenance(
        source_release=release,
        source_record_identifier="SIM-RECORD-UNKNOWN-RELEASE",
        classification=EvidenceClassification.UNKNOWN,
    )

    assert evidence.source_release.aineistoera.state is SourceFieldState.MISSING
    assert evidence.source_release.ajopvm.state is SourceFieldState.MISSING


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("source_record_identifier", "", "source record or package identifier"),
        ("source_record_identifier", "   ", "source record or package identifier"),
        ("source_record_locator", "", "Source record locator"),
        ("field_reference", " ", "Field reference"),
        ("note", "", "Note"),
    ],
)
def test_evidence_provenance_rejects_missing_or_blank_required_values(
    field: str, value: str, error: str
) -> None:
    values = {
        "source_release": make_source_release(),
        "source_record_identifier": "SIM-PKG-100",
        "classification": EvidenceClassification.UNKNOWN,
    }
    values[field] = value

    with pytest.raises(ValueError, match=error):
        EvidenceProvenance(**values)


def test_evidence_provenance_rejects_invalid_release_and_classification_types() -> None:
    with pytest.raises(TypeError, match="SourceRelease"):
        EvidenceProvenance(
            source_release=None,
            source_record_identifier="SIM-PKG-100",
            classification=EvidenceClassification.UNKNOWN,
        )

    with pytest.raises(TypeError, match="EvidenceClassification"):
        EvidenceProvenance(
            source_release=make_source_release(),
            source_record_identifier="SIM-PKG-100",
            classification="VERIFIED",
        )
