"""Inactive core-incompatible plugins stay discoverable but never executable."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from slipsurface import CORE_VERSION, apps
from slipsurface.desktop.app import MainWindow
from slipsurface.registry import load_manifest


def test_incompatible_core_is_marked_on_catalogue_entry():
    plugin = load_manifest({
        "key": "future_solver",
        "name": "Future Solver",
        "tr": "Gelecek Çözücü",
        "group": "Foundations",
        "description": "Experimental external plugin",
        "description_tr": "Yeni nesil harici çözücü",
        "version": "2.0.0",
        "requires_core": ">=99.0.0",
        "session": "future_solver.web.session",
    })
    assert CORE_VERSION != "99.0.0"
    candidate = apps._from_manifest(plugin)
    assert not candidate.compatible
    assert candidate.requires_core == ">=99.0.0"


def test_incompatible_module_is_visible_but_disabled(monkeypatch):
    _ = QApplication.instance() or QApplication([])
    plugin = apps.App(
        key="future_solver", name="Future Solver", tr="Gelecek Çözücü",
        group="Foundations", description="External engineering module",
        description_tr="Harici mühendislik modülü",
        version="2.0.0", requires_core=">=99.0.0",
        session="future_solver.web.session", compatible=False,
    )
    monkeypatch.setattr(apps, "APPS", (*apps.APPS, plugin))
    monkeypatch.setitem(apps._BY_KEY, plugin.key, plugin)
    window = MainWindow("tr", "light")
    seen = []
    warnings = []
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args, **kwargs: warnings.append(args[-1]),
    )
    try:
        card = window.home.cards["future_solver"]
        card.activated.connect(seen.append)
        assert not card.launch_button.isEnabled()
        assert "Uyumsuz" in card.toolTip()
        card.activate()
        assert seen == []
        matches = [
            window.navigator.item(i) for i in range(window.navigator.count())
            if window.navigator.item(i).data(Qt.ItemDataRole.UserRole) == plugin.key
        ]
        assert len(matches) == 1
        assert not (matches[0].flags() & Qt.ItemFlag.ItemIsEnabled)
        window.open_module(plugin.key)
        assert warnings
        assert plugin.key not in window.pages
        assert window.current_page() is None
    finally:
        window.close()
