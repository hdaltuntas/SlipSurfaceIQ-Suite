# SlipSurfaceIQ Suite — Desktop Design System

## Scope

All ten desktop engineering modules use **one native PySide6 design system**.
The existing numerical models, configuration dictionaries, analysis sessions,
JSON project files and scientific result generation remain separate from presentation.
LE is deliberately excluded. The sole startup command remains `python main.py`.

## Shared components

- `slipsurface/desktop/theme.py`: the single contrast-tested Nordic Dark QSS.
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
the left and result/plot tabs on the right. Nordic Dark uses layered slate
surfaces and mint accents, with explicit hover, keyboard focus and disabled
states. Engineering charts are produced by the existing Matplotlib engines,
not replaced by decorative graphics.

## Persistent application shell (2026)

The native **Home / Ana Sayfa** and **Language / Dil** buttons remain
visible on the shared header across the launcher and engineering modules.
There is no theme button; Nordic Dark is fixed. Language switches between Turkish and English and
relocalizes the launcher, module headers, form schemas, menus and navigation.

Language switching rebuilds the Qt form widgets while retaining the existing
engineering session objects, entered inputs, analysis results, plots and PDF
report capability. Running analyses or module updates block the switch so the
background task cannot be orphaned. Results that were computed before changing
the language remain in their original calculation language until recomputed.

The form editor/plot splitter begins at a **40/60** allocation rather than
giving the widest pane to a form with few fields. Users can still drag the
divider. Form groups have a maximum width and less cramped label columns, so
small parameter sets no longer spread across the full canvas. The numerical
engines and project formats are unchanged.

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


## Module workspace migration — completed in registry order

The same native PySide6 framework now includes a localized contextual input
guide, engineering-specific primary section, typed data grids and structured
result summary for every listed module. Engine calculations are unchanged.

| Order | Module | Primary editor | Specialized native action |
| --- | --- | --- | --- |
| 1 | Kinematic | Kinematic screening / failure mode | Screening, planar/wedge/toppling selection |
| 2 | Rock | Intact-rock inputs | Hoek–Brown summary |
| 3 | Bearing | Footing geometry / loading | Bearing factor-of-safety summary |
| 4 | Settle | Foundation / consolidation | Settlement indicators |
| 5 | Correlation | SPT/CPT/laboratory tests | Export projects to Settle and Bearing |
| 6 | Liquefaction | Site and earthquake data | SPT/CPT assessment |
| 7 | Pile | Pile geometry | Separate rock-socket calculation |
| 8 | SPWA | Retaining structure | Soil and anchor tables |
| 9 | MSEW | Wall geometry | Generate reinforcement layers with confirmation |
| 10 | Wall | Retaining-wall geometry | Suggest preliminary dimensions |

All ten screens share:

- validated SVG module icons and navigation;
- Nordic Dark contrast and keyboard-accessible controls;
- input groups, select-type table columns and row management;
- summary KPIs, warnings, read-only result tables and original plots;
- a document/action toolbar, status bar and Home navigation.

Generated screenshots from the running Qt application are stored in
`docs/screenshots/modules/{module}-dark.png`. The screenshots document
the **uncomputed default input state**, not validated engineering designs.

## Engineering QA boundaries

The GUI migration does not certify each solver for new design scenarios.
Original numerical regressions remain included, and numerical validation
against external references is tracked separately. The Suite remains Python-only:
`python main.py`. No installers, executables or Releases are created.

## Nordic Dark single-theme migration

The prior light/dark application chrome is replaced by one shared Nordic Dark
QSS. See [Dark UI Spec v1](DARK_UI_SPEC_V1.md) for exact tokens, accessible
focus/contrast rules, CAD and plot considerations, and staged acceptance.
Report/PDF paper figures are independent of on-screen application chrome.

## Engineering workbench C/D/E

Input forms now use responsive `QFormLayout.WrapLongRows`, physical-unit labels,
readable headers and horizontally scrollable tables. The results panel keeps
engineering captions intact; the dark plot viewer fits the **original PNG** to
the current workbench without changing saved reports or solver data.
The headless screenshot workflow captures the ten default module screens and
a calculated Bearing chart. See [Dark UI Spec v1](DARK_UI_SPEC_V1.md).
