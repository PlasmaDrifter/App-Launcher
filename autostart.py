"""Autostart configuration and desktop entry management for AutoLaunch.

Ensures no hardcoded user paths are written into configuration or desktop entries.
Uses dynamic environment resolution ($HOME / Path.home()) and standard XDG locations.
"""

from pathlib import Path


class AutostartManager:
    """Manages the ~/.config/autostart/autolaunch.desktop entry."""

    @staticmethod
    def get_autostart_file() -> Path:
        return Path.home() / ".config" / "autostart" / "autolaunch.desktop"

    @staticmethod
    def get_applications_desktop_file() -> Path:
        return Path.home() / ".local" / "share" / "applications" / "autolaunch.desktop"

    @classmethod
    def is_autostart_enabled(cls) -> bool:
        return cls.get_autostart_file().is_file()

    @classmethod
    def set_autostart(cls, enabled: bool) -> bool:
        autostart_file = cls.get_autostart_file()
        if enabled:
            try:
                autostart_file.parent.mkdir(parents=True, exist_ok=True)
                content = cls.generate_desktop_content(autostart=True)
                with open(autostart_file, "w", encoding="utf-8") as f:
                    f.write(content)
                autostart_file.chmod(0o755)
                return True
            except Exception:
                return False
        else:
            try:
                if autostart_file.is_file():
                    autostart_file.unlink()
                return True
            except Exception:
                return False

    @classmethod
    def install_desktop_entry(cls) -> bool:
        """Installs desktop entry into ~/.local/share/applications for system menus."""
        app_file = cls.get_applications_desktop_file()
        try:
            app_file.parent.mkdir(parents=True, exist_ok=True)
            content = cls.generate_desktop_content(autostart=False)
            with open(app_file, "w", encoding="utf-8") as f:
                f.write(content)
            app_file.chmod(0o755)
            return True
        except Exception:
            return False

    @staticmethod
    def generate_desktop_content(autostart: bool = False) -> str:
        """Generates desktop file content without any hardcoded usernames."""
        flag = " --autostart" if autostart else ""
        exec_line = f'Exec=sh -c \'python3 "$HOME/Source/AutoLaunch/autolaunch.py"{flag}\''
        icon_path = 'Icon=autolaunch'

        return f"""[Desktop Entry]
Type=Application
Version=1.0
Name=AutoLaunch
GenericName=Startup Application Launcher
Comment=Configure and launch startup applications on desktop boot
{exec_line}
{icon_path}
Terminal=false
StartupNotify=true
Categories=LocalTools;
X-GNOME-Autostart-enabled=true
StartupWMClass=autolaunch
X-KDE-Wayland-AppId=autolaunch
"""
