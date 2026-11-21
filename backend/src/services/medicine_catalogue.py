"""Read access to the latest validated medicine catalogue release."""

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from threading import Lock, RLock, Thread

from ..domain.medicine_snapshot import ActiveSubstanceFields, MedicineSnapshot
from ..domain.source_field import SourceField, SourceFieldState
from ..models import SourceReleaseCaptureRow
from ..services.ingest_source_release import (
    IngestionOutcome,
    ProcessingStatus,
    reload_captured_release,
)
from .detect_relevant_changes import _substance_identity, project_snapshot_fields
from .pipeline_store import PipelineStore

logger = logging.getLogger(__name__)

# Fields a caller can require to be absent (missing, or no occurrences).
ABSENCE_FIELDS = frozenset({"vnr", "atc", "form", "route", "available"})

# Product-level paths for the two-product comparison (FR-007). Package fields
# differ per package and are compared on the package page instead.
COMPARISON_PREFIXES = ("Laakevalmiste/", "Laakeaine/")


@dataclass(frozen=True, slots=True)
class MedicineCatalogueBaseline:
    """A reconstructed, validated catalogue baseline."""

    capture: SourceReleaseCaptureRow
    ingestion: IngestionOutcome

    @property
    def release_id(self) -> str:
        return self.capture.release_id

    @property
    def snapshots(self) -> tuple[MedicineSnapshot, ...]:
        return self.ingestion.snapshots


