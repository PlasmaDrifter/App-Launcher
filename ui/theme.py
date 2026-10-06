"""Theme definitions and modern dark stylesheet for AutoLaunch.

Inspired by modern Linux desktop aesthetics, with deep obsidian backgrounds,
sleek card elevation, cyan and emerald accent gradients, and refined typography.
Zero emojis used.
"""


MODERN_DARK_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #0b0f19;
    color: #f1f5f9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

QWidget {
    font-size: 13px;
    color: #e2e8f0;
}

/* Tooltips */
QToolTip {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #38bdf8;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 11px;
}

/* Scroll Area & List Widgets */
QScrollArea {
    border: none;
    background: transparent;
}

QListWidget {
    border: 1px solid #1e293b;
    border-radius: 10px;
    background-color: #0f172a;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    border-radius: 8px;
    padding: 6px 8px;
    margin: 2px 0px;
    background: transparent;
}

QListWidget::item:hover {
    background-color: #1e293b;
    color: #ffffff;
}

QListWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    height: 0px;
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 6px;
}

QScrollBar::handle:horizontal {
    background: #334155;
    min-width: 24px;
    border-radius: 3px;
}

/* Push Buttons */
QPushButton {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #475569;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #0f172a;
    border-color: #38bdf8;
}

QPushButton:disabled {
    background-color: #111827;
    color: #475569;
    border-color: #1f2937;
}

/* Inputs & LineEdits */
QLineEdit, QSpinBox {
    background-color: #111827;
    color: #f8fafc;
    border: 1px solid #28354f;
    border-radius: 6px;
    padding: 7px 12px;
    selection-background-color: #2563eb;
}

QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #38bdf8;
    background-color: #141d30;
}

/* Combo Boxes */
QComboBox {
    background-color: #111827;
    color: #f8fafc;
    border: 1px solid #28354f;
    border-radius: 6px;
    padding: 4px 26px 4px 10px;
    font-weight: 500;
}

QComboBox:hover {
    border-color: #38bdf8;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border: none;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #94a3b8;
    margin-right: 6px;
}

QComboBox::down-arrow:hover {
    border-top-color: #38bdf8;
}

QComboBox QAbstractItemView {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #2563eb;
    outline: none;
}

/* Tab Widgets */
QTabWidget::pane {
    border: 1px solid #1e293b;
    border-radius: 8px;
    background-color: #0f172a;
    top: -1px;
}

QTabBar::tab {
    background: transparent;
    color: #94a3b8;
    padding: 8px 18px;
    font-weight: 500;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:hover {
    color: #f1f5f9;
}

QTabBar::tab:selected {
    color: #38bdf8;
    font-weight: bold;
    border-bottom: 2px solid #38bdf8;
}

/* Group Boxes */
QGroupBox {
    border: 1px solid #1e293b;
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 14px;
    padding-left: 10px;
    padding-right: 10px;
    padding-bottom: 10px;
    font-weight: bold;
    color: #94a3b8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: #38bdf8;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    color: #e2e8f0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: #111827;
}

QCheckBox::indicator:hover {
    border-color: #38bdf8;
}

QCheckBox::indicator:checked {
    background-color: #38bdf8;
    border-color: #38bdf8;
}
"""

CLASSIC_DARK_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #232629;
    color: #eff0f1;
}

QWidget {
    font-size: 12px;
    color: #eff0f1;
}

/* Tooltips */
QToolTip {
    background-color: #31363b;
    color: #eff0f1;
    border: 1px solid #4f5b66;
    padding: 4px;
    font-size: 11px;
}

/* Scroll Area & List Widgets */
QListWidget {
    border: 1px solid #31363b;
    border-radius: 4px;
    background-color: #1b1e20;
    padding: 2px;
    outline: none;
}

QListWidget::item {
    border-bottom: 1px solid #2a2e32;
    background: transparent;
    padding: 0px;
    margin: 0px;
}

QListWidget::item:hover {
    background-color: #2d3237;
}

/* Push Buttons */
QPushButton {
    background-color: #31363b;
    color: #eff0f1;
    border: 1px solid #4f5b66;
    border-radius: 4px;
    padding: 5px 12px;
    font-weight: normal;
}

QPushButton:hover {
    background-color: #3a4147;
    border-color: #3daee9;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #232629;
    border-color: #3daee9;
}

QPushButton:disabled {
    background-color: #282c2f;
    color: #656d75;
    border-color: #31363b;
}

/* Inputs & LineEdits */
QLineEdit, QSpinBox {
    background-color: #1b1e20;
    color: #eff0f1;
    border: 1px solid #4f5b66;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #3daee9;
}

QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #3daee9;
}

/* Combo Boxes */
QComboBox {
    background-color: #31363b;
    color: #eff0f1;
    border: 1px solid #4f5b66;
    border-radius: 4px;
    padding: 4px 24px 4px 8px;
}

QComboBox:hover {
    border-color: #3daee9;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border: none;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #bdc3c7;
    margin-right: 6px;
}

QComboBox::down-arrow:hover {
    border-top-color: #3daee9;
}

QComboBox QAbstractItemView {
    background-color: #1b1e20;
    color: #eff0f1;
    border: 1px solid #31363b;
    padding: 2px;
    selection-background-color: #3daee9;
    outline: none;
}

/* Group Boxes */
QGroupBox {
    border: 1px solid #31363b;
    border-radius: 4px;
    margin-top: 14px;
    padding-top: 12px;
    padding-left: 8px;
    padding-right: 8px;
    padding-bottom: 8px;
    font-weight: bold;
    color: #bdc3c7;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #3daee9;
}

/* Checkboxes */
QCheckBox {
    spacing: 6px;
    color: #eff0f1;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #4f5b66;
    background-color: #1b1e20;
}

QCheckBox::indicator:hover {
    border-color: #3daee9;
}

QCheckBox::indicator:checked {
    background-color: #3daee9;
    border-color: #3daee9;
}
"""


def get_stylesheet(style_name: str = "modern") -> str:
    """Returns the QSS stylesheet for the given visual style."""
    if style_name == "classic":
        return CLASSIC_DARK_STYLESHEET
    return MODERN_DARK_STYLESHEET

