# SlipSurfaceIQ Suite

Native Python / PySide6 geotechnical desktop application. Ten modules; LE excluded.

## Start

Requirements: Python 3.10+.

    python -m pip install -r requirements.txt
    python main.py

On launch, the application displays a **home dashboard** with ten cards, each containing a module name and a short description. Select a card to enter its engineering interface. Use **Tüm programlar / All applications** to return to the dashboard; existing module inputs remain available.

[Actual light theme dashboard](docs/screenshots/native-pyside6-home-light.png) · [Actual dark theme dashboard](docs/screenshots/native-pyside6-home-dark.png)

Options to bypass the home dashboard and open a module immediately:

    python main.py --lang tr --theme light --app bearing
    python main.py --lang en --theme dark --app rock

The desktop launcher uses only Python and main.py. There is no EXE, PyInstaller, Windows installer or web server. Optional **per-module** signed-catalogue ZIP archives are supported for updating an individual Python analysis module (see docs/UPDATE_CATALOGUE.md); these are not desktop installer packages.

## Corporate identity

The original neon S mark is integrated into the native PySide6 window icon,
short startup splash, dashboard, module headers and contrast-conscious light/dark
themes. See [Brand integration](docs/BRAND_INTEGRATION.md).

Use `python main.py --no-splash` to skip the splash. The existing `--app`
direct launch still works. No EXE, installer or web server is required.

## Interface

The home screen and all ten module workspaces use the same icon-led PySide6
visual language: [desktop design system](docs/UI_DESIGN_SYSTEM.md). Module
icons are scalable SVG files and appear on home cards, module tabs, sidebars
and module headers. Both light and dark themes are supported.

Current native screenshots:
[launchpad — light](docs/screenshots/native-pyside6-home-light.png) ·
[module — light](docs/screenshots/native-pyside6-bearing-light.png) ·
[launchpad — dark](docs/screenshots/native-pyside6-home-dark.png) ·
[module — dark](docs/screenshots/native-pyside6-bearing-dark.png).

## Tests

    python -m pip install -r requirements-dev.txt
    python -m compileall -q main.py slipsurface
    python -m pytest -q
    ruff check main.py slipsurface/apps.py slipsurface/desktop tests

Numerical smoke/regression coverage does not replace independent engineering validation.

## License

Proprietary; see LICENSE.