class MedicineCatalogueService:
    """Provides read-only access to the selected validated source release.

    The service reuses the existing baseline-selection and release-reconstruction
    logic. It keeps at most one reconstructed release in memory.
    """

    def __init__(self, store: PipelineStore) -> None:
        self._store = store
        self._lock = RLock()
        self._cached_release_id: str | None = None
        self._cached_ingestion: IngestionOutcome | None = None
        self._vnr_index: tuple[str, dict[str, tuple[MedicineSnapshot, ...]]] | None = None
        self._warm_lock = Lock()
        self._warming: Thread | None = None

    @property
    def store(self) -> PipelineStore:
        return self._store

    def cached_baseline(self) -> MedicineCatalogueBaseline | None:
        """The active baseline if it is already in memory; never reconstructs.

        Returns None while another thread is reconstructing it (feature 006 uses
        this so the shortage list never waits for the catalogue).
        """

        capture = self._store.comparison_baseline()
        if capture is None or not self._lock.acquire(blocking=False):
            return None
        try:
            if self._cached_release_id != capture.release_id or self._cached_ingestion is None:
                return None
            return MedicineCatalogueBaseline(capture=capture, ingestion=self._cached_ingestion)
        finally:
            self._lock.release()

    def warm_in_background(self) -> None:
        """Reconstruct the baseline in a background thread, once at a time."""

        with self._warm_lock:
            if self._warming is not None and self._warming.is_alive():
                return
            self._warming = Thread(target=self._warm, name="catalogue-warm", daemon=True)
            self._warming.start()

    def _warm(self) -> None:
        try:
            self.get_baseline()
        except Exception:  # noqa: BLE001 - the catalogue API reports the error itself
            logger.exception("Catalogue baseline could not be prepared.")

    def packages_by_vnr(
        self, baseline: MedicineCatalogueBaseline
    ) -> dict[str, tuple[MedicineSnapshot, ...]]:
        """Packages of the baseline grouped by their VNR value (feature 006)."""

        with self._lock:
            if self._vnr_index is not None and self._vnr_index[0] == baseline.release_id:
                return self._vnr_index[1]
            grouped: dict[str, list[MedicineSnapshot]] = {}
            for snapshot in baseline.snapshots:
                vnr = snapshot.vnr_numero
                if vnr.state is SourceFieldState.VALUE and vnr.value:
                    grouped.setdefault(vnr.value, []).append(snapshot)
            index = {key: tuple(value) for key, value in grouped.items()}
            self._vnr_index = (baseline.release_id, index)
            return index

    def get_baseline(self) -> MedicineCatalogueBaseline | None:
        """Return the latest validated baseline, or None when none exists."""

        capture = self._store.comparison_baseline()

        if capture is None:
            with self._lock:
                self._cached_release_id = None
                self._cached_ingestion = None
            return None

        with self._lock:
            if self._cached_release_id == capture.release_id and self._cached_ingestion is not None:
                ingestion = self._cached_ingestion
            else:
                ingestion = reload_captured_release(capture.capture_directory)

                if ingestion.processing_status is not ProcessingStatus.VALIDATED:
                    raise ValueError(
                        "The selected catalogue baseline could not be reconstructed "
                        "as a validated release."
                    )

                self._cached_release_id = capture.release_id
                self._cached_ingestion = ingestion

        return MedicineCatalogueBaseline(
            capture=capture,
            ingestion=ingestion,
        )

    @staticmethod
    def _field_matches(field, query: str) -> bool:
        """Match a query against a populated source field only."""

        return (
            field.state is SourceFieldState.VALUE
            and field.value is not None
            and query in field.value.casefold()
        )

    @classmethod
    def _snapshot_matches(
        cls,
        snapshot: MedicineSnapshot,
        query: str,
    ) -> bool:
        """Search product name, package identity and VNR."""

        return (
            query in snapshot.pakkaustunnus.casefold()
            or cls._field_matches(snapshot.product.kauppanimi, query)
            or cls._field_matches(snapshot.vnr_numero, query)
        )

    def search(self, query: str = "") -> tuple[MedicineSnapshot, ...]:
        """Search the active catalogue by product name, package ID or VNR.

        An empty query returns every snapshot in the selected baseline.
        Results preserve the original source ordering and package identities.
        """

        baseline = self.get_baseline()

        if baseline is None:
            return ()

        return _search(baseline.snapshots, query)

    # T010: filters on source-recorded fields (FR-003).
    def filter(
        self, query: str = "", filters: "CatalogueFilters | None" = None
    ) -> tuple[MedicineSnapshot, ...] | None:
        """Search and filter the active catalogue; None when no baseline exists."""

        baseline = self.get_baseline()
        if baseline is None:
            return None
        filters = filters or CatalogueFilters()
        return tuple(s for s in _search(baseline.snapshots, query) if filters.matches(s))

    # T011: product details (FR-004).
    def product(self, product_reference: str) -> "ProductView | None":
        baseline = self._require_baseline()
        packages = tuple(
            s for s in baseline.snapshots if _text(s.product_reference) == product_reference
        )
        if not packages:
            return None
        return ProductView(product_reference, packages)

    # T012, T016, T017: package details, explicit VNR and VNR grouping (FR-005, FR-012, FR-013).
    def package(self, pakkaustunnus: str) -> "PackageView | None":
        baseline = self._require_baseline()
        snapshot = next((s for s in baseline.snapshots if s.pakkaustunnus == pakkaustunnus), None)
        if snapshot is None:
            return None
        return PackageView(snapshot, same_vnr_packages(baseline.snapshots, snapshot))

    # T013: active-substance exploration (FR-006).
    def active_substances(self, query: str = "") -> tuple["SubstanceEntry", ...] | None:
        baseline = self.get_baseline()
        if baseline is None:
            return None
        return substance_entries(baseline.snapshots, query)

    # T014: two-product comparison of source fields (FR-007).
    def compare(self, reference_a: str, reference_b: str) -> "ProductComparison | None":
        product_a = self.product(reference_a)
        product_b = self.product(reference_b)
        if product_a is None or product_b is None:
            return None
        return compare_products(product_a, product_b)

    # T015: active release and provenance summary (FR-008).
    def source_summary(self) -> "SourceSummary | None":
        baseline = self.get_baseline()
        if baseline is None:
            return None
        snapshots = baseline.snapshots
        return SourceSummary(
            baseline=baseline,
            package_count=len(snapshots),
            product_count=len({_text(s.product_reference) for s in snapshots}),
            active_substance_count=len(substance_entries(snapshots, "")),
        )

    # T018: callers that need data must handle the unavailable state explicitly.
    def _require_baseline(self) -> MedicineCatalogueBaseline:
        baseline = self.get_baseline()
        if baseline is None:
            raise CatalogueUnavailableError("No validated source release with verified chronology.")
        return baseline


