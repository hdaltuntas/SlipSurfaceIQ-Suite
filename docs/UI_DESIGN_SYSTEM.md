# SlipSurfaceIQ Suite — Desktop Design System

## Scope

All ten desktop engineering modules use **one native PySide6 design system**.
The existing numerical models, configuration dictionaries, analysis sessions,
JSON project files and scientific result generation remain separate from presentation.
LE is deliberately excluded. The sole startup command remains `python main.py`.

## Shared components

- `slipsurface/desktop/theme.py`: common contrast-tested light/dark QSS styles.
  It styles menus, controls, cards, tabs, group boxes, navigator and module toolbars.
- `slipsurface/desktop/widgets.py`: reusable `ModuleHeader` displaying program
  SVG, category, localized program title and concise description, followed by
  module-specific actions.
- `slipsurface/desktop/icons.py`: single validated Qt `QIcon` provider.
- `slipsurface/desktop/assets/icons/*.svg`: 10 native scalable vector icons.
  Icons are displayed in dashboard cards, sidebar entries, open module tabs and
  the module header. Paths use the same program keys as `slipsurface/apps.py`.
- `slipsurface/desktop/home.py`: card-based launcher, keyboard-accessible.
- `slipsurface/desktop/app.py`: common workspace, navigation, actions and
  framework-independent module adapters. Shared toolbar and common forms.
- `slipsurface/apps.py`: English and Turkish name/description registry.

## Visual conventions

A desktop-ready hierarchy: navigation toolbar (Home / New / Open / Save / PDF),
then module identity and Analyze action, followed by editable input groups on
the left and result/plot tabs on the right. Muted pale-blue backgrounds for light
mode; high-contrast dark blue surfaces for dark mode. Buttons have explicit hover,
keyboard focus and disabled states. Engineering charts are produced by the
existing Matplotlib engines, not replaced by decorative graphics.

## Program icon semantics

| Key | SVG symbol |
| --- | --- |
| kinematic | joint planes / stereonet |
| rock | faceted rock mass |
| bearing | strip footing with bearing stress |
| settle | layer movements and downward arrows |
| correlation | scatter plot / fitted relation |
| liquefaction | pore-water wave / soil layers |
| pile | embedded pile and soil interface |
| spwa | anchored retaining pile wall |
| msew | reinforced soil layers |
| wall | reinforced cantilever wall section |

Each program keeps its engineering context with one icon regardless of where it
appears. Assets are repository text files; no browser or external icon fonts.

## Verification

Run:

    python -m pip install -r requirements-dev.txt
    python -m pytest -q
    ruff check main.py slipsurface/apps.py slipsurface/desktop tests

Qt headless screenshot capture: `python scripts/capture_native_ui.py`.
The CI checks cover all ten module headers and vector icons. Separate
engineering benchmark validation is still required for design-critical work.

## Next design backlog

1. Per-module data-table input ergonomics, validation feedback and specialized
   editors (soil layers, CPT/SPT series, anchors, reinforcement).
2. Unified engineering result summary cards, warning banners and report toolbar.
3. CAD-style scalable visualization, properties and drawing tools where applicable.

These changes must not alter underlying numerical algorithms without benchmark
tests and engineering review.
