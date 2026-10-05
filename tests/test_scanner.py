"""Tests for DesktopScanner and desktop file parsing."""

import shutil
import tempfile
import unittest
from pathlib import Path

from desktop_scanner import DesktopScanner, clean_desktop_exec


class TestDesktopScanner(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.desktop_file = Path(self.test_dir) / "test-app.desktop"
        content = """[Desktop Entry]
Version=1.0
Type=Application
Name=Test Application
GenericName=Test Generic
Comment=A sample app
Exec=/usr/bin/test-app --arg %u %F
Icon=test-icon
StartupWMClass=testapp
X-KDE-Wayland-AppId=testapp
"""
        with open(self.desktop_file, "w", encoding="utf-8") as f:
            f.write(content)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_clean_exec(self):
        raw = "/usr/bin/zen --no-remote -P YT %u %F"
        cleaned = clean_desktop_exec(raw)
        self.assertEqual(cleaned, "/usr/bin/zen --no-remote -P YT")

    def test_parse_desktop_file(self):
        info = DesktopScanner.parse_desktop_file(self.desktop_file)
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "Test Application")
        self.assertEqual(info.generic_name, "Test Generic")
        self.assertEqual(info.clean_command, "/usr/bin/test-app --arg")
        self.assertEqual(info.icon_name, "test-icon")
        self.assertEqual(info.startup_wm_class, "testapp")
        self.assertEqual(info.kde_app_id, "testapp")


if __name__ == "__main__":
    unittest.main()
