"""SlipSurfaceIQ Suite common light/dark native PySide6 design system.

Centralized QSS for cards, menu contrast, inputs, navigators, module headers,
analysis panels and other widgets. No HTML/CSS web runtime is involved.
"""

LIGHT = """
QWidget { background: #f6f8fc; color: #19263a; font-size: 12px; }
QMainWindow, QSplitter, QScrollArea, QTabWidget::pane { background: #f6f8fc; }
QMenuBar, QMenu { background: #ffffff; color: #19263a; }
QMenuBar::item:selected, QMenu::item:selected { background: #dce8fc; color: #10203c; }
QPushButton { background: #ecf2fb; color: #152743; border: 1px solid #b9c8db;
              border-radius: 5px; padding: 7px 13px; }
QPushButton:hover { background: #d4e4fb; }
QPushButton:disabled { color: #7d8997; background: #e8ecf2; }
QLineEdit, QDoubleSpinBox, QComboBox, QTableWidget, QTextEdit {
    color: #162537; background: #ffffff; border: 1px solid #c3cddb;
    border-radius: 4px; padding: 3px;
}
QListWidget { color: #1a2941; background: #edf2f9; border: none; }
QListWidget::item { padding: 9px; }
QListWidget::item:selected { color: #ffffff; background: #225eaa; }
QHeaderView::section { background: #e7edf7; color: #1a2941; padding: 5px; }
QTabBar::tab { background: #e7edf6; color: #283b54; padding: 8px 12px; }
QTabBar::tab:selected { background: #ffffff; color: #12549f; }
QGroupBox { border: 1px solid #cbd5e3; border-radius: 5px; margin-top: 14px;
            padding-top: 8px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; }
QToolTip { background: white; color: #19263a; }

QWidget#suiteHomeBody, QScrollArea#suiteHomeScroll { background: #f6f8fc; }
QLabel#suiteHomeEyebrow { color: #3264a2; font-weight: 700; font-size: 11px; letter-spacing: 1px; }
QLabel#suiteHomeHeading { color: #182d49; font-size: 29px; font-weight: 750; }
QLabel#suiteHomeSubtitle { color: #536781; font-size: 14px; }
QFrame#suiteModuleCard { background: #ffffff; border: 1px solid #ced9e6; border-radius: 13px; }
QFrame#suiteModuleCard:hover, QFrame#suiteModuleCard:focus { border: 2px solid #2c70bf; background: #fafdff; }
QFrame#suiteModuleCard QLabel { background: transparent; border: none; }
QLabel#suiteCardCategory { color: #376eaa; font-size: 10px; font-weight: 700; }
QLabel#suiteCardIcon { background: #eaf2ff; border: 1px solid #cadcf2; border-radius: 11px; }
QLabel#suiteCardTitle { color: #192d49; font-size: 17px; font-weight: 700; }
QLabel#suiteCardDescription { color: #586a81; font-size: 12px; }
QPushButton#suiteCardLaunch { background: #eaf2ff; color: #14549e; border: 1px solid #cadef6; padding: 5px 13px; font-weight: 650; }
QPushButton#suiteCardLaunch:hover { background: #d2e5ff; }
QPushButton#suiteHomeBack { background: #eaf2ff; color: #14549e; border: 1px solid #cadef6; font-weight: 650; }
QLabel#suiteCardVersion { color: #7b8ca3; font-size: 10px; }
QLabel#suiteCardUpdateBadge { background: #fff3d9; color: #8a6416; border: 1px solid #ebca81;
    border-radius: 8px; padding: 2px 8px; font-size: 10px; font-weight: 700; }
QLabel#suiteCardUpdateBadgeIncompatible { background: #fdeae6; color: #a04a30; border: 1px solid #eab9a5;
    border-radius: 8px; padding: 2px 8px; font-size: 10px; font-weight: 700; }
QPushButton#suiteCardUpdateInstall { background: #1c9568; color: #ffffff; border: 1px solid #15754f;
    border-radius: 8px; padding: 3px 12px; font-size: 10px; font-weight: 700; }
QPushButton#suiteCardUpdateInstall:hover { background: #157a52; }
QLabel#suiteUpdateBanner { background: #eaf6ff; color: #14549e; border: 1px solid #b7d9f5;
    border-radius: 9px; padding: 10px 14px; font-weight: 650; }



/* Shared native workspace components */
QFrame#suiteModuleHeader { border: 1px solid #cdd9e8; border-radius: 12px;
                           background: #ffffff; }
QFrame#suiteModuleHeader QLabel { background: transparent; border: none; }
QLabel#suiteModuleHeading { font-size: 21px; font-weight: 750; color: #19314f; }
QLabel#suiteModuleSubheading { font-size: 12px; color: #607188; }
QLabel#suiteModuleGroup { font-size: 10px; font-weight: 700; color: #2563a7; }
QLabel#suiteModuleIcon { background: #edf5ff; border: 1px solid #cde1fb; border-radius: 10px; }
QGroupBox { background: #ffffff; border: 1px solid #cdd9e8; border-radius: 9px;
            margin-top: 16px; padding: 12px 8px 6px 8px; }
QGroupBox::title { left: 12px; padding: 0 5px; }
QFrame#suiteWorkspaceToolbar { background: #ffffff; border: 1px solid #cdd9e8;
                                border-radius: 10px; }
QFrame#suiteWorkspaceToolbar QPushButton { min-height: 22px; }
QPushButton#suiteAnalyzeAction { background: #2169bb; color: #ffffff; border-color: #16559c; font-weight: 700; padding: 9px 18px; }
QTabWidget::pane { border: 1px solid #cdd9e8; border-radius: 4px; }
QPushButton:focus { border: 2px solid #367ac8; }
QListWidget::item:hover:!selected { background: #deebfa; }


/* Results summary shared across every module */
QLabel#suiteResultsHeading { color: #173451; font-weight: 750; font-size: 17px; }
QLabel#suiteResultsHeadline { color: #375b82; font-size: 12px; }
QFrame#suiteResultCard { background: #ffffff; border: 1px solid #cddaea; border-radius: 10px; }
QLabel#suiteMetricTitle { color: #526985; font-size: 11px; }
QLabel#suiteMetricValue { color: #153b66; font-size: 20px; font-weight: 750; }
QLabel#suiteMetricDetail { color: #64788e; font-size: 10px; }
QFrame#suiteResultCard[checkState="ok"] { border-left: 4px solid #1c9568; }
QFrame#suiteResultCard[checkState="bad"] { border-left: 4px solid #c25d43; }
QFrame#suiteResultCard[checkState="warn"] { border-left: 4px solid #be862d; }
QLabel#suiteResultWarnings { background: #fff3d9; border: 1px solid #ebca81;
    border-radius: 7px; padding: 10px; color: #684614; }
QFrame#suiteResultTablePanel { background: #ffffff; border: 1px solid #cddaea;
    border-radius: 8px; }
QLabel#suiteResultTableTitle { color: #294b71; font-weight: 650; }


QLabel#suiteSectionHint { background: #eaf2fb; color: #385d85;
    border: 1px solid #d6e4f4; border-radius: 6px; padding: 9px 12px; }
QTableWidget#suiteInputTable { selection-background-color: #d9e9fa;
    alternate-background-color: #f3f7fc; gridline-color: #dbe5f1; }
QPushButton#suiteSpecialAction { background: #edf3fb; color: #164e83;
    border: 1px solid #b8d0eb; font-weight: 650; }

"""

