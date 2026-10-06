"""Icon loading and rendering utilities for AutoLaunch.

Resolves FreeDesktop theme icons and image files seamlessly for PyQt6.
Strictly avoids hardcoded user paths.
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtGui import QIcon

from desktop_scanner import find_icon_file


def resolve_icon(icon_name: Optional[str], icon_path: Optional[str] = None) -> QIcon:
    """Resolves an icon from theme or file path.

    Returns a valid QIcon or a fallback system icon.
    """
    # 1. Direct path provided
    if icon_path:
        p_obj = Path(icon_path).expanduser()
        if p_obj.is_file():
            icon = QIcon(str(p_obj))
            if not icon.isNull():
                return icon

    # 2. Check if icon_name itself is an existing file
    if icon_name:
        candidate_path = Path(icon_name).expanduser()
        if candidate_path.is_file():
            icon = QIcon(str(candidate_path))
            if not icon.isNull():
                return icon

        # 3. Theme icon lookup
        theme_icon = QIcon.fromTheme(icon_name)
        if not theme_icon.isNull():
            return theme_icon

        # 4. Check scanner icon search
        discovered = find_icon_file(icon_name)
        if discovered and Path(discovered).is_file():
            icon = QIcon(discovered)
            if not icon.isNull():
                return icon

    # 5. System fallback
    fallback = QIcon.fromTheme("application-x-executable")
    if not fallback.isNull():
        return fallback

    return QIcon()
