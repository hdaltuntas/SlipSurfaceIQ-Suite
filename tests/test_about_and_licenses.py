"""Release identity, AGPL notices and the native bilingual About dialog."""
from __future__ import annotations

import importlib
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialogButtonBox

from slipsurface import CORE_VERSION, __version__
from slipsurface.apps import catalogue
from slipsurface.desktop.about import AboutDialog
from slipsurface.desktop.app import MainWindow
from slipsurface.desktop.third_party import DEPENDENCIES, dependency_version
from slipsurface.versioning import module_version


def test_suite_and_each_module_have_separate_manifest_versions():
    assert __version__ == "2026.0.0"
    assert CORE_VERSION == "0.1.0"  # ABI separate from product release numbering
    assert len(catalogue()) == 10
    for module in catalogue():
        assert module.version == ("2026.0.1" if module.key == "rock" else "2026.0.0"), module.key
        package = importlib.import_module(f"slipsurface.{module.key}")
        assert package.__version__ == module.version
        assert module_version(package.__file__) == module.version


def test_license_is_full_agpl_v3_and_copyright_notice():
    root = Path(__file__).resolve().parents[1]
    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    notice = (root / "NOTICE").read_text(encoding="utf-8")
    deps = (root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert license_text.startswith("GNU AFFERO GENERAL PUBLIC LICENSE")
    assert "Version 3, 19 November 2007" in license_text
    assert len(license_text) > 30000
    assert "Hasan Deniz Altuntaş" in notice
    assert "AGPL-3.0-only" in notice
    assert "LGPLv3" in deps and "MIT" in deps and "BSD-3-Clause" in deps


def test_native_about_dialog_shows_author_modules_library_credits_in_both_languages():
    app = QApplication.instance() or QApplication([])
    for lang in ("tr", "en"):
        window = MainWindow(language=lang)
        dialog = AboutDialog(lang, window)
        try:
            assert dialog.module_table.rowCount() == len(catalogue())
            assert dialog.library_table.rowCount() == len(DEPENDENCIES) + 1
            assert "Hasan Deniz Altuntaş" in dialog.overview.toPlainText()
            assert "AGPL-3.0-only" in dialog.overview.toPlainText()
            assert "2026.0.0" in dialog.overview.toPlainText()
            assert "0.1.0" in dialog.overview.toPlainText()
            assert dialog.module_table.item(0, 1).text() == "2026.0.0"
            rock_index = next(i for i, module in enumerate(catalogue()) if module.key == "rock")
            assert dialog.module_table.item(rock_index, 1).text() == "2026.0.1"
            assert dialog.library_table.item(0, 0).text() == "Python"
            assert dialog.close_buttons.button(
                QDialogButtonBox.StandardButton.Close
            ) is not None
            assert window.about_action.objectName() == "suiteAboutAction"
            captions = [a.text() for a in window.menuBar().actions()]
            assert ("Yardım" if lang == "tr" else "Help") in captions
        finally:
            dialog.close()
            window.close()
    assert app is not None


def test_dependencies_have_license_metadata_and_runtime_versions():
    assert len(DEPENDENCIES) >= 9
    observed = {item.name: item.license for item in DEPENDENCIES}
    assert observed["NumPy"] == "BSD-3-Clause"
    assert observed["SciPy"] == "BSD-3-Clause"
    assert observed["python-docx"] == "MIT"
    assert "LGPLv3" in observed["PySide6 Essentials"]
    for dependency in DEPENDENCIES:
        assert dependency.license_url.startswith("https://")
        assert dependency.purpose_tr and dependency.purpose_en
        assert isinstance(dependency_version(dependency), str)
