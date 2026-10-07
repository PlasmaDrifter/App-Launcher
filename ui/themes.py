"""Theme system for AutoLaunch adapted from Theme Factory.

Provides 6 curated visual identities:
- Ocean Depths (Default): Deep maritime navy with soothing teal highlights
- Tech Innovation: Cyber dark aesthetic with electric blue and neon cyan
- Midnight Galaxy: Cosmic purple with mystical lavender and indigo accents
- Forest Canopy: Grounded organic dark theme with sage and olive accents
- Modern Minimalist: Clean contemporary grayscale with refined slate tones
- Sunset Boulevard: Deep twilight dusk with warm amber and coral accents

Complies with zero-emoji guidelines and dynamic path resolution.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
CHECKMARK_ICON_PATH = (ASSETS_DIR / "checkmark.svg").as_posix()


@dataclass(frozen=True)
class Theme:
    key: str
    name: str
    description: str
    # Surfaces & Backgrounds
    bg_base: str
    bg_surface: str
    bg_card: str
    bg_header: str
    card_hover: str
    # Borders
    border_subtle: str
    border_focus: str
    # Typography
    text_primary: str
    text_secondary: str
    text_muted: str
    # Accent / Glow
    accent_primary: str
    accent_hover: str
    accent_active: str
    accent_subtle: str
    accent_border: str
    # Status / Alerts
    danger: str
    danger_hover: str
    danger_border: str
    success: str
    success_hover: str

    def build_stylesheet(self) -> str:
        """Builds a complete application-level Qt stylesheet (QSS) for this theme."""
        return f"""
QMainWindow, QDialog {{
    background-color: {self.bg_base};
    color: {self.text_primary};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}}

QWidget {{
    font-size: 13px;
    color: {self.text_secondary};
}}

/* Tooltips */
QToolTip {{
    background-color: {self.bg_card};
    color: {self.text_primary};
    border: 1px solid {self.border_subtle};
    border-radius: 6px;
    padding: 7px 9px;
    font-size: 14px;
}}

/* Scroll Area & List Widgets */
QScrollArea {{
    border: none;
    background: transparent;
}}

QListWidget {{
    border: 1px solid {self.border_subtle};
    border-radius: 10px;
    background-color: {self.bg_surface};
    padding: 4px;
    outline: none;
}}

QListWidget::item {{
    border-radius: 8px;
    padding: 6px 8px;
    margin: 2px 0px;
    background: transparent;
}}

QListWidget::item:hover {{
    background-color: {self.bg_card};
    color: {self.text_primary};
}}

QListWidget::item:selected {{
    background-color: {self.accent_subtle};
    color: {self.text_primary};
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {self.border_subtle};
    min-height: 24px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background: {self.accent_primary};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0px;
    background: none;
}}

QScrollBar:horizontal {{
    border: none;
    background: transparent;
    height: 6px;
}}

QScrollBar::handle:horizontal {{
    background: {self.border_subtle};
    min-width: 24px;
    border-radius: 3px;
}}

/* Push Buttons */
QPushButton {{
    background-color: {self.bg_card};
    color: {self.text_primary};
    border: 1px solid {self.border_subtle};
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {self.card_hover};
    border-color: {self.border_focus};
    color: {self.text_primary};
}}

QPushButton:pressed {{
    background-color: {self.bg_surface};
    border-color: {self.accent_primary};
}}

QPushButton:disabled {{
    background-color: {self.bg_surface};
    color: {self.text_muted};
    border-color: {self.border_subtle};
}}

/* Inputs & LineEdits */
QLineEdit, QSpinBox {{
    background-color: {self.bg_surface};
    color: {self.text_primary};
    border: 1px solid {self.border_subtle};
    border-radius: 6px;
    padding: 7px 12px;
    selection-background-color: {self.accent_active};
}}

QLineEdit:focus, QSpinBox:focus {{
    border: 1px solid {self.border_focus};
    background-color: {self.bg_card};
}}

/* Combo Boxes */
QComboBox {{
    background-color: {self.bg_surface};
    color: {self.text_primary};
    border: 1px solid {self.border_subtle};
    border-radius: 6px;
    padding: 4px 26px 4px 10px;
    font-weight: 500;
}}

