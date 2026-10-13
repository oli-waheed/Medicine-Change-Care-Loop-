import pytest

from src.domain.medicine_snapshot import (
    ActiveSubstanceFields,
    AuthorizationBranch,
    AuthorizationRegistrationFields,
    MedicineSnapshot,
    PackageAvailabilityFields,
    PackageFields,
    ProductFields,
)
from src.domain.source_field import SourceField, SourceFieldState
from src.domain.source_release import SourceProvenance, SourceRelease


def make_snapshot() -> MedicineSnapshot:
    source_release = SourceRelease(
        ajopvm=SourceField.of("2099-01-01"),
        aineistoera=SourceField.of("SIM-2099-001"),
        kkera=SourceField.empty(),
        kattavuus=SourceField.of("1"),
        provenance=SourceProvenance(source_name="Fimea Basic Register"),
    )
    return MedicineSnapshot(
        pakkaustunnus="SIM-PKG-100",
        vnr_numero=SourceField.of("SIM-VNR-100"),
        product_reference=SourceField.of("SYN-PROD-100"),
        product=ProductFields(
            kauppanimi=SourceField.of("Fictional Product Amber"),
            vahvuus=SourceField.of("synthetic strength A"),
            laakemuoto=SourceField.empty(
                attributes=(("listname", "SIM-FORM"), ("id", "SIM-F01"), ("value", ""))
            ),
            atc_koodi=SourceField.missing(),
            antoreitti=(SourceField.of("fictional route"), SourceField.empty()),
        ),
        active_substances=(
            ActiveSubstanceFields(
                aine=SourceField.of("fictional substance"),
                cas_numero=SourceField.of("SIM-CAS-100"),
                maara=SourceField.of("1.0"),
                maara_yksikko=SourceField.of(
                    "synthetic units",
                    attributes=(("listname", "SIM-UNIT"), ("id", "SIM-MASS")),
                ),
                jakamaton_vahvuus=SourceField.missing(),
            ),
        ),
        package=PackageFields(
            pakkauskoko_teksti=SourceField.of("synthetic pack size"),
            pakkauskoko=SourceField.of("10"),
            pakkauskoko_kerroin=SourceField.of("1"),
            pakkauskoko_yksikko=SourceField.of("fictional units"),
            julkinen_tarkenne=SourceField.empty(),
            availability=PackageAvailabilityFields(
                kaupan=SourceField.of("1"),
                kauppaantulo_paiva=SourceField.of("2098-12-01"),
                kaupasta_poistumis_paiva=SourceField.empty(),
            ),
        ),
        authorizations=(
            AuthorizationRegistrationFields(
                branch=AuthorizationBranch.MYYNTILUPA,
                tila=SourceField.of(
                    "synthetic active",
                    attributes=(("listname", "SIM-AUTH"), ("id", "SIM-ACTIVE")),
                ),
                myontamis_paiva=SourceField.of("2098-01-01"),
                paattymis_paiva=SourceField.of("2099-12-31"),
            ),
        ),
        source_release=source_release,
        source_record_locator="/Perusrekisteri/Pakkaus[1]",
    )


def test_snapshot_retains_t005_fields_and_provenance() -> None:
    snapshot = make_snapshot()

    assert snapshot.pakkaustunnus == "SIM-PKG-100"
    assert snapshot.vnr_numero.value == "SIM-VNR-100"
    assert snapshot.product_reference.value == "SYN-PROD-100"
    assert snapshot.product.antoreitti[1].state is SourceFieldState.EMPTY
    assert snapshot.product.laakemuoto.attributes[0] == ("listname", "SIM-FORM")
    assert snapshot.active_substances[0].jakamaton_vahvuus.state is SourceFieldState.MISSING
    assert snapshot.package.julkinen_tarkenne.state is SourceFieldState.EMPTY
    assert snapshot.package.availability.kaupasta_poistumis_paiva.value == ""
    assert snapshot.authorizations[0].branch is AuthorizationBranch.MYYNTILUPA
    assert snapshot.source_release.provenance.source_name == "Fimea Basic Register"
    assert snapshot.source_record_locator == "/Perusrekisteri/Pakkaus[1]"


def test_snapshot_requires_the_primary_package_identifier() -> None:
    snapshot = make_snapshot()

    with pytest.raises(ValueError, match="Pakkaustunnus"):
        MedicineSnapshot(
            pakkaustunnus="",
            vnr_numero=snapshot.vnr_numero,
            product_reference=snapshot.product_reference,
            product=snapshot.product,
            active_substances=snapshot.active_substances,
            package=snapshot.package,
            authorizations=snapshot.authorizations,
            source_release=snapshot.source_release,
        )


def test_snapshot_allows_missing_vnr_without_changing_primary_identity() -> None:
    snapshot = make_snapshot()

    assert snapshot.pakkaustunnus == "SIM-PKG-100"
    assert snapshot.vnr_numero.state is SourceFieldState.VALUE

    without_vnr = MedicineSnapshot(
        pakkaustunnus=snapshot.pakkaustunnus,
        vnr_numero=SourceField.missing(),
        product_reference=snapshot.product_reference,
        product=snapshot.product,
        active_substances=snapshot.active_substances,
        package=snapshot.package,
        authorizations=snapshot.authorizations,
        source_release=snapshot.source_release,
    )

    assert without_vnr.pakkaustunnus == "SIM-PKG-100"
    assert without_vnr.vnr_numero.state is SourceFieldState.MISSING
