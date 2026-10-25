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

Only Python sources and main.py are used. No EXE, installer, PyInstaller, distribution package, release or web server.

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