QComboBox:hover {{
    border-color: {self.border_focus};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border: none;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {self.text_muted};
    margin-right: 6px;
}}

QComboBox::down-arrow:hover {{
    border-top-color: {self.accent_hover};
}}

QComboBox QAbstractItemView, QComboBox QListView {{
    background-color: {self.bg_card};
    color: {self.text_primary};
    border: 1px solid {self.border_focus};
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    outline: none;
}}

QComboBox QAbstractItemView::item, QComboBox QListView::item {{
    min-height: 28px;
    padding: 4px 10px;
    border-radius: 5px;
    color: {self.text_primary};
    background-color: transparent;
}}

QComboBox QAbstractItemView::item:hover, QComboBox QListView::item:hover {{
    background-color: #1d4ed8;
    color: #ffffff;
}}

QComboBox QAbstractItemView::item:selected, QComboBox QListView::item:selected {{
    background-color: #2563eb;
    color: #ffffff;
    font-weight: bold;
}}

/* Tab Widgets */
QTabWidget::pane {{
    border: 1px solid {self.border_subtle};
    border-radius: 8px;
    background-color: {self.bg_surface};
    top: -1px;
}}

QTabBar::tab {{
    background: transparent;
    color: {self.text_muted};
    padding: 8px 18px;
    font-weight: 500;
    border-bottom: 2px solid transparent;
}}

QTabBar::tab:hover {{
    color: {self.text_primary};
}}

QTabBar::tab:selected {{
    color: {self.accent_hover};
    font-weight: bold;
    border-bottom: 2px solid {self.accent_hover};
}}

/* Group Boxes */
QGroupBox {{
    border: 1px solid {self.border_subtle};
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 14px;
    padding-left: 10px;
    padding-right: 10px;
    padding-bottom: 10px;
    font-weight: bold;
    color: {self.text_muted};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: {self.accent_hover};
}}

/* Checkboxes */
QCheckBox {{
    spacing: 9px;
    color: {self.text_secondary};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #64748b;
    background-color: {self.bg_surface};
}}

QCheckBox::indicator:hover {{
    border: 2px solid {self.border_focus};
    background-color: {self.bg_card};
}}

QCheckBox::indicator:checked {{
    border: 2px solid #d4d4d8;
    background-color: #334155;
    image: url("{CHECKMARK_ICON_PATH}");
}}

