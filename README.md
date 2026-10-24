# SlipSurfaceIQ Suite

Native Python / PySide6 geotechnical desktop application. Ten modules; LE excluded.

## Start

Requirements: Python 3.10+.

    python -m pip install -r requirements.txt
    python main.py

Options:

    python main.py --lang tr --theme light --app bearing
    python main.py --lang en --theme dark --app rock

Only Python sources and main.py are used. No EXE, installer, PyInstaller, distribution package, release or web server.

## Tests

    python -m pip install -r requirements-dev.txt
    python -m compileall -q main.py slipsurface
    python -m pytest -q
    ruff check main.py slipsurface/apps.py slipsurface/desktop tests

Numerical smoke/regression coverage does not replace independent engineering validation.

## License

Proprietary; see LICENSE.
