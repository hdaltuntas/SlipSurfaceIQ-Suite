"""Nordic Dark: one native, accessible PySide6 design system.

The Suite deliberately has no light-mode stylesheet. Engineering reports and
printer/PDF charts remain controlled by their separate report renderers.
Qt's native widgets (not QWebEngine/HTML) share these stable object names.
"""
from __future__ import annotations

THEME_NAME = "Nordic Dark"

# Semantic UI tokens; avoid hardcoding surface colors in per-module editors.
COLORS = {
    "canvas": "#2B303B",
    "sidebar": "#303744",
    "surface": "#363E4D",
    "raised": "#414B5D",
    "input": "#262D39",
    "text": "#EDF1F7",
    "secondary": "#C2CCD9",
    "muted": "#B5C1CE",
    "border": "#586676",
    "accent": "#8FC9C3",
    "accent_hover": "#A9DEDA",
    "accent_text": "#17292E",
    "selected": "#385960",
    "ok": "#A3BE8C",
    "warning": "#EBCB8B",
    "error": "#E6949D",
}

# Stable, Qt-compatible QSS only (no unsupported browser backdrop filters).
NORDIC_DARK = """
QWidget {
    background: #2B303B;
    color: #EDF1F7;
    font-family: "Segoe UI";
    font-size: 12px;
}
QMainWindow, QSplitter, QScrollArea, QStackedWidget, QTabWidget::pane {
    background: #2B303B;
}
QMenuBar { background: #303744; color: #EDF1F7; padding: 2px 5px; }
QMenuBar::item { padding: 5px 11px; }
QMenuBar::item:selected, QMenuBar::item:pressed {
    background: #414B5D; color: #EDF1F7;
    border-radius: 5px;
}
QMenu { background: #363E4D; color: #EDF1F7; border: 1px solid #586676; }
QMenu::item { padding: 7px 22px 7px 16px; }
QMenu::item:selected { color: #EDF1F7; background: #385960; }
QMenu::separator { height: 1px; background: #586676; margin: 4px 8px; }
QStatusBar { background: #303744; color: #C2CCD9; border-top: 1px solid #586676; }
QToolTip { color: #EDF1F7; background: #414B5D; border: 1px solid #586676; padding: 5px; }
QPushButton {
    color: #EDF1F7; background: #414B5D;
    border: 1px solid #586676; border-radius: 8px;
    min-height: 25px; padding: 6px 12px;
}
QPushButton:hover { background: #506074; border-color: #8FC9C3; }
QPushButton:pressed { background: #385960; }
QPushButton:focus { border: 2px solid #8FC9C3; }
QPushButton:disabled { color: #9FAEBF; background: #353D4B; border-color: #485464; }
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
    color: #EDF1F7; background: #262D39;
    border: 1px solid #586676; border-radius: 7px;
    selection-background-color: #385960; selection-color: #FFFFFF;
    padding: 5px 8px; min-height: 24px;
}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus,
QTextEdit:focus, QPlainTextEdit:focus { border: 1px solid #8FC9C3; }
QComboBox QAbstractItemView {
    color: #EDF1F7; background: #303744;
    selection-background-color: #385960; selection-color: #FFFFFF;
    border: 1px solid #586676; outline: none;
}
QComboBox::drop-down { background: #363E4D; border: 0px; border-radius: 5px; width: 22px; }
QListWidget {
    color: #EDF1F7; background: #303744;
    border: 1px solid #465463; border-radius: 9px;
    outline: none;
}
QListWidget::item { padding: 10px 11px; border-radius: 5px; }
QListWidget::item:hover:!selected { background: #414B5D; }
QListWidget::item:selected { color: #EDF1F7; background: #385960; border-left: 3px solid #8FC9C3; }
QTabWidget::pane { border: 1px solid #586676; border-radius: 8px; background: #303744; }
QTabBar::tab {
    color: #C2CCD9; background: #303744;
    padding: 9px 14px; border: 1px solid #495769;
    border-bottom: 0px; border-top-left-radius: 7px; border-top-right-radius: 7px;
    margin-right: 3px;
}
QTabBar::tab:hover:!selected { color: #EDF1F7; background: #414B5D; }
QTabBar::tab:selected { color: #D9FAF5; background: #385960; border-color: #8FC9C3; }
QGroupBox {
    color: #EDF1F7; font-weight: 600; background: #363E4D;
    border: 1px solid #586676; border-radius: 9px;
    margin-top: 17px; padding: 12px 10px 8px 10px;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0px 7px; }
QTableWidget, QTableView {
    color: #EDF1F7; background: #303744;
    alternate-background-color: #363E4D;
    selection-background-color: #385960; selection-color: #FFFFFF;
    gridline-color: #4B5969; border: 1px solid #586676;
    border-radius: 7px;
}
QHeaderView::section {
    background: #414B5D; color: #EDF1F7;
    border: 0px; border-right: 1px solid #586676;
    border-bottom: 1px solid #586676; padding: 7px 9px;
}
QTableCornerButton::section { background: #414B5D; border: 1px solid #586676; }
QScrollBar:vertical { background: #2B303B; width: 12px; margin: 0px; }
QScrollBar::handle:vertical { background: #586676; border-radius: 5px; min-height: 28px; }
QScrollBar:horizontal { background: #2B303B; height: 12px; margin: 0px; }
QScrollBar::handle:horizontal { background: #586676; border-radius: 5px; min-width: 28px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0px; width: 0px; }
QScrollBar::add-page, QScrollBar::sub-page { background: none; }
QCheckBox { color: #EDF1F7; spacing: 8px; }
QCheckBox::indicator { width: 15px; height: 15px; }
QCheckBox::indicator:checked { background: #8FC9C3; border: 1px solid #8FC9C3; border-radius: 3px; }
QCheckBox::indicator:unchecked { background: #262D39; border: 1px solid #8D9BA9; border-radius: 3px; }
QProgressBar {
    color: #EDF1F7; background: #262D39; border: 1px solid #586676; border-radius: 5px;
}
QProgressBar::chunk { background: #8FC9C3; border-radius: 4px; }

/* All ten modules: dashboard, shared shell, forms and result containers. */
QWidget#suiteHomeBody, QScrollArea#suiteHomeScroll { background: #2B303B; }
QLabel#suiteHomeEyebrow, QLabel#suiteHomeHeading, QLabel#suiteHomeSubtitle,
QLabel#suiteToolbarMark, QLabel#suiteToolbarBrand, QLabel#suiteResultsHeading {
    background: transparent; border: none;
}
QLabel#suiteHomeEyebrow { color: #8FC9C3; font-size: 10px; font-weight: 700; }
QLabel#suiteHomeHeading { color: #EDF1F7; font-size: 25px; font-weight: 750; }
QLabel#suiteHomeSubtitle { color: #C2CCD9; font-size: 12px; }
QFrame#suiteBrandHero {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #262D39, stop:0.5 #303744, stop:1 #38505B);
    border: 1px solid #586676; border-radius: 16px;
}
QFrame#suiteBrandHero QLabel { background: transparent; border: none; }
QLabel#suiteBrandName { color: #EDF1F7; font-size: 29px; font-weight: 800; }
QLabel#suiteBrandIQ { color: #8FC9C3; font-size: 29px; font-weight: 800; }
QLabel#suiteBrandDescriptor { color: #C2CCD9; font-size: 11px; }
QLabel#suiteBrandMotto { color: #8FC9C3; font-weight: 700; font-size: 11px; }
QLabel#suiteBrandCategory { color: #C2CCD9; font-size: 11px; }
QFrame#suiteModuleCard {
    background: #363E4D; border: 1px solid #586676; border-radius: 12px;
}
QFrame#suiteModuleCard:hover, QFrame#suiteModuleCard:focus {
    background: #414B5D; border: 2px solid #8FC9C3;
}
QFrame#suiteModuleCard QLabel { background: transparent; border: none; }
QLabel#suiteCardCategory { color: #8FC9C3; font-size: 10px; font-weight: 700; }
QLabel#suiteCardIcon {
    background: #414B5D; border: 1px solid #586676; border-radius: 9px;
}
QLabel#suiteCardTitle { color: #EDF1F7; font-size: 17px; font-weight: 700; }
QLabel#suiteCardDescription { color: #C2CCD9; font-size: 12px; }
QLabel#suiteCardVersion { color: #B5C1CE; font-size: 10px; }
QPushButton#suiteCardLaunch {
    background: #385960; color: #D9FAF5; border: 1px solid #649E9B; font-weight: 700;
}
QPushButton#suiteCardLaunch:hover { background: #467078; }
QLabel#suiteCardUpdateBadge {
    background: #385960; color: #D9FAF5; border: 1px solid #8FC9C3;
    border-radius: 7px; padding: 3px 7px; font-size: 10px; font-weight: 700;
}
QLabel#suiteCardUpdateBadgeIncompatible {
    background: #594A44; color: #F7D7C5; border: 1px solid #EBCB8B;
    border-radius: 7px; padding: 3px 7px;
}
QPushButton#suiteCardUpdateInstall {
    background: #8FC9C3; color: #17292E; border-color: #8FC9C3; font-weight: 750;
}
QPushButton#suiteCardUpdateInstall:hover { background: #A9DEDA; }
QLabel#suiteUpdateBanner, QLabel#suiteIncompatibleBanner {
    background: #363E4D; color: #EDF1F7; border: 1px solid #586676;
    border-left: 3px solid #8FC9C3; border-radius: 7px; padding: 9px 12px;
}
QFrame#suiteWorkspaceToolbar {
    background: #303744; border: 1px solid #586676; border-radius: 11px;
}
QFrame#suiteWorkspaceToolbar QPushButton { min-height: 27px; }
QLabel#suiteToolbarBrand { color: #EDF1F7; font-size: 15px; font-weight: 800; }
QPushButton#suiteHomeBack { color: #EDF1F7; background: #414B5D; font-weight: 700; }
QPushButton#suiteLanguageSwitch, QPushButton#suiteCheckUpdates {
    color: #EDF1F7; background: #363E4D; border: 1px solid #586676;
}
QPushButton#suiteLanguageSwitch:hover, QPushButton#suiteCheckUpdates:hover {
    background: #385960; border-color: #8FC9C3;
}
QPushButton#suiteDocumentAction { padding: 6px 13px; }
QFrame#suiteModuleHeader {
    background: #363E4D; border: 1px solid #586676;
    border-left: 4px solid #8FC9C3; border-radius: 11px;
}
QFrame#suiteModuleHeader QLabel { background: transparent; border: none; }
QLabel#suiteModuleGroup { color: #8FC9C3; font-size: 10px; font-weight: 700; }
QLabel#suiteModuleHeading { color: #EDF1F7; font-size: 21px; font-weight: 750; }
QLabel#suiteModuleSubheading { color: #C2CCD9; font-size: 12px; }
QLabel#suiteModuleIcon {
    background: #414B5D; border: 1px solid #586676; border-radius: 9px;
}
QPushButton#suiteAnalyzeAction {
    background: #8FC9C3; color: #17292E; border: 1px solid #8FC9C3;
    font-weight: 750; padding: 8px 17px;
}
QPushButton#suiteAnalyzeAction:hover { background: #A9DEDA; }
QPushButton#suiteSpecialAction { color: #D9FAF5; background: #385960; border: 1px solid #649E9B; }
QLabel#suiteSectionHint {
    color: #C2CCD9; background: #363E4D;
    border: 1px solid #586676; border-radius: 7px; padding: 8px 11px;
}
QSplitter#suiteEditorSplitter::handle:horizontal { background: #586676; width: 8px; }
QSplitter#suiteEditorSplitter::handle:horizontal:hover { background: #8FC9C3; }
QTableWidget#suiteInputTable {
    background: #303744; alternate-background-color: #363E4D;
    selection-background-color: #385960; gridline-color: #586676;
}
QLabel#suiteResultsHeading { color: #EDF1F7; font-size: 17px; font-weight: 750; }
QLabel#suiteResultsHeadline { color: #C2CCD9; }
QFrame#suiteResultCard {
    background: #363E4D; border: 1px solid #586676; border-radius: 9px;
}
QFrame#suiteResultCard[checkState="ok"] { border-left: 4px solid #A3BE8C; }
QFrame#suiteResultCard[checkState="bad"] { border-left: 4px solid #E6949D; }
QFrame#suiteResultCard[checkState="warn"] { border-left: 4px solid #EBCB8B; }
QLabel#suiteMetricTitle { color: #C2CCD9; font-size: 11px; }
QLabel#suiteMetricValue { color: #EDF1F7; font-size: 20px; font-weight: 750; }
QLabel#suiteMetricDetail { color: #B5C1CE; }
QLabel#suiteResultWarnings {
    background: #594A44; border: 1px solid #EBCB8B;
    color: #F6DFB3; border-radius: 7px; padding: 9px;
}
QFrame#suiteResultTablePanel {
    background: #363E4D; border: 1px solid #586676; border-radius: 8px;
}
QLabel#suiteResultTableTitle { color: #C2CCD9; font-weight: 650; }

/* Data-first editing and display. The plot PNG is painted without recoloring
   its scientific legends; the dark panel is not an image filter. */
QWidget#suitePlotPanel, QScrollArea#suitePlotScroll {
    background: #303744;
}
QLabel#suitePlotCanvas {
    background: #262D39; color: #C2CCD9;
    border: 1px solid #586676; border-radius: 8px;
    padding: 8px;
}
QTextEdit#suiteResultDetails {
    background: #262D39; color: #EDF1F7;
    border: 1px solid #586676; padding: 12px;
    selection-background-color: #385960;
}
QScrollArea#suiteResultsScroll { background: #2B303B; }
QWidget#suiteResultsOverview { background: #2B303B; }
QTableWidget#suiteResultTable {
    background: #303744; alternate-background-color: #363E4D;
    gridline-color: #586676;
}
QPushButton#suiteAddRow, QPushButton#suiteDuplicateRow {
    background: #414B5D; color: #EDF1F7;
}
QPushButton#suiteRemoveRow {
    background: #493C43; border: 1px solid #996977; color: #F5DDE1;
}
QPushButton#suiteRemoveRow:hover { background: #594650; }
QLabel#suiteFieldUnit { color: #C2CCD9; background: transparent; }

/* About dialog shares one dark surface; licenses and links stay readable. */
QDialog#suiteAboutDialog { background: #2B303B; }
QFrame#suiteAboutHero {
    background: #303744; border: 1px solid #586676; border-radius: 12px;
}
QFrame#suiteAboutHero QLabel { background: transparent; border: none; }
QLabel#suiteAboutTitle { color: #EDF1F7; font-size: 21px; font-weight: 750; }
QLabel#suiteAboutDescriptor { color: #C2CCD9; }
QLabel#suiteAboutEdition { color: #8FC9C3; }
"""

def stylesheet(theme: str = "dark") -> str:
    """Return the sole application theme.

    A legacy request for 'light' is intentionally mapped to Nordic Dark:
    removing the visual mode must not crash older launch scripts/plugins.
    """
    return NORDIC_DARK