QCheckBox::indicator:checked:hover {{
    border: 2px solid #d4d4d8;
    background-color: #475569;
    image: url("{CHECKMARK_ICON_PATH}");
}}
"""


THEMES: Dict[str, Theme] = {
    "modern_minimalist": Theme(
        key="modern_minimalist",
        name="Modern Minimalist",
        description="Clean contemporary grayscale with refined slate tones",
        bg_base="#121214",
        bg_surface="#18181b",
        bg_card="#202024",
        bg_header="#1c1c20",
        card_hover="#28282e",
        border_subtle="#2f2f37",
        border_focus="#64748b",
        text_primary="#d4d4d8",
        text_secondary="#d4d4d8",
        text_muted="#71717a",
        accent_primary="#94a3b8",
        accent_hover="#e2e8f0",
        accent_active="#64748b",
        accent_subtle="rgba(226, 232, 240, 0.15)",
        accent_border="rgba(226, 232, 240, 0.45)",
        danger="#e11d48",
        danger_hover="#f43f5e",
        danger_border="rgba(225, 29, 72, 0.35)",
        success="#10b981",
        success_hover="#34d399",
    ),
}

MODERN_MINIMALIST = THEMES["modern_minimalist"]
DEFAULT_THEME_KEY = "modern_minimalist"
DEFAULT_THEME = DEFAULT_THEME_KEY


def get_theme(key: Optional[str] = None) -> Theme:
    """Returns the Theme matching the specified key, falling back to default."""
    if key and key in THEMES:
        return THEMES[key]
    return THEMES[DEFAULT_THEME_KEY]


def get_all_themes() -> List[Theme]:
    """Returns list of all registered themes."""
    return list(THEMES.values())


def get_theme_choices() -> List[Tuple[str, str, str]]:
    """Returns list of (key, name, description) tuples for UI dropdowns."""
    return [(t.key, t.name, t.description) for t in THEMES.values()]


def build_card_stylesheet(theme: Theme) -> str:
    """Returns QSS stylesheet for AppCardWidget."""
    return f"""
        QFrame#AppCard {{
            background-color: {theme.bg_card};
            border: 1px solid {theme.border_subtle};
            border-radius: 8px;
        }}
        QFrame#AppCard:hover {{
            background-color: {theme.card_hover};
            border: 1px solid {theme.border_focus};
        }}
    """


def build_header_btn_stylesheet(theme: Theme) -> str:
    """Returns QSS stylesheet for top header action buttons."""
    return f"""
        QPushButton {{
            background-color: {theme.bg_card};
            color: {theme.text_secondary};
            border: 1px solid {theme.border_subtle};
            border-radius: 5px;
            font-size: 11px;
            font-weight: 500;
            padding: 4px 8px;
        }}
        QPushButton:hover {{
            background-color: {theme.accent_subtle};
            border-color: {theme.accent_hover};
            color: {theme.text_primary};
        }}
        QPushButton:disabled {{
            color: {theme.text_muted};
            border-color: {theme.border_subtle};
        }}
    """


def build_default_btn_active_stylesheet(theme: Theme) -> str:
    """Returns QSS stylesheet for active default profile button."""
    return f"""
        QPushButton {{
            background-color: {theme.accent_subtle};
            color: {theme.accent_hover};
            border: 1px solid {theme.accent_border};
            border-radius: 5px;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 8px;
        }}
        QPushButton:hover {{
            background-color: {theme.accent_subtle};
            border-color: {theme.accent_hover};
            color: #ffffff;
        }}
        QPushButton:disabled {{
            background-color: {theme.accent_subtle};
            color: {theme.accent_hover};
            border: 1px solid {theme.accent_border};
        }}
    """


def build_delete_btn_stylesheet(theme: Theme) -> str:
    """Returns QSS stylesheet for delete profile / remove button."""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {theme.danger};
            border: 1px solid {theme.danger_border};
            border-radius: 5px;
            font-size: 11px;
            font-weight: 500;
            padding: 4px 8px;
        }}
        QPushButton:hover {{
            background-color: {theme.danger_border};
            border-color: {theme.danger_hover};
            color: #ffffff;
        }}
        QPushButton:disabled {{
            color: {theme.text_muted};
            border-color: {theme.border_subtle};
        }}
    """


def build_micro_btn_stylesheet(theme: Theme) -> str:
    """Returns QSS stylesheet for compact card action buttons (up, down, edit)."""
    return f"""
        QPushButton {{
            background-color: {theme.bg_card};
            color: {theme.text_secondary};
            border: 1px solid {theme.border_subtle};
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            padding: 2px 4px;
        }}
        QPushButton:hover {{
            background-color: {theme.card_hover};
            border-color: {theme.accent_hover};
            color: {theme.text_primary};
        }}
        QPushButton:pressed {{
            background-color: {theme.bg_surface};
            border-color: {theme.accent_primary};
        }}
        QPushButton:disabled {{
            color: {theme.text_muted};
            border-color: {theme.border_subtle};
        }}
    """


def build_micro_delete_btn_stylesheet(theme: Theme) -> str:
    """Returns QSS stylesheet for compact card delete button."""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {theme.danger};
            border: 1px solid {theme.danger_border};
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            padding: 2px 4px;
        }}
        QPushButton:hover {{
            background-color: {theme.danger_border};
            border-color: {theme.danger_hover};
            color: #ffffff;
        }}
        QPushButton:disabled {{
            color: {theme.text_muted};
            border-color: {theme.border_subtle};
        }}
    """


def build_primary_btn_stylesheet(theme: Theme) -> str:
    """Returns QSS stylesheet for primary dialog action/save button."""
    return f"""
        QPushButton {{
            background-color: {theme.bg_card};
            color: {theme.text_primary};
            font-weight: bold;
            font-size: 13px;
            border: 1px solid {theme.accent_border};
            border-radius: 6px;
            padding: 7px 22px;
        }}
        QPushButton:hover {{
            background-color: {theme.card_hover};
            border-color: #d4d4d8;
            color: #d4d4d8;
        }}
        QPushButton:pressed {{
            background-color: {theme.bg_surface};
            border-color: {theme.accent_primary};
        }}
    """
