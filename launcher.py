"""Process launcher for AutoLaunch.

Spawns applications in detached sessions so they continue running after AutoLaunch exits.
Prefers gtk-launch / gio launch for desktop entries so desktop environments (such as KDE Wayland)
correctly associate running windows with their .desktop file and display custom icons.
"""

import functools
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

from config import AppEntry


class AppLauncher:
    """Manages spawning applications in decoupled sessions."""

    @staticmethod
    @functools.lru_cache(maxsize=32)
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
    def get_target_window_classes(cls, app: AppEntry) -> List[str]:
        """Resolves probable window classes for the given app entry."""
        classes = []
        desktop_target = app.desktop_file.strip()
        desktop_path: Path = Path(desktop_target).expanduser() if desktop_target else Path()
        
        if desktop_path.is_file():
            from desktop_scanner import DesktopScanner
            parsed = DesktopScanner.parse_desktop_file(desktop_path)
            if parsed:
                if parsed.startup_wm_class:
                    classes.append(parsed.startup_wm_class)
                if parsed.kde_app_id and parsed.kde_app_id not in classes:
                    classes.append(parsed.kde_app_id)
            stem = desktop_path.stem
            if stem.endswith(".desktop"):
                stem = stem[:-8]
            if stem and stem not in classes:
                classes.append(stem)
        elif desktop_target:
            stem = Path(desktop_target).stem
            if stem.endswith(".desktop"):
                stem = stem[:-8]
            if stem:
                classes.append(stem)

        # Also extract from command if specified (e.g. --class foo)
        if app.command:
            m = re.search(r"--class\s+([^\s]+)", app.command)
            if m and m.group(1) not in classes:
                classes.append(m.group(1))
            parts = app.command.split()
            if parts:
                cmd_stem = Path(parts[0]).name
                if cmd_stem and cmd_stem not in classes:
                    classes.append(cmd_stem)

        return classes

    @classmethod
    def minimize_window_deferred(cls, app: AppEntry, delay_seconds: float = 0.0) -> None:
        """Polls for the app window's appearance and minimizes it via kdotool."""
        if not cls._has_binary("kdotool"):
            return

        classes = cls.get_target_window_classes(app)
        if not classes:
            return

        # Build regex for class search
        class_regex = "|".join(re.escape(c) for c in classes)
        total_delay = max(0.0, float(app.delay_seconds)) + delay_seconds

        # Background script: sleeps until startup delay passes, then polls kdotool search for window and minimizes
        script = (
            f"sleep {total_delay}; "
            f"for i in $(seq 1 30); do "
            f"wids=$(kdotool search --class '{class_regex}' 2>/dev/null); "
            f'if [ -n "$wids" ]; then '
            f'for wid in $wids; do kdotool windowminimize "$wid" 2>/dev/null; done; '
            f"break; "
            f"fi; "
            f"sleep 0.25; "
            f"done"
        )

        try:
            subprocess.Popen(
                ["/bin/sh", "-c", script],
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        except Exception:
            pass

    @classmethod
    def launch(cls, app: AppEntry, global_launch_minimized: bool = False) -> bool:
        """Launches a single app in an isolated background session."""
        try:
            args, use_shell = cls.get_launch_command(app)

            # In systemd user sessions (such as autostart), wrap with systemd-run so
            # the launched process breaks out into its own transient unit in app.slice
            # instead of being trapped in AutoLaunch's service cgroup.
            if cls._has_binary("systemd-run"):
                desc = app.name or "AutoLaunch app"
                # args is ["/bin/sh", "-c", full_shell_cmd]
                cmd_to_run = args if isinstance(args, list) else [args]
                run_args = [
                    "systemd-run",
                    "--user",
                    "--slice=app.slice",
                    f"--description={desc}",
                    *cmd_to_run,
                ]
                try:
                    res = subprocess.run(
                        run_args,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if res.returncode == 0:
                        if app.start_minimized or global_launch_minimized:
                            cls.minimize_window_deferred(app)
                        return True
                except Exception:
                    pass

            # Fallback to detached subprocess.Popen
            subprocess.Popen(
                args,
                shell=use_shell,
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )

            # Check if application should be minimized upon launch
            if app.start_minimized or global_launch_minimized:
                cls.minimize_window_deferred(app)

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
    def restore_activity_deferred(activity_id: str, duration_seconds: float = 12.0) -> None:
        """Ensures the desktop view stays on the starting activity after apps on secondary activities spawn."""
        if not activity_id:
            return
        script = (
            f"for i in $(seq 1 24); do "
            f"sleep 0.5; "
            f"curr=$(qdbus-qt6 org.kde.ActivityManager /ActivityManager/Activities CurrentActivity 2>/dev/null); "
            f'if [ -n "$curr" ] && [ "$curr" != "{activity_id}" ]; then '
            f'qdbus-qt6 org.kde.ActivityManager /ActivityManager/Activities SetCurrentActivity "{activity_id}" 2>/dev/null; '
            f"fi; "
            f"done"
        )
        try:
            subprocess.Popen(
                ["/bin/sh", "-c", script],
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        except Exception:
            pass

    @classmethod
    def launch_many(cls, apps: List[AppEntry], global_launch_minimized: bool = False) -> int:
        """Launches all enabled applications in the list. Returns count launched."""
        initial_activity = cls.get_current_activity()
        launched_count = 0
        for app in apps:
            if app.enabled:
                if cls.launch(app, global_launch_minimized=global_launch_minimized):
                    launched_count += 1

        if initial_activity:
            cls.restore_activity_deferred(initial_activity)

        return launched_count

