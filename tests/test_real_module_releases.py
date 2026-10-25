"""Real release archives must import and obey the Suite contract after relocation.

Unlike fixture-only ZIP tests, this covers every shipped engineering module
with its real Python package, numerical dependencies and session imports.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import sys
import zipfile

from PySide6.QtWidgets import QApplication

from scripts.build_module_dist import build
from slipsurface.apps import catalogue
from slipsurface.contract import satisfies_contract
from slipsurface.desktop.icons import module_icon
from slipsurface.desktop.profiles import profile
from slipsurface.installer import install_release
from slipsurface.registry import discover, load_manifest


def test_installed_real_archives_import_and_satisfy_contract(tmp_path):
    packages = []
    for module in catalogue():
        key = module.key
        archive = build(key, tmp_path / "releases")
        raw = archive.read_bytes()
        with zipfile.ZipFile(archive) as zipped:
            manifest = json.loads(zipped.read(f"{key}-1.0.0/app.json"))
            source = zipped.read(
                f"{key}-1.0.0/slipsurface_{key}/__init__.py"
            ).decode("utf-8")
        assert "from .. import __version__" not in source
        assert manifest["session"] == f"slipsurface_{key}.web.session"
        installed = install_release(
            {
                "key": key,
                "version": manifest["version"],
                "url": archive.resolve().as_uri(),
                "sha256": hashlib.sha256(raw).hexdigest(),
            },
            apps_root=tmp_path / "apps",
            fetch=lambda _url, data=raw: data,
        )
        assert installed == manifest
        packages.append(key)
    try:
        discovered = {item["key"]: item for item in discover(tmp_path / "apps")}
        assert set(packages).issubset(discovered)
        for key in packages:
            module = importlib.import_module(discovered[key]["session"])
            session = module.Session() if key == "kinematic" else module.Session(lang="tr")
            assert satisfies_contract(session), key
            result = session.meta()
            assert isinstance(result["schema"], dict)
            assert isinstance(result["defaults"], dict)
    finally:
        for key in packages:
            prefix = f"slipsurface_{key}"
            for name in list(sys.modules):
                if name == prefix or name.startswith(prefix + "."):
                    del sys.modules[name]
            plugin_root = str(tmp_path / "apps" / key)
            if plugin_root in sys.path:
                sys.path.remove(plugin_root)


def test_unknown_plugin_has_safe_default_profile_and_icon(monkeypatch):
    import slipsurface.apps as apps

    app = QApplication.instance() or QApplication([])
    data = {
        "key": "new_solver",
        "name": "New Solver",
        "tr": "Yeni Analiz",
        "group": "Foundations",
        "description": "Plugin demonstration",
        "description_tr": "Eklenti gösterimi",
        "version": "2.1.0",
    }
    manifest = load_manifest(data)
    assert manifest["key"] == "new_solver"
    monkeypatch.setitem(apps._BY_KEY, "new_solver", apps._from_manifest(manifest))
    default = profile("new_solver")
    assert default.module == "new_solver"
    assert default.hint_tr
    icon = module_icon("new_solver")
    assert not icon.isNull()
    assert not icon.pixmap(36, 36).isNull()
    assert app is not None
