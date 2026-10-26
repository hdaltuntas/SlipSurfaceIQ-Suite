# SlipSurfaceIQ — Dark UI Spec v1.0

Status: **Phases A–B merged; C/D engineering workspace improvements implemented and under CI validation; E visual/regression review in progress.**
Reference: Nordic/KDE dark desktop example supplied for visual direction. 
Runtime: **native Python/PySide6 only**. No QWebEngine, browser, Electron or light theme.

## Principles

- Exactly **one** dark appearance (Nordic Dark); no theme switch in the toolbar or menus.
- Keep TR/EN language switching, update badges, Home navigation and all 10 engineering modules.
- Preserve solver inputs, engine/session state, numeric validation and project files.
- Mint is an *action/focus* accent, not a replacement for scientific plot legend encoding.
- Use opaque surfaces for tabular/canvas legibility. No blur over numbers, CAD grid or charts.
- Qt Fusion controls/QSS must remain readable and keyboard navigable on Windows.
- Generated PDFs and printable reports keep independent paper-readable chart styles.

## Design tokens

| Token | Hex | Usage |
| --- | --- | --- |
| Canvas | `#2B303B` | Main window, workspace background |
| Sidebar | `#303744` | Navigator, menu bar |
| Surface | `#363E4D` | Cards, form groups, module headers |
| Raised | `#414B5D` | Toolbar controls, hover states |
| Input | `#262D39` | Fields and read-only data |
| Text | `#EDF1F7` | Primary text |
| Secondary | `#C2CCD9` | Descriptions, table hints |
| Muted | `#B5C1CE` | Noncritical metadata |
| Border | `#586676` | Subtle separation |
| Accent | `#8FC9C3` | Primary actions, focus, updates |
| Accent hover | `#A9DEDA` | Interactive hover |
| Accent text | `#17292E` | Text on mint action backgrounds |
| Selected | `#385960` | Active tabs, navigator, selection |
| Success | `#A3BE8C` | Pass states |
| Warning | `#EBCB8B` | Caution, incomplete results |
| Error | `#E6949D` | Fail/error states |

Contrast checks using WCAG relative luminance:
- Primary text on canvas: ~11.7:1
- Secondary text on surface: ~6.6:1
- Muted text on raised surface: ~4.8:1
- Accent text on accent: ~8.1:1

## Components

1. **Global shell:** single toolbar (Home, check module updates, TR/EN, document actions); no theme action.
2. **Home dashboard:** 10 named SVG module cards, installed versions and available updates. Darkened brand hero retains the user-approved S mark.
3. **Workspace:** compact left-side module navigation, form/results adjustable split, clear active-state and focus.
4. **Forms:** bounded numeric spinboxes; min and max schema metadata must survive. Tabs, lists, selects, tables and scrollbars follow one palette.
5. **Results:** cards, metrics, warnings, detail text and tables use shared objects and contextual green/amber/red status.
6. **Reports/charts:** existing numerical data and print-oriented plot rendering left unchanged. Later chart-specific work must be benchmarked and compared independently.
7. **About/dialogs:** author, AGPL v3, libraries/licenses and version data remain visible with dark link contrast.
8. **Splash/icons:** subdued midnight-to-slate gradients and soft module strokes; approved multicolor S logo remains intact.

## Implementation stages

| Stage | Goal | Acceptance |
| --- | --- | --- |
| A | Single Nordic Dark QSS; remove light mode and theme button | All app entrypoints dark; no toggle or white default widgets |
| B | Style landing dashboard, toolbar, navigation, icons and splash | Each of 10 cards legible; versions and Update buttons preserved |
| C | Form/editor and result panel visual consistency | Inputs, table columns, focus, read-only and disabled states legible |
| D | Scientific charts and PDF/report appearance verification | No numerical changes; contrast on plot is tested; print remains paper-readable |
| E | Full regression/screenshot review | Windows/Linux CI, 10 native module screenshots, no failed input/project flows |

## Engineering QA guardrails

- This UI work is not a numerical validation or certification.
- Never rewrite project JSON, input conversion or analysis results for cosmetic consistency.
- Single dark mode applies to **the Suite desktop UI**; independent numerical PDF reports may
  remain white for printing. Their palette does not expose a user-selectable light UI theme.
- Older `MainWindow(theme="light")` or `set_theme("light")` callers fall back to dark safely;
  `python main.py --theme light` is no longer a supported CLI choice.
- Native screenshot generator only produces `*-dark.png`; the older light screenshots, if
  present in repository history, are archival and no longer the active design.
- App product version is independent from 10 module versions and the shared core ABI.


## C–E engineering workbench implementation

- Form rows wrap rather than overlap at narrow split widths. Labels have
  contextual tooltips and physical unit labels use a consistent muted style.
- Input table column widths are calibrated from field captions with horizontal
  scroll for multi-column SPT/CPT/soil and structural grids. Internal engine
  enum values and numeric serialization remain unchanged.
- Result tables remain read-only; captions have full tooltip texts and column
  widths no longer depend on a clipped last-column stretch.
- Chart preview stores the **original full-resolution PNG** and paints it
  proportional to the available viewport whenever resized. The canvas is dark,
  preserving the analysis engine's own dark plot theme without artificially
  recoloring legend/data pixels.
- Direct ModulePage creations explicitly use the desktop's dark plotting
  session, avoiding accidental light plots in plugin verification.
- Screenshot script captures all ten dark workspaces and an **actual
  calculated Bearing figure** (`native-pyside6-bearing-plot-dark.png`).
- Print/PDF exporters, analysis engines and numerical benchmarks are unmodified.
- Native Qt regressions verify cross-module form wrapping, original chart
  resolution after resizing, table scroll behavior, summary tables and colors.

**Evidence limit:** Passing offscreen Qt screenshot generation checks widget
rendering and existence of plots, not subjective visual perfection on every
Windows display scale. High-DPI and interactive inspection remain follow-up QA.
