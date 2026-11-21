"""Compare normalized snapshots only when source order is explicitly supported.

XML parsing/capture belongs to T022/T023. The caller supplies normalized snapshots
and source ordering evidence; local retrieval times are never ordering keys.
"""

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, fields
from datetime import UTC, datetime

from ..domain.detected_change import DetectedChange, PackageChangeKind, PackageChangeSet
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
    """Field-level ``changes`` plus their per-package grouping in ``change_sets``.

    Change sets also include packages that are no longer present in the current
    release; those have no field-level changes.
    """

    changes: tuple[DetectedChange, ...]
    classification: EvidenceClassification
    notes: tuple[str, ...] = ()
    change_sets: tuple[PackageChangeSet, ...] = ()


# Feature 015: read for linking records, not compared. Whether the holder becomes
# a compared field is a team decision, like T018 for VNR.
_NOT_COMPARED = frozenset({"haltija"})


def project_snapshot_fields(snapshot: MedicineSnapshot) -> dict[str, tuple[SourceField, ...]]:
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
            if field.name in _NOT_COMPARED:
                continue
            item = getattr(value, field.name)
            if isinstance(item, SourceField):
                result[f"{prefix}/{names[field.name]}"] = (item,)
            elif isinstance(item, tuple):
                # Repeated values (e.g. Antoreitti) keep source order (data-model.md).
                result[f"{prefix}/{names[field.name]}"] = item

    add("Laakevalmiste", snapshot.product)
    for label, substance in _labelled_substances(snapshot.active_substances):
        add(f"Laakeaine/VaikuttavaAine[{label}]", substance)
    add("Pakkaus", snapshot.package)
    # Decision T018 (2026-11-21): VNR is compared, because shortages link by VNR.
    result["Pakkaus/VNR-numero"] = (snapshot.vnr_numero,)
    add("Pakkaus/Kaupanolo", snapshot.package.availability)
    per_branch = Counter()
    for authorization in snapshot.authorizations:
        branch = authorization.branch.value
        add(f"Laakevalmiste/{branch}[{per_branch[branch]}]", authorization)
        per_branch[branch] += 1
    return result


def _field_sort_key(field: SourceField):
    return (field.state.value, field.value or "", field.attributes)


def _substance_identity(substance) -> str:
    """Stable identity used to pair the same active substance across releases.

    Prefer the Aine code (CT attribute ``id``), then the Aine text, then the CAS
    number. Pairing by list position would compare different substances with
    each other whenever their order differs, producing false before/after values.
    Snapshots still keep every occurrence in source order.
    """
    aine = substance.aine
    code = dict(aine.attributes).get("id")
    if code:
        return f"Aine={code}"
    if aine.value:
        return f"Aine={aine.value}"
    if substance.cas_numero.value:
        return f"CAS={substance.cas_numero.value}"
    return "Aine=unidentified"


def _labelled_substances(substances):
    groups: dict[str, list] = {}
    for substance in substances:
        groups.setdefault(_substance_identity(substance), []).append(substance)
    for identity in sorted(groups):
        group = groups[identity]
        if len(group) == 1:
            yield identity, group[0]
            continue
        # The same substance listed more than once: order by content so the pairing
        # is deterministic. Changes inside such a group are reported per member.
        ordered = sorted(
            group, key=lambda item: [_field_sort_key(getattr(item, f.name)) for f in fields(item)]
        )
        for n, substance in enumerate(ordered, start=1):
            yield f"{identity}#{n}", substance


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
    release_identities = [
        _release_identity(order.prior_release),
        _release_identity(order.current_release),
    ]
    note = "Source-data difference only; cross-release key stability is not established generally."

    def change_set_id(key, kind):
        identity = [*release_identities, key, kind.value]
        return hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()

    def record_evidence(snapshot, key):
        return EvidenceProvenance(
            source_release=snapshot.source_release,
            source_record_identifier=key,
            source_record_locator=snapshot.source_record_locator,
            classification=EvidenceClassification.VERIFIED,
            note=note,
        )

    changes, change_sets, notes = [], [], []
    for key in sorted(old.keys() | new.keys()):
        if old_counts[key] == 1 and new_counts[key] == 0:
            change_sets.append(
                PackageChangeSet(
                    change_set_id=change_set_id(key, PackageChangeKind.NO_LONGER_PRESENT),
                    medicine_key=key,
                    kind=PackageChangeKind.NO_LONGER_PRESENT,
                    field_changes=(),
                    prior_snapshot=old[key],
                    current_snapshot=None,
                    prior_evidence=record_evidence(old[key], key),
                    current_evidence=EvidenceProvenance(
                        source_release=order.current_release,
                        source_record_identifier=key,
                        classification=EvidenceClassification.VERIFIED,
                        note=(
                            "No Pakkaus with this Pakkaustunnus in this full-coverage "
                            "release. The source does not state why."
                        ),
                    ),
                    change_evidence_class=EvidenceClassification.VERIFIED,
                    prior_source_order=order.prior_order,
                    current_source_order=order.current_order,
                    source_order_basis=order.basis,
                    detected_at=timestamp,
                )
            )
            continue
        if old_counts[key] == 0 and new_counts[key] == 1:
            notes.append(f"Package {key}: newly present; no review case is created.")
            continue
        if old_counts[key] != 1 or new_counts[key] != 1:
            notes.append(f"Package {key}: ambiguous pair; no change asserted.")
            continue
        before, after = old[key], new[key]
        old_fields, new_fields = project_snapshot_fields(before), project_snapshot_fields(after)
        package_changes = []
        for path in sorted(old_fields.keys() | new_fields.keys()):
            old_value = old_fields.get(path, (SourceField.missing(),))
            new_value = new_fields.get(path, (SourceField.missing(),))
            if old_value == new_value:
                continue
            identity = [*release_identities, key, path]
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
                    note=note,
                )

            package_changes.append(
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
        if not package_changes:
            continue
        changes.extend(package_changes)
        change_sets.append(
            PackageChangeSet(
                change_set_id=change_set_id(key, PackageChangeKind.FIELDS_CHANGED),
                medicine_key=key,
                kind=PackageChangeKind.FIELDS_CHANGED,
                field_changes=tuple(package_changes),
                prior_snapshot=before,
                current_snapshot=after,
                prior_evidence=record_evidence(before, key),
                current_evidence=record_evidence(after, key),
                change_evidence_class=EvidenceClassification.VERIFIED,
                prior_source_order=order.prior_order,
                current_source_order=order.current_order,
                source_order_basis=order.basis,
                detected_at=timestamp,
            )
        )
    return ComparisonResult(
        tuple(changes), EvidenceClassification.VERIFIED, tuple(notes), tuple(change_sets)
    )
