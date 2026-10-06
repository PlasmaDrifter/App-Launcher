"""Tests for ConfigManager and data models."""

import shutil
import tempfile
import unittest
from pathlib import Path

from config import AppEntry, ConfigManager


class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.test_dir) / "autolaunch"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_initialization(self):
        mgr = ConfigManager(self.config_dir)
        self.assertEqual(mgr.active_profile, "Default")
        self.assertEqual(mgr.countdown_seconds, 5)
        self.assertTrue(mgr.enable_countdown)
        self.assertTrue(mgr.countdown_autostart_only)
        self.assertIn("Default", mgr.profiles)
        self.assertTrue((self.config_dir / "config.json").is_file())

    def test_add_and_remove_profile(self):
        mgr = ConfigManager(self.config_dir)
        self.assertTrue(mgr.add_profile("Work"))
        self.assertIn("Work", mgr.profiles)
        self.assertFalse(mgr.add_profile("Work"))  # Duplicate

        self.assertTrue(mgr.set_active_profile("Work"))
        self.assertEqual(mgr.active_profile, "Work")

        self.assertTrue(mgr.remove_profile("Default"))
        self.assertNotIn("Default", mgr.profiles)
        # Cannot delete the last remaining profile
        self.assertFalse(mgr.remove_profile("Work"))

    def test_app_entries_in_profile(self):
        mgr = ConfigManager(self.config_dir)
        app = AppEntry(
            name="Zen Browser (YouTube)",
            command="zen-youtube",
            desktop_file="zen-youtube.desktop",
            icon="zen-youtube",
            enabled=True,
            delay_seconds=2,
        )
        self.assertTrue(mgr.add_app_to_profile("Default", app))
        prof = mgr.get_current_profile()
        self.assertEqual(len(prof.apps), 1)
        self.assertEqual(prof.apps[0].name, "Zen Browser (YouTube)")
        self.assertEqual(prof.apps[0].delay_seconds, 2)

        # Reload from disk
        mgr2 = ConfigManager(self.config_dir)
        prof2 = mgr2.get_current_profile()
        self.assertEqual(len(prof2.apps), 1)
        self.assertEqual(prof2.apps[0].name, "Zen Browser (YouTube)")

        # Update app
        app.name = "Zen YouTube Updated"
        self.assertTrue(mgr2.update_app_in_profile("Default", app))
        self.assertEqual(mgr2.get_current_profile().apps[0].name, "Zen YouTube Updated")

        # Remove app
        self.assertTrue(mgr2.remove_app_from_profile("Default", app.id))
        self.assertEqual(len(mgr2.get_current_profile().apps), 0)

    def test_minimization_settings(self):
        mgr = ConfigManager(self.config_dir)
        self.assertFalse(mgr.launch_minimized)

        # Global toggle
        mgr.launch_minimized = True
        mgr.save()

        mgr2 = ConfigManager(self.config_dir)
        self.assertTrue(mgr2.launch_minimized)

        # Per-app toggle
        app = AppEntry(
            name="Minimized App",
            command="true",
            start_minimized=True,
        )
        self.assertTrue(mgr2.add_app_to_profile("Default", app))
        mgr3 = ConfigManager(self.config_dir)
        saved_app = mgr3.get_current_profile().apps[0]
        self.assertTrue(saved_app.start_minimized)

    def test_countdown_settings(self):
        mgr = ConfigManager(self.config_dir)
        self.assertTrue(mgr.countdown_autostart_only)

        mgr.countdown_autostart_only = False
        mgr.countdown_seconds = 10
        mgr.save()

        mgr2 = ConfigManager(self.config_dir)
        self.assertFalse(mgr2.countdown_autostart_only)
        self.assertEqual(mgr2.countdown_seconds, 10)


if __name__ == "__main__":
    unittest.main()
