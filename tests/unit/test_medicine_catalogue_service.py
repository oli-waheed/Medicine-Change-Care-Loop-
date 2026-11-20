
from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.domain.source_field import SourceField as F
from src.services.medicine_catalogue import MedicineCatalogueService


@pytest.fixture
def catalogue_service(snapshot_pair, monkeypatch):
    """Create a catalogue service backed by the existing fictional snapshots."""
    old, new, _order = snapshot_pair
    service = MedicineCatalogueService(store=object())

    baseline = SimpleNamespace(snapshots=(old, new))
    monkeypatch.setattr(service, "get_baseline", lambda: baseline)

    return service, old, new


def test_search_by_product_name(catalogue_service):
    service, old, new = catalogue_service

    results = service.search("fictional alpha")

    assert results == (old, new)


def test_search_by_package_identifier(catalogue_service):
    service, old, new = catalogue_service

    results = service.search("SIM-PKG-100")

    assert results == (old, new)


def test_search_by_vnr(catalogue_service):
    service, old, new = catalogue_service

    results = service.search("SIM-VNR-000123")

    assert results == (old, new)


def test_search_is_case_insensitive_and_supports_partial_matches(
    catalogue_service,
):
    service, old, new = catalogue_service

    results = service.search("  FICTIONAL ALP  ")

    assert results == (old, new)


def test_empty_search_returns_all_snapshots_in_source_order(catalogue_service):
    service, old, new = catalogue_service

    assert service.search() == (old, new)
    assert service.search("   ") == (old, new)


def test_missing_and_empty_source_fields_are_not_searchable(
    snapshot_pair, monkeypatch
):
    old, _new, _order = snapshot_pair

    snapshot = replace(
        old,
        vnr_numero=F.empty(),
        product=replace(
            old.product,
            kauppanimi=F.missing(),
        ),
    )

    service = MedicineCatalogueService(store=object())
    baseline = SimpleNamespace(snapshots=(snapshot,))
    monkeypatch.setattr(service, "get_baseline", lambda: baseline)

    assert service.search("fictional alpha") == ()
    assert service.search("SIM-VNR-000123") == ()


def test_search_returns_empty_when_no_validated_baseline_exists(monkeypatch):
    service = MedicineCatalogueService(store=object())
    monkeypatch.setattr(service, "get_baseline", lambda: None)

    assert service.search("anything") == ()
    assert service.search() == ()


def test_search_does_not_modify_source_snapshots(catalogue_service):
    service, old, new = catalogue_service

    service.search("fictional")
    service.search("SIM-PKG")

    assert old.pakkaustunnus == "SIM-PKG-100"
    assert old.vnr_numero.value == "SIM-VNR-000123"
    assert new.product.kauppanimi.value == "Fictional Alpha Updated"
