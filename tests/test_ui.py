"""Tests for MainWindow keyboard shortcuts and countdown control."""

import shutil
import tempfile
import unittest
from pathlib import Path

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication

from config import ConfigManager
from ui.main_window import MainWindow

app = QApplication.instance()
if app is None:
    app = QApplication([])


class TestMainWindowShortcuts(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.test_dir) / "autolaunch"
        self.cfg = ConfigManager(self.config_dir)
        self.cfg.countdown_seconds = 10
        self.cfg.enable_countdown = True
        self.cfg.countdown_autostart_only = False

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_space_bar_pauses_and_resumes_countdown(self):
        win = MainWindow(self.cfg, autostart_mode=True)
        win.show()
        self.assertTrue(win.countdown_card.isVisible())
        self.assertFalse(win.is_paused)

        # Press space to pause
        evt_press = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier)
        app.sendEvent(win, evt_press)
        self.assertTrue(win.is_paused)
        self.assertIn("Paused", win.countdown_status_label.text())

        # Press space again to resume
        app.sendEvent(win, evt_press)
        self.assertFalse(win.is_paused)
        self.assertIn("Auto-launching", win.countdown_status_label.text())
        win.close()
