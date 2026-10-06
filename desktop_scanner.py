"""Desktop application scanner and metadata parser for AutoLaunch.

Scans standard FreeDesktop / XDG application directories to discover installed apps,
extracting names, clean exec commands, icons, and desktop file paths.
Strictly complies with dynamic path resolution (no hardcoded usernames).
"""

import configparser
import functools
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class DesktopAppInfo:
    """Information discovered from an installed .desktop file."""

    desktop_file: str  # Full path to .desktop file
    desktop_id: str    # e.g. zen-youtube.desktop
    name: str
    generic_name: str
    comment: str
    exec_command: str
    clean_command: str
    icon_name: str
    icon_path: Optional[str] = None
    startup_wm_class: str = ""
    kde_app_id: str = ""
    categories: Optional[List[str]] = None
    no_display: bool = False
    _search_cache: Optional[str] = None

    def search_text(self) -> str:
        """Returns consolidated lowercase string for fuzzy searching (cached)."""
        if self._search_cache is None:
            cats = " ".join(self.categories or [])
            self._search_cache = (
                f"{self.name} {self.generic_name} {self.comment} "
                f"{self.clean_command} {self.desktop_id} {cats}"
            ).lower()
        return self._search_cache


def clean_desktop_exec(raw_exec: str) -> str:
    """Removes FreeDesktop field codes (%u, %U, %f, %F, etc.) from Exec lines."""
    # Replace standard % tokens: %f, %F, %u, %U, %d, %D, %n, %N, %i, %c, %k, %v, %m
    cleaned = re.sub(r"%(?:[fFuUdDnNickvm%])", "", raw_exec)
    return " ".join(cleaned.split()).strip()


@functools.lru_cache(maxsize=512)
def find_icon_file(icon_name: str) -> Optional[str]:
    """Finds an absolute file path for an icon if not already an absolute path."""
    if not icon_name:
        return None

    path_obj = Path(icon_name)
    if path_obj.is_file():
        return str(path_obj)

    # Check for direct file with common extensions
    for ext in [".svg", ".png", ".xpm"]:
        candidate = Path(icon_name + ext)
        if candidate.is_file():
            return str(candidate)

    # Search in common user and system icon locations
    search_dirs = [
        Path.home() / ".local" / "share" / "icons",
        Path.home() / ".icons",
        Path.home() / "Pictures" / "Avatar",
        Path("/usr/share/pixmaps"),
        Path("/usr/share/icons/hicolor/scalable/apps"),
        Path("/usr/share/icons/hicolor/256x256/apps"),
        Path("/usr/share/icons/hicolor/128x128/apps"),
        Path("/usr/share/icons/hicolor/48x48/apps"),
    ]

    for sdir in search_dirs:
        if not sdir.is_dir():
            continue
        for ext in ["", ".svg", ".png", ".xpm"]:
            direct_file = sdir / f"{icon_name}{ext}"
            if direct_file.is_file():
                return str(direct_file)

    return None


class DesktopScanner:
    """Scans and parses system and user .desktop files."""

    @staticmethod
    def get_search_directories() -> List[Path]:
        """Returns standard desktop file directories dynamically."""
        dirs = []
        user_apps = Path.home() / ".local" / "share" / "applications"
        if user_apps.is_dir():
            dirs.append(user_apps)

        xdg_data_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
        for p in xdg_data_dirs.split(":"):
            if p:
                app_dir = Path(p) / "applications"
                if app_dir.is_dir():
                    dirs.append(app_dir)

        # Flatpak system and user directories
        flatpak_system = Path("/var/lib/flatpak/exports/share/applications")
        if flatpak_system.is_dir():
            dirs.append(flatpak_system)

        flatpak_user = Path.home() / ".local" / "share" / "flatpak" / "exports" / "share" / "applications"
        if flatpak_user.is_dir():
            dirs.append(flatpak_user)

        return dirs

    @classmethod
    def scan_all(cls, include_no_display: bool = False) -> List[DesktopAppInfo]:
        """Scans all desktop directories and returns sorted list of applications."""
        seen_ids = set()
        apps: List[DesktopAppInfo] = []

        for directory in cls.get_search_directories():
            try:
                for entry in directory.iterdir():
                    if not entry.is_file() or not entry.name.endswith(".desktop"):
                        continue
                    desktop_id = entry.name
                    if desktop_id in seen_ids:
                        continue

                    app_info = cls.parse_desktop_file(entry)
                    if app_info is None:
                        continue

                    if not include_no_display and app_info.no_display:
                        continue

                    seen_ids.add(desktop_id)
                    apps.append(app_info)
            except (PermissionError, FileNotFoundError):
                continue

        # Sort alphabetically by display name (case-insensitive)
        apps.sort(key=lambda a: a.name.lower())
        return apps

    @classmethod
    def parse_desktop_file(cls, path: Path) -> Optional[DesktopAppInfo]:
        """Parses a single .desktop file into DesktopAppInfo."""
        config = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            config.read(str(path), encoding="utf-8")
        except Exception:
            try:
                config.read(str(path), encoding="latin-1")
            except Exception:
                return None

        if "Desktop Entry" not in config:
            return None

        section = config["Desktop Entry"]
        entry_type = section.get("Type", "").strip()
        if entry_type and entry_type.lower() != "application":
            return None

        no_display = section.getboolean("NoDisplay", fallback=False)
        hidden = section.getboolean("Hidden", fallback=False)
        if hidden:
            return None

        name = section.get("Name", "").strip()
        exec_cmd = section.get("Exec", "").strip()

        if not name or not exec_cmd:
            return None

        generic_name = section.get("GenericName", "").strip()
        comment = section.get("Comment", "").strip()
        icon = section.get("Icon", "").strip()
        startup_wm_class = section.get("StartupWMClass", "").strip()
        kde_app_id = section.get("X-KDE-Wayland-AppId", "").strip()
        categories_raw = section.get("Categories", "").strip()
        categories = [c.strip() for c in categories_raw.split(";") if c.strip()]

        clean_cmd = clean_desktop_exec(exec_cmd)
        icon_path = find_icon_file(icon)

        return DesktopAppInfo(
            desktop_file=str(path),
            desktop_id=path.name,
            name=name,
            generic_name=generic_name,
            comment=comment,
            exec_command=exec_cmd,
            clean_command=clean_cmd,
            icon_name=icon,
            icon_path=icon_path,
            startup_wm_class=startup_wm_class,
            kde_app_id=kde_app_id,
            categories=categories,
            no_display=no_display,
        )
