
"""Read access to the latest validated medicine catalogue release."""

from dataclasses import dataclass
from threading import RLock

from ..domain.medicine_snapshot import MedicineSnapshot
from ..domain.source_field import SourceFieldState
from ..models import SourceReleaseCaptureRow
from ..services.ingest_source_release import (
    IngestionOutcome,
    ProcessingStatus,
    reload_captured_release,
)
from .pipeline_store import PipelineStore


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

    def get_baseline(self) -> MedicineCatalogueBaseline | None:
        """Return the latest validated baseline, or None when none exists."""

        capture = self._store.comparison_baseline()

        if capture is None:
            with self._lock:
                self._cached_release_id = None
                self._cached_ingestion = None
            return None

        with self._lock:
            if (
                self._cached_release_id == capture.release_id
                and self._cached_ingestion is not None
            ):
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

        normalized_query = query.strip().casefold()

        if not normalized_query:
            return baseline.snapshots

        return tuple(
            snapshot
            for snapshot in baseline.snapshots
            if self._snapshot_matches(snapshot, normalized_query)
        )
