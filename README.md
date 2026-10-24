# SlipSurfaceIQ Suite

**Native Python / PySide6 desktop package for geotechnical and rock engineering.**

The suite brings 10 analysis modules from the legacy SlipSurface IQ monorepo into one native Qt desktop application. **LE is intentionally excluded**; the legacy web/HTTP frontend is not part of the desktop package.

## Modules

| Group | Modules |
| --- | --- |
| Rock mechanics | Kinematic, Rock |
| Foundations | Bearing, Settle, Correlation, Liquefaction, Pile |
| Retaining structures | Pile Wall Analysis (SPWA), MSEW, Wall |

The original Python numerical models, metadata-driven input forms, reporting functions and analysis sessions are preserved. The UI uses PySide6 widgets (not a browser wrapper). Some specialist workflows, including kinematic probability studies, are being integrated into the new desktop workspace; existing computation APIs remain available in Python.

## Run from source

Python 3.10+ is required.

    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # Linux/macOS:
    # source .venv/bin/activate
    python -m pip install -e .
    python main.py

Optional startup settings:

    python main.py --lang tr --theme light --app bearing
    python main.py --lang en --theme dark --app rock

No web server, HTTP port or JavaScript UI is required. The main window has native menus, a module navigator, editable input forms, data tables, analyses and PNG result figures. Projects save as JSON with their existing module-specific structure where supported.

## Build and QA

    python -m pip install -e ".[dev]"
    python -m compileall -q slipsurface main.py
    pytest -q
    ruff check main.py slipsurface/apps.py slipsurface/desktop tests

A Windows executable can be built using the workflow under .github/workflows/windows-package.yml. Build artifacts are **not** validated public releases. Do not mark an engineering build production-ready before numerical regressions and end-user acceptance have passed.

## Licensing

Proprietary; see LICENSE. Publishing the source repository does not grant redistribution or relicensing rights.
