"""Theme definitions and backward-compatible exports for AutoLaunch.

Points to the centralized theme engine in ui.themes.
Zero emojis used.
"""

from ui.themes import (
    DEFAULT_THEME_KEY,
    THEMES,
    Theme,
    build_card_stylesheet,
    build_default_btn_active_stylesheet,
    build_delete_btn_stylesheet,
    build_header_btn_stylesheet,
    build_micro_btn_stylesheet,
    build_micro_delete_btn_stylesheet,
    build_primary_btn_stylesheet,
    get_all_themes,
    get_theme,
)

# Backward-compatible global default stylesheet
MODERN_DARK_STYLESHEET = get_theme(DEFAULT_THEME_KEY).build_stylesheet()
