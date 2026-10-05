"""Process launcher for AutoLaunch.

Spawns applications in detached sessions so they continue running after AutoLaunch exits.
Prefers gtk-launch / gio launch for desktop entries so desktop environments (such as KDE Wayland)
correctly associate running windows with their .desktop file and display custom icons.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

from config import AppEntry


class AppLauncher:
    """Manages spawning applications in decoupled sessions."""

    @staticmethod
    def _has_binary(name: str) -> bool:
        return shutil.which(name) is not None

    @classmethod
    def get_launch_command(cls, app: AppEntry) -> Tuple[List[str], bool]:
        """Returns the command arguments and whether shell=True should be used.

        For .desktop files:
        Uses gtk-launch or gio launch so the desktop environment sets the proper
        Wayland app_id and startup notification token for custom icons.
        """
        # Check if desktop file is configured and exists
        desktop_target = app.desktop_file.strip()
        desktop_path: Path = Path(desktop_target).expanduser() if desktop_target else Path()
        desktop_id = desktop_path.name if desktop_target else ""

        # Check if gtk-launch or gio is available
        has_gtk_launch = cls._has_binary("gtk-launch")
        has_gio = cls._has_binary("gio")

        cmd_str = ""

        if desktop_id and has_gtk_launch:
            cmd_str = f'gtk-launch "{desktop_id}"'
        elif desktop_path.is_file() and has_gio:
            cmd_str = f'gio launch "{desktop_path}"'
        elif app.command.strip():
            cmd_str = app.command.strip()
        elif desktop_path.is_file():
            # Fallback to parsing exec line from desktop file
            from desktop_scanner import DesktopScanner
            parsed = DesktopScanner.parse_desktop_file(desktop_path)
            if parsed and parsed.clean_command:
                cmd_str = parsed.clean_command

        if not cmd_str:
            raise ValueError(f"No valid command or desktop file found for app: {app.name}")

        if app.delay_seconds > 0:
            full_shell_cmd = f"sleep {app.delay_seconds} && exec {cmd_str}"
        else:
            full_shell_cmd = f"exec {cmd_str}"

        return ["/bin/sh", "-c", full_shell_cmd], False

    @classmethod
    def launch(cls, app: AppEntry) -> bool:
        """Launches a single app in a detached background session."""
        try:
            args, use_shell = cls.get_launch_command(app)
            # Create a completely detached process
            env = os.environ.copy()
            subprocess.Popen(
                args,
                shell=use_shell,
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                env=env,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def get_current_activity() -> str:
        """Returns the current active KDE Plasma activity UUID if available."""
        try:
            res = subprocess.run(
                ["qdbus-qt6", "org.kde.ActivityManager", "/ActivityManager/Activities", "CurrentActivity"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return ""

    @staticmethod
    def restore_activity_deferred(activity_id: str, delay_seconds: float = 1.2) -> None:
        """Ensures the desktop view stays on the starting activity after apps on secondary activities spawn."""
        if not activity_id:
            return
        cmd = (
            f"sleep {delay_seconds} && "
            f"qdbus-qt6 org.kde.ActivityManager /ActivityManager/Activities SetCurrentActivity '{activity_id}'"
        )
        try:
            subprocess.Popen(
                ["/bin/sh", "-c", cmd],
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        except Exception:
            pass

    @classmethod
    def launch_many(cls, apps: List[AppEntry]) -> int:
        """Launches all enabled applications in the list. Returns count launched."""
        initial_activity = cls.get_current_activity()
        launched_count = 0
        for app in apps:
            if app.enabled:
                if cls.launch(app):
                    launched_count += 1

        if initial_activity:
            cls.restore_activity_deferred(initial_activity)

        return launched_count

