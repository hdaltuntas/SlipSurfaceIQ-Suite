"""Incompatible module releases must never become clickable or importable."""
from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QMessageBox

from slipsurface.desktop.app import MainWindow
from slipsurface.desktop.home import HomePage
from slipsurface.registry import discover, incompatible_modules


def incompatible_manifest(key, version="9.0.0"):
    return {
        "key": key, "name": key.title(), "tr": "Uyumsuz Analiz",
        "group": "Foundations", "description": "Needs newer core",
        "description_tr": "Daha yeni çekirdek gerekiyor",
        "version": version, "requires_core": ">=9.0.0",
        "session": f"slipsurface_{key}.web.session",
    }


def _write_release(root, key):
    folder = root / key
    (folder / f"slipsurface_{key}").mkdir(parents=True)
    (folder / "app.json").write_text(
        json.dumps(incompatible_manifest(key)), encoding="utf-8"
    )
    return folder


def test_incompatible_new_plugin_not_launchable(tmp_path):
    folder = _write_release(tmp_path, "future_solver")
    active = {manifest["key"] for manifest in discover(tmp_path)}
    issues = incompatible_modules(tmp_path)
    assert "future_solver" not in active
    assert len(issues) == 1
    assert issues[0]["key"] == "future_solver"
    assert issues[0]["requires_core"] == ">=9.0.0"
    assert str(folder) not in sys.path


def test_incompatible_replacement_keeps_bundled_pile_available(tmp_path):
    folder = _write_release(tmp_path, "pile")
    active = {manifest["key"]: manifest for manifest in discover(tmp_path)}
    assert active["pile"]["version"] == "2026.0.0"
    assert active["pile"]["session"] == "slipsurface.pile.web.session"
    assert incompatible_modules(tmp_path)[0]["key"] == "pile"
    assert str(folder) not in sys.path


def test_home_displays_reason_without_opening_incompatible_plugin(monkeypatch):
    import slipsurface.desktop.home as home

    _ = QApplication.instance() or QApplication([])
    monkeypatch.setattr(
        home, "incompatible_modules",
        lambda: [dict(key="future_solver", name="Future Solver",
                      version="9.0.0", requires_core=">=9.0.0", core="0.1.0")],
    )
    dashboard = HomePage("tr")
    try:
        warnings = dashboard.findChildren(QLabel, "suiteIncompatibleBanner")
        assert len(warnings) == 1
        assert "future_solver" not in dashboard.cards
        assert ">=9.0.0" in warnings[0].text()
    finally:
        dashboard.close()


def test_failure_during_native_activation_rolls_back_and_preserves_old_page(monkeypatch):
    from slipsurface import installer

    _ = QApplication.instance() or QApplication([])
    window = MainWindow(language="tr", initial_app="bearing")
    old = window.current_page()
    called = []
    warnings = []
    monkeypatch.setattr(
        window, "_verify_updated_module",
        lambda _: (_ for _ in ()).throw(RuntimeError("candidate Qt failure")),
    )
    monkeypatch.setattr(
        installer, "rollback_release",
        lambda key, expected_version=None: called.append((key, expected_version)),
    )
    monkeypatch.setattr(
        QMessageBox, "warning",
        lambda *args, **kwargs: warnings.append(args[-1]),
    )
    window._update_task = object()
    try:
        window._update_installed({"key": "bearing", "version": "1.1.0"}, None)
        assert called == [("bearing", "1.1.0")]
        assert window.pages["bearing"] is old
        assert window.current_page() is old
        assert "geri dönüldü" in warnings[-1]
    finally:
        window.close()
