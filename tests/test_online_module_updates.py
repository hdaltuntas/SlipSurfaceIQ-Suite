"""Online module catalogue is safe, bounded, and reflected on module cards."""
from __future__ import annotations

import io
import json
import os
from dataclasses import replace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from slipsurface.apps import catalogue
from slipsurface.desktop.app import MainWindow
from slipsurface.desktop.home import HomePage
from slipsurface.desktop import updater


def test_public_catalogue_maps_rock_to_a_card_update():
    installed = tuple(
        replace(app, version="2026.0.0") if app.key == "rock" else app
        for app in catalogue()
    )
    index = {
        "rock": {
            "version": "2026.0.1",
            "changelog": "D range corrected",
            "requires_core": ">=0.1.0",
            "url": "https://example.com/rock-2026.0.1.zip",
            "sha256": "a" * 64,
        },
    }
    updates = updater.check(index, apps=installed)
    assert set(updates) == {"rock"}
    assert updates["rock"].installed == "2026.0.0"
    _ = QApplication.instance() or QApplication([])
    home = HomePage("tr", updates)
    try:
        rock = home.cards["rock"]
        badge = rock.findChild(type(rock.launch_button), "suiteCardUpdateInstall")
        assert isinstance(badge, QPushButton)
        assert "Güncelle" in badge.text()
        assert "2026.0.1" in next(
            w.text() for w in rock.findChildren(type(home.brand_title))
            if w.objectName() == "suiteCardUpdateBadge"
        )
        assert home.findChild(type(home.brand_title), "suiteUpdateBanner") is not None
    finally:
        home.close()


class _Reply(io.BytesIO):
    def __init__(self, contents: bytes, url: str):
        super().__init__(contents)
        self.url = url

    def geturl(self):
        return self.url


def test_remote_catalogue_fetch_is_https_and_size_bounded(monkeypatch):
    url = updater.PUBLISHED_INDEX
    records = {"rock": {"version": "2026.0.1"}}
    payload = json.dumps(records).encode("utf-8")
    monkeypatch.setattr(updater.urllib.request, "urlopen",
                        lambda request, timeout: _Reply(payload, url))
    assert updater.read_published_index() == records
    with pytest.raises(ValueError, match="HTTPS"):
        updater.read_published_index("http://example.org/index.json")
    monkeypatch.setattr(
        updater.urllib.request, "urlopen",
        lambda request, timeout: _Reply(b"x" * (updater.MAX_INDEX_BYTES + 1), url),
    )
    with pytest.raises(ValueError, match="size"):
        updater.read_published_index()


def test_local_override_wins_and_offline_returns_no_updates(tmp_path, monkeypatch):
    user_index = tmp_path / "index.json"
    monkeypatch.setattr(updater, "INDEX_PATHS", (user_index,))
    monkeypatch.setattr(updater, "read_published_index",
                        lambda: {"pile": {"version": "2026.0.2"}})
    user_index.write_text(json.dumps({"rock": "2026.0.2"}), encoding="utf-8")
    assert set(updater.load_available_updates(include_remote=True)) == {"rock"}
    user_index.unlink()
    assert set(updater.load_available_updates(include_remote=True)) == {"pile"}
    def offline():
        raise OSError("network offline")
    monkeypatch.setattr(updater, "read_published_index", offline)
    assert updater.load_available_updates(include_remote=True) == {}


def test_async_update_result_refreshes_cards_without_leaving_home():
    _ = QApplication.instance() or QApplication([])
    window = MainWindow(language="tr", theme="light")
    try:
        assert window.stack.currentWidget() is window.home
        assert window.check_updates_button.isEnabled()
        installed = next(app for app in catalogue() if app.key == "rock").version
        offer = updater.AppUpdate(
            key="rock", installed=installed, latest="2026.0.2",
            changelog="New validated Rock version",
            url="https://example.com/rock.zip", sha256="b" * 64,
        )
        window._updates_checked({"rock": offer}, None)
        assert window.stack.currentWidget() is window.home
        assert "rock" in window.available_updates
        rock = window.home.cards["rock"]
        assert rock.findChild(QPushButton, "suiteCardUpdateInstall") is not None
        assert window.home.findChild(type(window.home.brand_title),
                                     "suiteUpdateBanner") is not None
        assert window.check_updates_button.isEnabled()
    finally:
        window.close()
