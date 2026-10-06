import pytest

from src.domain.source_field import SourceField, SourceFieldState
from src.domain.source_release import SourceProvenance, SourceRelease


def test_source_field_preserves_missing_empty_and_value_states() -> None:
    missing = SourceField.missing()
    empty = SourceField.empty()
    value = SourceField.of("2099-01-01")

    assert (missing.state, missing.value) == (SourceFieldState.MISSING, None)
    assert (empty.state, empty.value) == (SourceFieldState.EMPTY, "")
    assert (value.state, value.value) == (SourceFieldState.VALUE, "2099-01-01")


def test_source_field_retains_code_table_attributes() -> None:
    field = SourceField.of(
        "fictional route",
        attributes=(("listname", "SIM-ROUTE"), ("id", "SIM-R01")),
    )

    assert field.attributes == (("listname", "SIM-ROUTE"), ("id", "SIM-R01"))


def test_source_field_rejects_inconsistent_state_values() -> None:
    with pytest.raises(ValueError, match="Missing source fields"):
        SourceField(state=SourceFieldState.MISSING, value="")

    with pytest.raises(ValueError, match="Empty source fields"):
        SourceField(state=SourceFieldState.EMPTY, value=None)

    with pytest.raises(ValueError, match="non-empty"):
        SourceField(state=SourceFieldState.VALUE, value="")

    with pytest.raises(TypeError, match="SourceFieldState"):
        SourceField(state="missing")


def test_source_release_keeps_source_metadata_and_provenance_separate() -> None:
    release = SourceRelease(
        ajopvm=SourceField.of("2099-01-01"),
        aineistoera=SourceField.of("SIM-2099-001"),
        kkera=SourceField.missing(),
        kattavuus=SourceField.of("1"),
        provenance=SourceProvenance(
            source_name="Fimea Basic Register",
            raw_file_name="prior-release.xml",
            raw_file_checksum="synthetic-checksum",
        ),
    )

    assert release.ajopvm.value == "2099-01-01"
    assert release.aineistoera.value == "SIM-2099-001"
    assert release.kkera.state is SourceFieldState.MISSING
    assert release.provenance.source_name == "Fimea Basic Register"


def test_source_provenance_requires_a_source_name() -> None:
    with pytest.raises(ValueError, match="source name"):
        SourceProvenance(source_name="")
