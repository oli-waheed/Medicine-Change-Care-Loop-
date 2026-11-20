"""Feature 004 T027: the catalogue service against real stored source releases.

Verifies T007 (validated baseline selection) and T008 (snapshot reconstruction
from the captured release) with the synthetic fixture releases, uploaded through
the same ingestion endpoint the n8n workflow uses.
"""

import asyncio
import json
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile
from starlette.requests import Request

from src.api.source_release_ingestion import ingest_uploaded_source_release
from src.services.medicine_catalogue import MedicineCatalogueService
from src.services.pipeline_store import PipelineStore

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "fimea-basic-register"
UNKNOWN_ORDER = {"value": None, "evidenceClass": "UNKNOWN"}


def _upload(app, filename, *, day, declared_order=None):
    request = Request(
        {
            "type": "http",
            "app": app,
            "headers": [],
            "method": "POST",
            "path": "/api/source-releases/ingest",
            "query_string": b"",
        }
    )
    content = (FIXTURE_DIR / filename).read_bytes()
    return asyncio.run(
        ingest_uploaded_source_release(
            request,
            UploadFile(filename=filename, file=BytesIO(content)),
            source_name="Fimea Basic Register",
            source_release_reference=json.dumps(
                {"value": f"SIM-{filename}", "evidenceClass": "VERIFIED"}
            ),
            retrieved_at=datetime(2099, 1, day, tzinfo=UTC).isoformat(),
            source_order=json.dumps(declared_order or UNKNOWN_ORDER),
        )
    )


def _package_ids(baseline):
    return sorted(snapshot.pakkaustunnus for snapshot in baseline.snapshots)


def test_no_validated_release_means_no_baseline(isolated_app):
    service = MedicineCatalogueService(isolated_app.state.store)

    assert service.get_baseline() is None
    assert service.search() == ()


def test_baseline_is_the_validated_release_with_its_packages(isolated_app):
    app = isolated_app
    prior = _upload(app, "prior-release.xml", day=3)
    service = MedicineCatalogueService(app.state.store)

    baseline = service.get_baseline()

    assert baseline.release_id == prior["capturedReleaseReference"]
    assert _package_ids(baseline) == [
        "SIM-PKG-100",
        "SIM-PKG-200",
        "SIM-PKG-300",
        "SIM-PKG-500",
    ]
    assert {s.source_release.ajopvm.value for s in baseline.snapshots} == {"2099-01-01"}


def test_newer_release_replaces_the_cached_baseline(isolated_app):
    app = isolated_app
    _upload(app, "prior-release.xml", day=3)
    service = MedicineCatalogueService(app.state.store)
    first = service.get_baseline()

    current = _upload(app, "current-release.xml", day=4)
    second = service.get_baseline()

    assert second.release_id == current["capturedReleaseReference"]
    assert second.release_id != first.release_id
    # SIM-PKG-300 is no longer in the register; SIM-PKG-400 is new.
    assert _package_ids(second) == [
        "SIM-PKG-100",
        "SIM-PKG-200",
        "SIM-PKG-400",
        "SIM-PKG-500",
    ]


def test_same_baseline_reuses_the_reconstructed_release(isolated_app):
    _upload(isolated_app, "prior-release.xml", day=3)
    service = MedicineCatalogueService(isolated_app.state.store)

    assert service.get_baseline().ingestion is service.get_baseline().ingestion


def test_older_release_uploaded_later_does_not_become_the_baseline(isolated_app):
    app = isolated_app
    current = _upload(app, "current-release.xml", day=3)
    _upload(app, "prior-release.xml", day=4)

    baseline = MedicineCatalogueService(app.state.store).get_baseline()

    assert baseline.release_id == current["capturedReleaseReference"]


def test_release_without_verified_chronology_is_never_the_baseline(isolated_app):
    app = isolated_app
    _upload(
        app,
        "ordering-unknown-release.xml",
        day=3,
        declared_order={"value": "1", "evidenceClass": "VERIFIED"},
    )

    assert MedicineCatalogueService(app.state.store).get_baseline() is None


def test_baseline_survives_a_restart(isolated_app):
    app = isolated_app
    prior = _upload(app, "prior-release.xml", day=3)
    database_url = app.state.store.database_url

    app.state.store.dispose()
    app.state.store = PipelineStore(database_url)
    baseline = MedicineCatalogueService(app.state.store).get_baseline()

    assert baseline.release_id == prior["capturedReleaseReference"]
    assert len(baseline.snapshots) == 4


def test_search_works_on_a_real_stored_release(isolated_app):
    _upload(isolated_app, "current-release.xml", day=3)
    service = MedicineCatalogueService(isolated_app.state.store)

    assert [s.pakkaustunnus for s in service.search("sim-pkg-400")] == ["SIM-PKG-400"]
    assert [s.pakkaustunnus for s in service.search("SIM-VNR-200")] == ["SIM-PKG-200"]
    assert len(service.search()) == 4


def test_cache_is_cleared_when_the_baseline_disappears(isolated_app, monkeypatch):
    store = isolated_app.state.store
    _upload(isolated_app, "prior-release.xml", day=3)
    service = MedicineCatalogueService(store)
    first = service.get_baseline()

    real_baseline = store.comparison_baseline
    monkeypatch.setattr(store, "comparison_baseline", lambda: None)
    assert service.get_baseline() is None

    monkeypatch.setattr(store, "comparison_baseline", real_baseline)
    again = service.get_baseline()
    assert again.release_id == first.release_id
    assert again.ingestion is not first.ingestion


def test_tampered_capture_is_rejected_instead_of_shown(isolated_app):
    store = isolated_app.state.store
    _upload(isolated_app, "prior-release.xml", day=3)
    directory = Path(store.comparison_baseline().capture_directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    (directory / manifest["files"][0]["contentReference"]).write_bytes(b"<changed/>")

    with pytest.raises(ValueError, match="no longer matches its checksum"):
        MedicineCatalogueService(store).get_baseline()
