"""Configuration management for AutoLaunch.

Handles dynamic resolution of XDG directories without hardcoded user paths.
Manages profiles, application lists, countdown timers, and autostart preferences.
"""

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AppEntry:
    """Represents an application configured for autolaunch."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    command: str = ""
    desktop_file: str = ""  # Full path or desktop filename (e.g. zen-youtube.desktop)
    icon: str = ""
    enabled: bool = True
    delay_seconds: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppEntry":
        return cls(
            id=str(data.get("id") or uuid.uuid4()),
            name=str(data.get("name", "")),
            command=str(data.get("command", "")),
            desktop_file=str(data.get("desktop_file", "")),
            icon=str(data.get("icon", "")),
            enabled=bool(data.get("enabled", True)),
            delay_seconds=int(data.get("delay_seconds", 0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Profile:
    """Represents a set of applications to launch."""

    name: str = "Default"
    apps: List[AppEntry] = field(default_factory=list)

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "Profile":
        raw_apps = data.get("apps", [])
        apps = [AppEntry.from_dict(item) for item in raw_apps if isinstance(item, dict)]
        return cls(name=name, apps=apps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "apps": [app.to_dict() for app in self.apps],
        }


class ConfigManager:
    """Loads, modifies, and saves AutoLaunch configuration."""

    DEFAULT_PROFILE_NAME = "Default"

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            xdg_config = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config:
                self.config_dir = Path(xdg_config) / "autolaunch"
            else:
                self.config_dir = Path.home() / ".config" / "autolaunch"
        else:
            self.config_dir = Path(config_dir)

        self.config_file = self.config_dir / "config.json"
        self.active_profile: str = self.DEFAULT_PROFILE_NAME
        self.countdown_seconds: int = 5
        self.enable_countdown: bool = True
        self.autostart_enabled: bool = True
        self.profiles: Dict[str, Profile] = {}

        self.load()

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "active_profile": self.DEFAULT_PROFILE_NAME,
            "countdown_seconds": 5,
            "enable_countdown": True,
            "autostart_enabled": True,
            "profiles": {
                self.DEFAULT_PROFILE_NAME: {
                    "apps": []
                }
            },
        }

    def load(self) -> None:
        """Loads configuration from JSON file or initializes default configuration."""
        if not self.config_file.is_file():
            self._apply_dict(self.get_default_config())
            self.save()
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._apply_dict(data)
        except Exception:
            self._apply_dict(self.get_default_config())

    def _apply_dict(self, data: Dict[str, Any]) -> None:
        self.active_profile = str(data.get("active_profile", self.DEFAULT_PROFILE_NAME))
        self.countdown_seconds = max(0, int(data.get("countdown_seconds", 5)))
        self.enable_countdown = bool(data.get("enable_countdown", True))
        self.autostart_enabled = bool(data.get("autostart_enabled", True))

        profiles_raw = data.get("profiles", {})
        self.profiles = {}
        if isinstance(profiles_raw, dict):
            for name, pdata in profiles_raw.items():
                if isinstance(pdata, dict):
                    self.profiles[name] = Profile.from_dict(name, pdata)

        if not self.profiles:
            self.profiles[self.DEFAULT_PROFILE_NAME] = Profile(name=self.DEFAULT_PROFILE_NAME, apps=[])

        if self.active_profile not in self.profiles:
            self.active_profile = next(iter(self.profiles.keys()))

    def save(self) -> None:
        """Saves current configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "active_profile": self.active_profile,
            "countdown_seconds": self.countdown_seconds,
            "enable_countdown": self.enable_countdown,
            "autostart_enabled": self.autostart_enabled,
            "profiles": {
                name: {"apps": [app.to_dict() for app in prof.apps]}
                for name, prof in self.profiles.items()
            },
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_current_profile(self) -> Profile:
        """Returns the currently active profile."""
        if self.active_profile not in self.profiles:
            self.active_profile = next(iter(self.profiles.keys()))
        return self.profiles[self.active_profile]

    def set_active_profile(self, name: str) -> bool:
        if name in self.profiles:
            self.active_profile = name
            self.save()
            return True
        return False

    def add_profile(self, name: str) -> bool:
        clean_name = name.strip()
        if not clean_name or clean_name in self.profiles:
            return False
        self.profiles[clean_name] = Profile(name=clean_name, apps=[])
        self.save()
        return True

    def remove_profile(self, name: str) -> bool:
        if name not in self.profiles or len(self.profiles) <= 1:
            return False
        del self.profiles[name]
        if self.active_profile == name:
            self.active_profile = next(iter(self.profiles.keys()))
        self.save()
        return True

    def rename_profile(self, old_name: str, new_name: str) -> bool:
        clean_name = new_name.strip()
        if not clean_name or old_name not in self.profiles or clean_name in self.profiles:
            return False
        profile = self.profiles.pop(old_name)
        profile.name = clean_name
        self.profiles[clean_name] = profile
        if self.active_profile == old_name:
            self.active_profile = clean_name
        self.save()
        return True

    def add_app_to_profile(self, profile_name: str, app: AppEntry) -> bool:
        if profile_name not in self.profiles:
            return False
        self.profiles[profile_name].apps.append(app)
        self.save()
        return True

    def remove_app_from_profile(self, profile_name: str, app_id: str) -> bool:
        if profile_name not in self.profiles:
            return False
        profile = self.profiles[profile_name]
        initial_count = len(profile.apps)
        profile.apps = [a for a in profile.apps if a.id != app_id]
        if len(profile.apps) != initial_count:
            self.save()
            return True
        return False

    def update_app_in_profile(self, profile_name: str, updated_app: AppEntry) -> bool:
        if profile_name not in self.profiles:
            return False
        profile = self.profiles[profile_name]
        for idx, app in enumerate(profile.apps):
            if app.id == updated_app.id:
                profile.apps[idx] = updated_app
                self.save()
                return True
        return False
