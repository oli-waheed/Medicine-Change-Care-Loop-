"""Feature 009: the streaming normaliser shares equal values and keeps its checks.

The same document must give the same snapshots, or the same error, as before;
only memory use and speed change.
"""

from pathlib import Path

import pytest

from src.services.normalize_basic_register_release import normalize_basic_register_release

FIXTURES = Path(__file__).parents[2] / "fixtures" / "fimea-basic-register"


def _normalize(content: bytes):
    return normalize_basic_register_release(content, file_name="x.xml", checksum="synthetic")


def _snapshots(name: str):
    _, snapshots = _normalize((FIXTURES / name).read_bytes())
    return {snapshot.pakkaustunnus: snapshot for snapshot in snapshots}


def test_packages_of_one_product_share_its_records():
    snapshots = _snapshots("current-release.xml")
    a, b = snapshots["SIM-PKG-200"], snapshots["SIM-PKG-500"]  # both SYN-PROD-200, SYN-SUB-200
    assert a.product is b.product
    assert a.authorizations is b.authorizations
    assert a.active_substances[0] is b.active_substances[0]
    # Equal source values are one object, wherever they occur.
    assert a.package.pakkauskoko_yksikko is b.package.pakkauskoko_yksikko
    assert a.package.availability.kaupan is snapshots["SIM-PKG-100"].package.availability.kaupan


def test_shared_values_compare_like_separate_ones():
    snapshots = _snapshots("current-release.xml")
    assert snapshots["SIM-PKG-200"] != snapshots["SIM-PKG-500"]
    assert snapshots["SIM-PKG-200"].source_record_locator == "/Perusrekisteri/Pakkaus[2]"
    assert snapshots["SIM-PKG-500"].source_record_locator == "/Perusrekisteri/Pakkaus[4]"


def _document(products: str, packages: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Perusrekisteri>
  <Versiotiedot><Ajopvm>2099-01-01</Ajopvm><Kattavuus>1</Kattavuus></Versiotiedot>
  {packages}
  {products}
</Perusrekisteri>""".encode()


GOOD_PRODUCT = '<Laakevalmiste id="SYN-P1"><Kauppanimi>Fictional</Kauppanimi></Laakevalmiste>'
BAD_PRODUCT = (
    '<Laakevalmiste id="SYN-P2"><Kauppanimi>A</Kauppanimi><Kauppanimi>B</Kauppanimi>'
    "</Laakevalmiste>"
)
PACKAGE = '<Pakkaus Laakevalmiste-ref="{ref}"><Pakkaustunnus>SIM-PKG-{n}</Pakkaustunnus></Pakkaus>'


def test_a_malformed_product_only_fails_when_a_package_uses_it():
    unused = _document(GOOD_PRODUCT + BAD_PRODUCT, PACKAGE.format(ref="SYN-P1", n=1))
    _, snapshots = _normalize(unused)
    assert [s.pakkaustunnus for s in snapshots] == ["SIM-PKG-1"]

    used = _document(GOOD_PRODUCT + BAD_PRODUCT, PACKAGE.format(ref="SYN-P2", n=1))
    with pytest.raises(ValueError, match="Repeated singular field: Kauppanimi"):
        _normalize(used)


@pytest.mark.parametrize(
    ("products", "packages", "message"),
    [
        (GOOD_PRODUCT, PACKAGE.format(ref="SYN-NONE", n=1), "Unresolved product reference"),
        (
            GOOD_PRODUCT,
            PACKAGE.format(ref="SYN-P1", n=1) + PACKAGE.format(ref="SYN-P1", n=1),
            "Missing or duplicate Pakkaustunnus",
        ),
        (GOOD_PRODUCT + GOOD_PRODUCT, PACKAGE.format(ref="SYN-P1", n=1), "duplicate Laakevalmiste"),
    ],
)
def test_link_and_identity_errors_are_unchanged(products, packages, message):
    with pytest.raises(ValueError, match=message):
        _normalize(_document(products, packages))


def test_wrong_root_and_missing_version_are_rejected():
    with pytest.raises(ValueError, match="Perusrekisteri"):
        _normalize(b"<Other><Versiotiedot/></Other>")
    with pytest.raises(ValueError, match="Exactly one Versiotiedot"):
        _normalize(b"<Perusrekisteri></Perusrekisteri>")
