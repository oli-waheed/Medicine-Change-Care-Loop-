"""Evidence-preserving normalized source values for one medicine package."""

from dataclasses import dataclass
from enum import StrEnum

from ..source_field import SourceField
from ..source_release import SourceRelease


@dataclass(frozen=True, slots=True)
class ProductFields:
    kauppanimi: SourceField
    vahvuus: SourceField
    laakemuoto: SourceField
    atc_koodi: SourceField
    antoreitti: tuple[SourceField, ...]


@dataclass(frozen=True, slots=True)
class ActiveSubstanceFields:
    aine: SourceField
    cas_numero: SourceField
    maara: SourceField
    maara_yksikko: SourceField
    jakamaton_vahvuus: SourceField


@dataclass(frozen=True, slots=True)
class PackageAvailabilityFields:
    kaupan: SourceField
    kauppaantulo_paiva: SourceField
    kaupasta_poistumis_paiva: SourceField


class AuthorizationBranch(StrEnum):
    MYYNTILUPA = "Myyntilupa"
    ERITYISLUPA = "Erityislupa"
    REKISTEROINTI = "Rekisterointi"


@dataclass(frozen=True, slots=True)
class AuthorizationRegistrationFields:
    branch: AuthorizationBranch
    tila: SourceField
    myontamis_paiva: SourceField
    paattymis_paiva: SourceField


@dataclass(frozen=True, slots=True)
class PackageFields:
    pakkauskoko_teksti: SourceField
    pakkauskoko: SourceField
    pakkauskoko_kerroin: SourceField
    pakkauskoko_yksikko: SourceField
    julkinen_tarkenne: SourceField
    availability: PackageAvailabilityFields


@dataclass(frozen=True, slots=True)
class MedicineSnapshot:
    """One package's source evidence; references are scoped to its source release."""

    pakkaustunnus: str
    vnr_numero: SourceField
    product_reference: SourceField
    product: ProductFields
    active_substances: tuple[ActiveSubstanceFields, ...]
    package: PackageFields
    authorizations: tuple[AuthorizationRegistrationFields, ...]
    source_release: SourceRelease
    source_record_locator: str | None = None

    def __post_init__(self) -> None:
        if not self.pakkaustunnus:
            raise ValueError("Pakkaustunnus is required as the package identity.")
        if not isinstance(self.active_substances, tuple):
            raise TypeError("Active substances must remain an ordered tuple of source records.")
        if not isinstance(self.authorizations, tuple):
            raise TypeError("Authorization branches must remain an ordered tuple.")
