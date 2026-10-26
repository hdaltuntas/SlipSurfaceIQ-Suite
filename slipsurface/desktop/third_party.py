"""Declared direct Python dependencies and their upstream license notices.

The original SlipSurfaceIQ code uses AGPL-3.0-only. These third-party packages
retain their separate licenses; do not represent them as AGPL-licensed.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version


@dataclass(frozen=True)
class Dependency:
    name: str
    distribution: str
    license: str
    purpose_tr: str
    purpose_en: str
    license_url: str
    development_only: bool = False

DEPENDENCIES = (
    Dependency("NumPy", "numpy", "BSD-3-Clause",
               "Sayısal diziler ve vektör işlemleri", "Numerical arrays and vectors",
               "https://numpy.org/doc/stable/license.html"),
    Dependency("SciPy", "scipy", "BSD-3-Clause",
               "Bilimsel hesaplama ve optimizasyon", "Scientific computing and optimization",
               "https://github.com/scipy/scipy/blob/main/LICENSE.txt"),
    Dependency("Matplotlib", "matplotlib", "Matplotlib License (PSF-derived)",
               "Mühendislik grafikleri ve görselleştirme", "Engineering plots and visualization",
               "https://matplotlib.org/stable/project/license.html"),
    Dependency("ReportLab", "reportlab", "BSD-style (ReportLab License)",
               "PDF raporları", "PDF report generation",
               "https://pypi.org/project/reportlab/"),
    Dependency("PySide6 Essentials", "PySide6_Essentials",
               "LGPLv3 / GPLv2 / GPLv3 / Commercial",
               "Yerel Qt masaüstü arayüzü", "Native Qt desktop user interface",
               "https://doc.qt.io/qtforpython-6/"),
    Dependency("Shiboken6", "shiboken6", "LGPLv3 / GPLv3 / Commercial",
               "Qt/Python bağlama altyapısı", "Qt/Python binding infrastructure",
               "https://doc.qt.io/qtforpython-6/"),
    Dependency("python-docx", "python-docx", "MIT",
               "Word belgeleri ve DOCX dışa aktarma", "Word documents and DOCX export",
               "https://github.com/python-openxml/python-docx/blob/master/LICENSE"),
    Dependency("openpyxl", "openpyxl", "MIT",
               "Excel elektronik tabloları", "Excel spreadsheet files",
               "https://pypi.org/project/openpyxl/"),
    Dependency("pytest", "pytest", "MIT",
               "Otomatik testler", "Automated tests",
               "https://github.com/pytest-dev/pytest/blob/main/LICENSE"),
    Dependency("Ruff", "ruff", "MIT",
               "Python kod denetimi", "Python source linting",
               "https://github.com/astral-sh/ruff/blob/main/LICENSE",
               development_only=True),
)

def dependency_version(item: Dependency) -> str:
    """Show the actually installed version, not a made-up pinned release."""
    try:
        return version(item.distribution)
    except PackageNotFoundError:
        return "—"

def python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
