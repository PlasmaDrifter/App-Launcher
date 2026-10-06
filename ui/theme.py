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
    border: 1px solid #4a6d8c;
    border-radius: 6px;
    padding: 7px 9px;
    font-size: 14px;
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
    background-color: #244366;
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
    border-color: #4a6d8c;
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
    selection-background-color: #244366;
}

QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #4a6d8c;
    background-color: #131a28;
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
    border-color: #4a6d8c;
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
    border-top-color: #6297bf;
}

QComboBox QAbstractItemView {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #244366;
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
    color: #6297bf;
    font-weight: bold;
    border-bottom: 2px solid #6297bf;
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
    color: #6297bf;
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
    border-color: #4a6d8c;
}

QCheckBox::indicator:checked {
    background-color: #356082;
    border-color: #4a6d8c;
}
"""