class CatalogueUnavailableError(LookupError):
    """No validated release with verified chronology is available (FR-009)."""


def _text(field: SourceField) -> str:
    return field.value or ""


def _search(snapshots: tuple[MedicineSnapshot, ...], query: str) -> tuple[MedicineSnapshot, ...]:
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return snapshots
    return tuple(
        snapshot
        for snapshot in snapshots
        if MedicineCatalogueService._snapshot_matches(snapshot, normalized_query)
    )


def _match_keys(field: SourceField) -> set[str]:
    """Values a filter can match: the text, and a code-table id and display value."""

    if field.state is SourceFieldState.MISSING:
        return set()
    keys = {field.value.casefold()} if field.value else set()
    attributes = dict(field.attributes)
    keys |= {attributes[name].casefold() for name in ("id", "value") if attributes.get(name)}
    return keys


def _absent(fields: Iterable[SourceField]) -> bool:
    """True when every occurrence is missing, or there are no occurrences."""

    return all(f.state is SourceFieldState.MISSING for f in fields)


def substance_identity(substance: ActiveSubstanceFields) -> str:
    """The existing change-detection identity: Aine code, then text, then CAS number."""

    return _substance_identity(substance)


@dataclass(frozen=True, slots=True)
class CatalogueFilters:
    """Exact or prefix filters on source-recorded fields; all must match (AND)."""

    active_substance: str | None = None
    atc: str | None = None
    form: str | None = None
    route: str | None = None
    available: str | None = None
    vnr: str | None = None
    missing: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        unknown = set(self.missing) - ABSENCE_FIELDS
        if unknown:
            raise ValueError(
                f"Unknown missing-field filter {sorted(unknown)}; use {sorted(ABSENCE_FIELDS)}."
            )

    def matches(self, snapshot: MedicineSnapshot) -> bool:
        product = snapshot.product
        checks = (
            (
                self.atc,
                lambda wanted: any(k.startswith(wanted) for k in _match_keys(product.atc_koodi)),
            ),
            (self.form, lambda wanted: wanted in _match_keys(product.laakemuoto)),
            (
                self.route,
                lambda wanted: any(wanted in _match_keys(r) for r in product.antoreitti),
            ),
            (
                self.available,
                lambda wanted: wanted in _match_keys(snapshot.package.availability.kaupan),
            ),
            (self.vnr, lambda wanted: wanted in _match_keys(snapshot.vnr_numero)),
            (
                self.active_substance,
                lambda wanted: any(
                    wanted == substance_identity(s).casefold() or wanted in _match_keys(s.aine)
                    for s in snapshot.active_substances
                ),
            ),
        )
        for wanted, check in checks:
            if wanted is not None and wanted.strip() and not check(wanted.strip().casefold()):
                return False
        absent_fields = {
            "vnr": (snapshot.vnr_numero,),
            "atc": (product.atc_koodi,),
            "form": (product.laakemuoto,),
            "route": product.antoreitti,
            "available": (snapshot.package.availability.kaupan,),
        }
        return all(_absent(absent_fields[name]) for name in self.missing)


