"""Tests for AppLauncher command generation."""

import unittest

from config import AppEntry
from launcher import AppLauncher


class TestAppLauncher(unittest.TestCase):

    def test_launch_command_desktop_entry(self):
        app = AppEntry(
            name="Zen Browser (YouTube)",
            desktop_file="zen-youtube.desktop",
            delay_seconds=0,
        )
        args, use_shell = AppLauncher.get_launch_command(app)
        self.assertFalse(use_shell)
        self.assertEqual(args[0], "/bin/sh")
        self.assertEqual(args[1], "-c")
        self.assertIn('gtk-launch "zen-youtube.desktop"', args[2])

    def test_launch_command_with_delay(self):
        app = AppEntry(
            name="Zen Browser (YouTube)",
            desktop_file="zen-youtube.desktop",
            delay_seconds=5,
        )
        args, use_shell = AppLauncher.get_launch_command(app)
        self.assertIn("sleep 5 && exec", args[2])

    def test_launch_custom_command(self):
        app = AppEntry(
            name="Custom Script",
            command="python3 my_script.py",
            desktop_file="",
            delay_seconds=0,
        )
        args, use_shell = AppLauncher.get_launch_command(app)
        self.assertIn("exec python3 my_script.py", args[2])


if __name__ == "__main__":
    unittest.main()
