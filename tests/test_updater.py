"""Tests for the AutoLaunch dual-mode self-updater."""

import unittest
from unittest.mock import patch, MagicMock

from updater import (
    parse_version_tuple,
    is_newer_version,
    check_github_update,
    UPDATE_CACHE,
    APP_VERSION
)


class TestUpdater(unittest.TestCase):
    def test_version_tuple_parsing(self):
        self.assertEqual(parse_version_tuple("0.1.5"), (0, 1, 5))
        self.assertEqual(parse_version_tuple("v0.1.5"), (0, 1, 5))
        self.assertEqual(parse_version_tuple("v0.2.0"), (0, 2, 0))
        self.assertEqual(parse_version_tuple("1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version_tuple("v0.8.12"), (0, 8, 12))

    def test_version_comparison(self):
        self.assertTrue(is_newer_version("v0.1.6", "0.1.5"))
        self.assertTrue(is_newer_version("0.2.0", "0.1.5"))
        self.assertTrue(is_newer_version("v1.0.0", "0.1.5"))

        self.assertFalse(is_newer_version("v0.1.5", "0.1.5"))
        self.assertFalse(is_newer_version("0.1.4", "0.1.5"))
        self.assertFalse(is_newer_version("0.1.0", "0.1.5"))

    def test_check_github_update_cached(self):
        with UPDATE_CACHE["lock"]:
            UPDATE_CACHE["last_checked"] = 9999999999
            UPDATE_CACHE["has_update"] = False
            UPDATE_CACHE["latest_version"] = "v0.1.5"
            UPDATE_CACHE["release_url"] = "https://github.com/PlasmaDrifter/AutoLaunch/releases"

        res = check_github_update(force=False)
        self.assertTrue(res["ok"])
        self.assertFalse(res["has_update"])
        self.assertEqual(res["latest_version"], "v0.1.5")

    def test_config_dismissed_update_persistence(self):
        import tempfile
        from pathlib import Path
        from config import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = ConfigManager(config_dir=Path(tmpdir))
            self.assertIsNone(cfg.dismissed_update_version)

            cfg.dismissed_update_version = "v0.1.6"
            cfg.save()

            cfg2 = ConfigManager(config_dir=Path(tmpdir))
            self.assertEqual(cfg2.dismissed_update_version, "v0.1.6")

    def test_dismissed_update_filtering(self):
        from config import ConfigManager
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = ConfigManager(config_dir=Path(tmpdir))
            latest = "v0.1.6"

            # Initially not dismissed -> notification active
            has_notification = (cfg.dismissed_update_version != latest)
            self.assertTrue(has_notification)

            # User dismisses v0.1.6
            cfg.dismissed_update_version = latest
            cfg.save()
            has_notification = (cfg.dismissed_update_version != latest)
            self.assertFalse(has_notification)

            # New update v0.1.7 arrives later -> notification should trigger again!
            new_latest = "v0.1.7"
            has_notification = (cfg.dismissed_update_version != new_latest)
            self.assertTrue(has_notification)


if __name__ == "__main__":
    unittest.main()
