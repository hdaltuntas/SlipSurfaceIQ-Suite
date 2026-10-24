# Migration record

Source: hdaltuntas/slipsurface_iq (private, main)
Destination: hdaltuntas/SlipSurfaceIQ-Suite
Scope: 10 modules (all except LE).

- Preserved Python calculation engines, input schemas, studies, report generation and stateless analysis-session adapters.
- Excluded: slipsurface.le, the legacy hub, standalone FastAPI service, browser HTTP handlers, HTML/CSS/JS static assets, deployment credentials and hosting configuration.
- Added a PySide6 native shell launched by main.py.
- Retained the proprietary source licence. No external open-source re-licensing is implied.
- Existing source is not deleted to avoid losing history before numerical verification.
- Desktop workflows and packaging require QA before a versioned GitHub release.

Known engineering QA gates:
1. Validate representative numerical benchmarks for all 10 engines.
2. Verify project-file open/save round trips and table editors for every module.
3. Verify light/dark menu contrast and native CAD-style workspace usability.
4. Build Windows executable and inspect distributed third-party licences.
5. Confirm graphics and PDF exports in a packaged build.
