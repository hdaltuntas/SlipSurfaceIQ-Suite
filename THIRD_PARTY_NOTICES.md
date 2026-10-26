# Third-party software and licenses

SlipSurfaceIQ Suite's **original source code** is licensed under the
[GNU Affero General Public License, Version 3 only](LICENSE)
(SPDX identifier: \`AGPL-3.0-only\`).
Copyright © 2026 **Hasan Deniz Altuntaş**.

The libraries below are independently developed and retain their own
copyrights and license terms. SlipSurfaceIQ does **not** relicense their
source code. The table covers the direct requirements in \`requirements.txt\`,
the primary PySide6 binding dependency and the developer tools listed in
\`requirements-dev.txt\`.

| Library | License | Purpose | Upstream license / notices |
| --- | --- | --- | --- |
| Python | PSF License 2.0 | Language runtime | https://docs.python.org/3/license.html |
| NumPy | BSD-3-Clause | Numerical arrays and vector operations | https://numpy.org/doc/stable/license.html |
| SciPy | BSD-3-Clause | Scientific computing and optimization | https://github.com/scipy/scipy/blob/main/LICENSE.txt |
| Matplotlib | Matplotlib License (PSF-derived) | Scientific plots and figures | https://matplotlib.org/stable/project/license.html |
| ReportLab | BSD-style ReportLab license | PDF reports | https://pypi.org/project/reportlab/ |
| PySide6 Essentials | LGPLv3 / GPLv2 / GPLv3 / commercial | Native desktop GUI | https://doc.qt.io/qtforpython-6/ |
| Shiboken6 | LGPLv3 / GPLv3 / commercial | Qt/Python binding layer | https://doc.qt.io/qtforpython-6/ |
| python-docx | MIT | Word documents | https://github.com/python-openxml/python-docx/blob/master/LICENSE |
| openpyxl | MIT | Excel files | https://pypi.org/project/openpyxl/ |
| pytest (development) | MIT | Tests | https://github.com/pytest-dev/pytest/blob/main/LICENSE |
| Ruff (development) | MIT | Source linting | https://github.com/astral-sh/ruff/blob/main/LICENSE |

**Important:** The license options for PySide6 and Shiboken6 describe the
vendor's alternative licensing models, **not** simultaneous application of
every license. The Qt components and bundled native libraries can have their
own notices, and Matplotlib/NumPy/SciPy likewise contain third-party
components. Read the actual licenses shipped with the installed wheel
versions before redistribution. In particular, Qt LGPLv3 redistribution
requirements must be assessed for the chosen distribution arrangement.

Actual installed dependency versions are displayed in the application's
**Help / Yardım → About / Hakkında → Libraries / Kütüphaneler** tab.
This is a summary for identification and is **not** a complete dependency
SBOM or a substitute for the upstream license text.

Licensing sources are controlled by their upstream rights holders; no
license or trademark of a third party is claimed as SlipSurfaceIQ property.
