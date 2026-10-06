#!/usr/bin/env python3
"""AutoLaunch - Startup Application Launcher.

Configures and launches startup applications on desktop boot with profiles,
countdown timer, and clean self-termination upon launching.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPalette, QColor
from PyQt6.QtWidgets import QApplication

from config import ConfigManager
from launcher import AppLauncher
from ui.main_window import MainWindow
from ui.theme import MODERN_DARK_STYLESHEET


def apply_dark_theme(app: QApplication) -> None:
    """Applies a clean, modern dark palette matching KDE dark breeze styling."""
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(35, 38, 41))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(239, 240, 241))
    palette.setColor(QPalette.ColorRole.Base, QColor(27, 30, 32))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 38, 41))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(20, 20, 20))
    palette.setColor(QPalette.ColorRole.Text, QColor(239, 240, 241))
    palette.setColor(QPalette.ColorRole.Button, QColor(49, 54, 59))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(239, 240, 241))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Link, QColor(61, 174, 233))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(61, 174, 233))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)


def main() -> None:
    parser = argparse.ArgumentParser(description="AutoLaunch Desktop Application")
    parser.add_argument("--autostart", action="store_true", help="Started by desktop autostart")
    parser.add_argument("--config", action="store_true", help="Open in configuration mode without countdown")
    parser.add_argument("--headless", action="store_true", help="Launch active profile without showing GUI")
    args = parser.parse_args()

    config_manager = ConfigManager()

    if args.headless:
        profile = config_manager.get_current_profile()
        enabled = [a for a in profile.apps if a.enabled]
        AppLauncher.launch_many(enabled, global_launch_minimized=config_manager.launch_minimized)
        sys.exit(0)

    # Disable countdown if --config flag is explicitly passed
    if args.config:
        config_manager.enable_countdown = False

    app = QApplication(sys.argv)
    app.setApplicationName("AutoLaunch")
    app.setApplicationDisplayName("AutoLaunch")
    app.setDesktopFileName("autolaunch")

    # App icon
    assets_icon = SCRIPT_DIR / "assets" / "autolaunch.svg"
    if assets_icon.is_file():
        app.setWindowIcon(QIcon(str(assets_icon)))
    else:
        app_icon = QIcon.fromTheme("autolaunch", QIcon.fromTheme("system-run"))
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)

    apply_dark_theme(app)
    app.setStyleSheet(MODERN_DARK_STYLESHEET)

    window = MainWindow(config_manager, autostart_mode=args.autostart)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