@dataclass(frozen=True, slots=True)
class ProductView:
    """One Laakevalmiste and its packages in the active release."""

    product_reference: str
    packages: tuple[MedicineSnapshot, ...]

    @property
    def representative(self) -> MedicineSnapshot:
        # Product fields come from the shared Laakevalmiste element, so every
        # package of the product carries the same values.
        return self.packages[0]

    @property
    def active_substances(self) -> tuple[ActiveSubstanceFields, ...] | None:
        """The product's substances, or None when its packages list different ones."""

        first = self.packages[0].active_substances
        if all(p.active_substances == first for p in self.packages):
            return first
        return None


@dataclass(frozen=True, slots=True)
class PackageView:
    snapshot: MedicineSnapshot
    same_vnr_packages: tuple[str, ...]


def same_vnr_packages(
    snapshots: tuple[MedicineSnapshot, ...], snapshot: MedicineSnapshot
) -> tuple[str, ...]:
    """Other packages with an equal, present VNR; never merged, never inferred."""

    vnr = snapshot.vnr_numero
    if vnr.state is not SourceFieldState.VALUE:
        return ()
    return tuple(
        other.pakkaustunnus
        for other in snapshots
        if other.pakkaustunnus != snapshot.pakkaustunnus
        and other.vnr_numero.state is SourceFieldState.VALUE
        and other.vnr_numero.value == vnr.value
    )


@dataclass(frozen=True, slots=True)
class SubstanceOccurrence:
    pakkaustunnus: str
    product_reference: str
    product_name: SourceField
    position: int
    substance: ActiveSubstanceFields


@dataclass(frozen=True, slots=True)
class SubstanceEntry:
    identity: str
    name: SourceField
    cas_number: SourceField
    occurrences: tuple[SubstanceOccurrence, ...]


def substance_entries(
    snapshots: tuple[MedicineSnapshot, ...], query: str
) -> tuple[SubstanceEntry, ...]:
    """Group substance occurrences by identity, keeping source order and repeats."""

    normalized_query = query.strip().casefold()
    groups: dict[str, list[SubstanceOccurrence]] = {}
    for snapshot in snapshots:
        for position, substance in enumerate(snapshot.active_substances, start=1):
            groups.setdefault(substance_identity(substance), []).append(
                SubstanceOccurrence(
                    snapshot.pakkaustunnus,
                    _text(snapshot.product_reference),
                    snapshot.product.kauppanimi,
                    position,
                    substance,
                )
            )
    entries = []
    for identity, occurrences in groups.items():
        first = occurrences[0].substance
        if normalized_query and not (
            normalized_query in identity.casefold()
            or any(normalized_query in key for key in _match_keys(first.aine))
            or any(normalized_query in key for key in _match_keys(first.cas_numero))
        ):
            continue
        entries.append(SubstanceEntry(identity, first.aine, first.cas_numero, tuple(occurrences)))
    return tuple(entries)


@dataclass(frozen=True, slots=True)
class ComparedField:
    path: str
    a: tuple[SourceField, ...]
    b: tuple[SourceField, ...]

    @property
    def same(self) -> bool:
        # Full SourceField equality: state, value and attributes. Missing is never
        # equal to empty, and order matters for repeated fields.
        return self.a == self.b


@dataclass(frozen=True, slots=True)
class ProductComparison:
    product_a: ProductView
    product_b: ProductView
    fields: tuple[ComparedField, ...]


def compare_products(product_a: ProductView, product_b: ProductView) -> ProductComparison:
    """Compare product-level source fields using the existing field paths (read-only)."""

    fields_a = project_snapshot_fields(product_a.representative)
    fields_b = project_snapshot_fields(product_b.representative)
    paths = sorted(
        path for path in set(fields_a) | set(fields_b) if path.startswith(COMPARISON_PREFIXES)
    )
    return ProductComparison(
        product_a,
        product_b,
        tuple(
            ComparedField(path, fields_a.get(path, ()), fields_b.get(path, ())) for path in paths
        ),
    )


@dataclass(frozen=True, slots=True)
class SourceSummary:
    baseline: MedicineCatalogueBaseline
    package_count: int
    product_count: int
    active_substance_count: int