DARK = """
QWidget { background: #1a2331; color: #e8eef8; font-size: 12px; }
QMainWindow, QSplitter, QScrollArea, QTabWidget::pane { background: #1a2331; }
QMenuBar, QMenu { background: #242f41; color: #edf3fa; }
QMenuBar::item:selected, QMenu::item:selected { background: #385277; color: white; }
QPushButton { background: #2d405b; color: #eff5fc; border: 1px solid #4b6383;
              border-radius: 5px; padding: 7px 13px; }
QPushButton:hover { background: #40608a; }
QPushButton:disabled { color: #8a9bac; background: #2a3544; }
QLineEdit, QDoubleSpinBox, QComboBox, QTableWidget, QTextEdit {
    color: #f1f5fb; background: #243247; border: 1px solid #4b607b;
    border-radius: 4px; padding: 3px;
}
QListWidget { color: #e6eef8; background: #222f41; border: none; }
QListWidget::item { padding: 9px; }
QListWidget::item:selected { color: white; background: #2f609b; }
QHeaderView::section { background: #314158; color: #edf3fa; padding: 5px; }
QTabBar::tab { background: #2a3c52; color: #dbe6f4; padding: 8px 12px; }
QTabBar::tab:selected { background: #405b7e; color: white; }
QGroupBox { border: 1px solid #4b607b; border-radius: 5px; margin-top: 14px;
            padding-top: 8px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; }
QToolTip { background: #30415a; color: white; }

QWidget#suiteHomeBody, QScrollArea#suiteHomeScroll { background: #1a2331; }
QLabel#suiteHomeEyebrow { color: #87b6fc; font-weight: 700; font-size: 11px; letter-spacing: 1px; }
QLabel#suiteHomeHeading { color: #f2f6fd; font-size: 29px; font-weight: 750; }
QLabel#suiteHomeSubtitle { color: #adbed4; font-size: 14px; }
QFrame#suiteModuleCard { background: #26354a; border: 1px solid #425873; border-radius: 13px; }
QFrame#suiteModuleCard:hover, QFrame#suiteModuleCard:focus { border: 2px solid #82b6ff; background: #2d4058; }
QFrame#suiteModuleCard QLabel { background: transparent; border: none; }
QLabel#suiteCardCategory { color: #95c3ff; font-size: 10px; font-weight: 700; }
QLabel#suiteCardIcon { background: #344762; border: 1px solid #537098; border-radius: 11px; }
QLabel#suiteCardTitle { color: #f0f5fc; font-size: 17px; font-weight: 700; }
QLabel#suiteCardDescription { color: #b4c5dc; font-size: 12px; }
QPushButton#suiteCardLaunch { background: #354e70; color: #e0edff; border: 1px solid #54729d; padding: 5px 13px; font-weight: 650; }
QPushButton#suiteCardLaunch:hover { background: #446a9d; }
QPushButton#suiteHomeBack { background: #354e70; color: #e0edff; border: 1px solid #54729d; font-weight: 650; }
QLabel#suiteCardVersion { color: #8fa4bd; font-size: 10px; }
QLabel#suiteCardUpdateBadge { background: #4d3b28; color: #ffe9bf; border: 1px solid #8f7646;
    border-radius: 8px; padding: 2px 8px; font-size: 10px; font-weight: 700; }
QLabel#suiteCardUpdateBadgeIncompatible { background: #4a2e26; color: #ffc9b8; border: 1px solid #9a5f4a;
    border-radius: 8px; padding: 2px 8px; font-size: 10px; font-weight: 700; }
QPushButton#suiteCardUpdateInstall { background: #2f6e57; color: #e2f6ec; border: 1px solid #4d9a7d;
    border-radius: 8px; padding: 3px 12px; font-size: 10px; font-weight: 700; }
QPushButton#suiteCardUpdateInstall:hover { background: #3a8a6c; }
QLabel#suiteUpdateBanner { background: #1f3550; color: #cfe6ff; border: 1px solid #3f6fa8;
    border-radius: 9px; padding: 10px 14px; font-weight: 650; }



QFrame#suiteModuleHeader { background: #25344a; border: 1px solid #445976; border-radius: 12px; }
QFrame#suiteModuleHeader QLabel { background: transparent; border: none; }
QLabel#suiteModuleHeading { font-size: 21px; font-weight: 750; color: #f1f5fd; }
QLabel#suiteModuleSubheading { font-size: 12px; color: #b7c9df; }
QLabel#suiteModuleGroup { font-size: 10px; font-weight: 700; color: #92bfff; }
QLabel#suiteModuleIcon { background: #314762; border: 1px solid #527197; border-radius: 10px; }
QGroupBox { background: #243247; border: 1px solid #405978; border-radius: 9px;
            margin-top: 16px; padding: 12px 8px 6px 8px; }
QGroupBox::title { left: 12px; padding: 0 5px; }
QFrame#suiteWorkspaceToolbar { background: #243247; border: 1px solid #405978;
                                border-radius: 10px; }
QFrame#suiteWorkspaceToolbar QPushButton { min-height: 22px; }
QTabWidget::pane { border: 1px solid #405978; border-radius: 4px; }
QPushButton:focus { border: 2px solid #90baff; }
QListWidget::item:hover:!selected { background: #334966; }


QLabel#suiteResultsHeading { color: #f1f5ff; font-weight: 750; font-size: 17px; }
QLabel#suiteResultsHeadline { color: #b9cce4; font-size: 12px; }
QFrame#suiteResultCard { background: #283950; border: 1px solid #456081; border-radius: 10px; }
QLabel#suiteMetricTitle { color: #b9cce4; font-size: 11px; }
QLabel#suiteMetricValue { color: #f2f7ff; font-size: 20px; font-weight: 750; }
QLabel#suiteMetricDetail { color: #a8bdd7; font-size: 10px; }
QFrame#suiteResultCard[checkState="ok"] { border-left: 4px solid #63cda7; }
QFrame#suiteResultCard[checkState="bad"] { border-left: 4px solid #f38f82; }
QFrame#suiteResultCard[checkState="warn"] { border-left: 4px solid #f2bd68; }
QLabel#suiteResultWarnings { background: #4d3b28; border: 1px solid #8f7646;
    border-radius: 7px; padding: 10px; color: #ffe9bf; }
QFrame#suiteResultTablePanel { background: #283950; border: 1px solid #456081; border-radius: 8px; }
QLabel#suiteResultTableTitle { color: #e0edfc; font-weight: 650; }


QLabel#suiteSectionHint { background: #293e58; color: #d5e8ff;
    border: 1px solid #405d80; border-radius: 6px; padding: 9px 12px; }
QTableWidget#suiteInputTable { selection-background-color: #375b83;
    alternate-background-color: #293c53; gridline-color: #435b78; }
QPushButton#suiteSpecialAction { background: #2f4969; color: #e2eeff;
    border: 1px solid #537ba9; font-weight: 650; }

"""


def stylesheet(theme: str) -> str:
    return DARK if theme == "dark" else LIGHT
