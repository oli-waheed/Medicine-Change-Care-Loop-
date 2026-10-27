"""Compare normalized snapshots only when source order is explicitly supported.

XML parsing/capture belongs to T022/T023. The caller supplies normalized snapshots
and source ordering evidence; local retrieval times are never ordering keys.
"""

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, fields
from datetime import UTC, datetime

from ..domain.detected_change import DetectedChange
from ..domain.evidence import EvidenceClassification, EvidenceProvenance
from ..domain.medicine_snapshot import MedicineSnapshot
from ..domain.source_field import SourceField
from ..domain.source_release import SourceRelease


@dataclass(frozen=True, slots=True)
class SourceOrderEvidence:
    prior_release: SourceRelease
    current_release: SourceRelease
    prior_order: int
    current_order: int
    classification: EvidenceClassification
    basis: str

    def __post_init__(self) -> None:
        if not self.basis.strip():
            raise ValueError("Source ordering evidence needs a documented basis.")
        if type(self.prior_order) is not int or type(self.current_order) is not int:
            raise TypeError("Source order must use established integer ordering keys.")


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    changes: tuple[DetectedChange, ...]
    classification: EvidenceClassification
    notes: tuple[str, ...] = ()


def _project(snapshot: MedicineSnapshot) -> dict[str, tuple[SourceField, ...]]:
    names = {
        "kauppanimi": "Kauppanimi",
        "vahvuus": "Vahvuus",
        "laakemuoto": "Laakemuoto",
        "atc_koodi": "ATC-koodi",
        "antoreitti": "Antoreitti",
        "aine": "Aine",
        "cas_numero": "CASnumero",
        "maara": "Maara",
        "maara_yksikko": "Maarayksikko",
        "jakamaton_vahvuus": "JakamatonVahvuus",
        "pakkauskoko_teksti": "Pakkauskokoteksti",
        "pakkauskoko": "Pakkauskoko",
        "pakkauskoko_kerroin": "Pakkauskokokerroin",
        "pakkauskoko_yksikko": "Pakkauskokoyksikko",
        "julkinen_tarkenne": "JulkinenTarkenne",
        "kaupan": "Kaupan",
        "kauppaantulo_paiva": "Kauppaantulopaiva",
        "kaupasta_poistumis_paiva": "Kaupastapoistumispaiva",
        "tila": "Tila",
        "myontamis_paiva": "Myontamispaiva",
        "paattymis_paiva": "Paattymispaiva",
    }
    result = {}

    def add(prefix, value):
        for field in fields(value):
            item = getattr(value, field.name)
            if isinstance(item, SourceField):
                result[f"{prefix}/{names[field.name]}"] = (item,)
            elif isinstance(item, tuple):
                result[f"{prefix}/{names[field.name]}"] = item

    add("Laakevalmiste", snapshot.product)
    for i, substance in enumerate(snapshot.active_substances):
        add(f"Laakeaine/VaikuttavaAine[{i}]", substance)
    add("Pakkaus", snapshot.package)
    add("Pakkaus/Kaupanolo", snapshot.package.availability)
    for i, authorization in enumerate(snapshot.authorizations):
        add(f"Laakevalmiste/{authorization.branch.value}[{i}]", authorization)
    return result


def _release_identity(release: SourceRelease):
    # Content checksum distinguishes reissues with identical date/batch labels.
    def value(field):
        return [field.state.value, field.value, field.attributes]

    return [
        release.provenance.source_name,
        release.provenance.raw_file_name,
        release.provenance.raw_file_checksum,
        value(release.ajopvm),
        value(release.aineistoera),
        value(release.kkera),
        value(release.kattavuus),
    ]


def detect_relevant_changes(
    prior: tuple[MedicineSnapshot, ...],
    current: tuple[MedicineSnapshot, ...],
    *,
    order: SourceOrderEvidence | None,
    detected_at: datetime | None = None,
) -> ComparisonResult:
    if not prior:
        return ComparisonResult(
            (), EvidenceClassification.UNKNOWN, ("First release is baseline only.",)
        )
    if order is None or order.classification is not EvidenceClassification.VERIFIED:
        classification = EvidenceClassification.UNKNOWN if order is None else order.classification
        return ComparisonResult((), classification, ("Source order is not verified.",))
    if order.current_order <= order.prior_order:
        return ComparisonResult(
            (), EvidenceClassification.CONFLICTING, ("Source order is not strictly increasing.",)
        )
    if order.prior_release.provenance.source_name != order.current_release.provenance.source_name:
        return ComparisonResult(
            (), EvidenceClassification.CONFLICTING, ("Source identities disagree.",)
        )
    if any(s.source_release != order.prior_release for s in prior) or any(
        s.source_release != order.current_release for s in current
    ):
        return ComparisonResult(
            (),
            EvidenceClassification.CONFLICTING,
            ("Snapshots do not belong to the ordered releases.",),
        )
    timestamp = detected_at or datetime.now(UTC)
    old_counts = Counter(s.pakkaustunnus for s in prior)
    new_counts = Counter(s.pakkaustunnus for s in current)
    old = {s.pakkaustunnus: s for s in prior}
    new = {s.pakkaustunnus: s for s in current}
    changes, notes = [], []
    for key in sorted(old.keys() | new.keys()):
        if old_counts[key] != 1 or new_counts[key] != 1:
            notes.append(f"Package {key}: absent or ambiguous pair; no field change asserted.")
            continue
        before, after = old[key], new[key]
        old_fields, new_fields = _project(before), _project(after)
        for path in sorted(old_fields.keys() | new_fields.keys()):
            old_value = old_fields.get(path, (SourceField.missing(),))
            new_value = new_fields.get(path, (SourceField.missing(),))
            if old_value == new_value:
                continue
            identity = [
                _release_identity(before.source_release),
                _release_identity(after.source_release),
                key,
                path,
            ]
            change_id = hashlib.sha256(
                json.dumps(identity, ensure_ascii=False).encode()
            ).hexdigest()

            def evidence(snapshot):
                return EvidenceProvenance(
                    source_release=snapshot.source_release,
                    source_record_identifier=key,
                    source_record_locator=snapshot.source_record_locator,
                    field_reference=path,
                    classification=EvidenceClassification.VERIFIED,
                    note=(
                        "Source-data difference only; cross-release key stability "
                        "is not established generally."
                    ),
                )

            changes.append(
                DetectedChange(
                    change_id,
                    key,
                    path,
                    old_value,
                    new_value,
                    before,
                    after,
                    evidence(before),
                    evidence(after),
                    EvidenceClassification.VERIFIED,
                    order.prior_order,
                    order.current_order,
                    order.basis,
                    timestamp,
                )
            )
    return ComparisonResult(tuple(changes), EvidenceClassification.VERIFIED, tuple(notes))
