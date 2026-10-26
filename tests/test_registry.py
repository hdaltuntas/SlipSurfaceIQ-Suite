"""Manifest registry, versioning and update-catalogue checks.

Standard-library friendly: nothing here imports PySide6, so the checks run
in any environment that has the package on ``sys.path``.
"""
import json

from slipsurface import CORE_VERSION
from slipsurface.apps import APPS, keys
from slipsurface.contract import satisfies_contract
from slipsurface.registry import REQUIRED_FIELDS, ManifestError, discover, load_manifest
from slipsurface.versioning import VersionError, compare, is_compatible, parse

EXPECTED_ORDER = [
    "kinematic", "rock", "bearing", "settle", "correlation",
    "liquefaction", "pile", "spwa", "msew", "wall",
]


class FakeSession:
    """The smallest object that satisfies the application contract."""

    def meta(self) -> dict: ...
    def analyse(self, values: dict) -> dict: ...
    def plot(self, target: str, kind: str) -> bytes: ...
    def report(self, kind: str, path: str) -> None: ...
    def project_file(self, values: dict) -> dict: ...
    def load_project(self, payload: dict) -> dict: ...


def test_versioning_parses_and_compares():
    assert parse("v1.2.3") == (1, 2, 3)
    assert parse(" 1.2.3 ") == (1, 2, 3)
    assert compare("1.2.3", "1.2.3") == 0
    assert compare("1.2.3", "1.10.0") == -1
    assert compare("2.0.0", "1.9.9") == 1
    try:
        parse("1.2")
        raise AssertionError("unpadded versions must be rejected")
    except VersionError:
        pass


def test_versioning_is_compatible():
    assert is_compatible("0.1.0", ">=0.1.0")
    assert is_compatible("0.1.0", ">=0.1.0,<0.2.0")
    assert not is_compatible("0.2.0", ">=0.1.0,<0.2.0")
    assert is_compatible("0.1.0", "")
    assert is_compatible("0.1.0", "!=0.3.0")
    assert not is_compatible("0.1.0", "==0.2.0")


def test_discover_finds_ten_modules_in_stable_order():
    manifests = discover()
    assert [manifest["key"] for manifest in manifests] == EXPECTED_ORDER


def test_every_manifest_is_complete_and_correctly_versioned():
    orders = []
    for manifest in discover():
        assert set(REQUIRED_FIELDS) <= set(manifest), manifest["key"]
        assert is_compatible(CORE_VERSION, manifest["requires_core"]), manifest["key"]
        parse(manifest["version"])  # must be a well-formed release number
        orders.append(manifest["order"])
    assert sorted(orders) == list(range(1, 11))


def test_apps_catalogue_keeps_the_original_order_and_carries_versions():
    assert keys() == EXPECTED_ORDER
    assert [app.key for app in APPS] == EXPECTED_ORDER
    assert all(app.version == (
        "2026.0.2" if app.key == "rock" else
        "2026.0.1" if app.key == "bearing" else "2026.0.0"
    ) for app in APPS)
    assert all(app.requires_core == ">=0.1.0" for app in APPS)


def test_load_manifest_rejects_incomplete_or_broken_manifests():
    try:
        load_manifest({"key": "pile", "name": "Pile"})
        raise AssertionError("incomplete manifests must be rejected")
    except ManifestError:
        pass
    try:
        load_manifest({"key": "pile", "name": "Pile", "tr": "Kazık", "group": "Foundations",
                       "description": "d", "description_tr": "a", "version": "1.0"})
        raise AssertionError("unpadded manifest versions must be rejected")
    except ManifestError:
        pass


def test_satisfies_contract_accepts_a_duck_typed_session():
    assert satisfies_contract(FakeSession())
    assert not satisfies_contract(object())


def test_updater_reports_only_newer_releases():
    from slipsurface.desktop.updater import AppUpdate, check

    updates = check({
        "pile": {"version": "2026.0.1", "changelog": "socket", "requires_core": ">=0.1.0"},
        "rock": "2026.0.2",                       # same version, not an update
        "wall": "2025.9.0",                       # older than installed
        "msew": {"version": "2027.0.0", "requires_core": ">=9.0.0"},
    })
    assert set(updates) == {"pile", "msew"}
    assert updates["pile"].update_available and updates["pile"].core_ok
    assert updates["msew"].core_ok is False
    assert updates["pile"].changelog == "socket"
    assert AppUpdate("pile", "1.0.0", "1.0.0").update_available is False


def test_updater_reads_a_catalogue_file(tmp_path):
    from slipsurface.desktop.updater import read_index

    path = tmp_path / "slipsurface-index.json"
    path.write_text(json.dumps({"pile": {"version": "1.2.0"}}), encoding="utf-8")
    try:
        index = read_index(path)
        assert index["pile"]["version"] == "1.2.0"
    finally:
        path.unlink(missing_ok=True)
