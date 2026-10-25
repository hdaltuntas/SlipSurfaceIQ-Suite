"""Corporate identity regression coverage for the native Qt application."""
from __future__ import annotations

import os
from xml.etree import ElementTree

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from slipsurface.desktop.app import MainWindow
from slipsurface.desktop.brand import (
    BRAND_ASSETS,
    BRAND_DESCRIPTOR,
    BRAND_NAME,
    PALETTE,
    application_icon,
    symbol_icon,
)
from slipsurface.desktop.splash import BrandSplash
from slipsurface.desktop.theme import stylesheet


def test_brand_assets_are_real_scalable_vector_marks():
    app = QApplication.instance() or QApplication([])
    for name in ("symbol.svg", "app_icon.svg"):
        path = BRAND_ASSETS / name
        assert path.is_file(), name
        root = ElementTree.parse(path).getroot()
        assert root.tag.endswith("svg")
        assert any(node.tag.endswith("path") for node in root.iter())
    assert not symbol_icon().pixmap(84, 108).isNull()
    assert not application_icon().pixmap(64, 64).isNull()
    assert BRAND_NAME == "SlipSurfaceIQ"
    assert "GEOTECHNICAL" in BRAND_DESCRIPTOR
    assert app is not None


def test_native_splash_renders_for_both_languages():
    app = QApplication.instance() or QApplication([])
    for language in ("tr", "en"):
        image = BrandSplash.render_artwork(language)
        assert image.width() == 900
        assert image.height() == 480
        assert not image.isNull()
        assert image.toImage().pixelColor(10, 10).isValid()
        splash = BrandSplash(language)
        try:
            assert splash.objectName() == "suiteBrandSplash"
            assert not splash.pixmap().isNull()
        finally:
            splash.close()
    assert app is not None


def test_brand_home_toolbar_and_all_module_headers_share_symbol():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(language="tr", theme="light")
    try:
        assert not window.windowIcon().isNull()
        assert window.home.brand_hero.objectName() == "suiteBrandHero"
        assert window.home.brand_hero.accessibleName() == BRAND_NAME
        assert not window.home.brand_mark.pixmap().isNull()
        assert window.home.brand_title.text() + window.home.brand_suffix.text() == BRAND_NAME
        assert "MODELLE" in window.home.brand_motto.text()
        assert window.toolbar_brand.text() == BRAND_NAME
        assert not window.toolbar_brand_mark.pixmap().isNull()
        for theme in ("light", "dark"):
            window.set_theme(theme)
            css = app.styleSheet()
            assert all(code in css for code in ("#00DDF5", "#6B4CFF", "#0B1529"))
            assert "suiteBrandHero" in css
            assert "suiteToolbarBrand" in css
            window.open_module("bearing")
            page = window.current_page()
            assert page is not None and page.key == "bearing"
            assert not page.header.brand_mark.pixmap().isNull()
            assert not page.header.icon_label.pixmap().isNull()
            window.show_home()
            assert window.home.brand_title.text() == "SlipSurface"
    finally:
        window.close()


def test_english_wordmark_and_startup_do_not_open_solver():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(language="en", theme="dark")
    try:
        assert "MODEL" in window.home.brand_motto.text()
        assert "ANALYZE" in window.home.brand_motto.text()
        assert window.home.brand_descriptor.text() == BRAND_DESCRIPTOR
        assert len(window.pages) == 0
        assert "suiteModuleCard" in stylesheet("dark")
        assert PALETTE["violet"] == "#B629F4"
    finally:
        window.close()
    assert app is not None
