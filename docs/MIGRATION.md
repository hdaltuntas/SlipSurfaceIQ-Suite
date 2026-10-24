# Migration record

Source: hdaltuntas/slipsurface_iq (private). Destination: hdaltuntas/SlipSurfaceIQ-Suite.

- LE excluded; ten engineering Python modules transferred.
- Native PySide6 GUI launches only with python main.py.
- Existing web/session.py are local Python session adapters, not servers; HTTP server packages excluded.
- No EXE files, PyInstaller, Windows package workflow, installers, or release publishing.
- Install dependencies from requirements.txt; run regression tests from requirements-dev.txt.
- Proprietary license retained and source repository unchanged.

Outstanding: independent engineering numerical benchmarks, end-user GUI verification and comprehensive project/report round trips.
