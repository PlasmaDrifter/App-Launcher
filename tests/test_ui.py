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

    def test_card_buttons_and_truncation(self):
        from config import AppEntry
        from ui.main_window import AppCardWidget

        long_app = AppEntry(
            id="long-app",
            name="Super Extremely Long Application Title That Exceeds Normal Window Width",
            command="/usr/bin/test",
            delay_seconds=12,
            start_minimized=True
        )
        self.cfg.profiles[self.cfg.active_profile].apps.append(long_app)

        win = MainWindow(self.cfg, autostart_mode=False)
        win.show()
        app.processEvents()

        cards = win.findChildren(AppCardWidget)
        self.assertGreater(len(cards), 0)
        card = cards[-1]

        # Verify buttons are visible and within bounds
        self.assertTrue(card.edit_btn.isVisible())
        self.assertTrue(card.delete_btn.isVisible())
        self.assertLess(card.edit_btn.geometry().right(), card.width())
        self.assertLess(card.delete_btn.geometry().right(), card.width())
        win.close()

    def test_window_default_widths_and_resizer(self):
        from ui.app_dialog import AppDialog
        from PyQt6.QtCore import QPoint

        win = MainWindow(self.cfg, autostart_mode=False)
        self.assertGreaterEqual(win.width(), 600)
        self.assertTrue(hasattr(win, "resize_handler"))

        # Verify edge detection on MainWindow
        handler = win.resize_handler
        self.assertIn("T", handler._get_edge(win, QPoint(300, 2)))
        self.assertIn("B", handler._get_edge(win, QPoint(300, win.height() - 2)))
        self.assertIn("L", handler._get_edge(win, QPoint(2, 400)))
        self.assertIn("R", handler._get_edge(win, QPoint(win.width() - 2, 400)))

        dlg = AppDialog(win)
        self.assertLessEqual(dlg.width(), 800)
        self.assertGreaterEqual(dlg.width(), 640)
        self.assertTrue(hasattr(dlg, "resize_handler"))

        # Verify edge detection on AppDialog
        dlg_handler = dlg.resize_handler
        self.assertIn("T", dlg_handler._get_edge(dlg, QPoint(350, 2)))
        self.assertIn("B", dlg_handler._get_edge(dlg, QPoint(350, dlg.height() - 2)))
        self.assertIn("L", dlg_handler._get_edge(dlg, QPoint(2, 250)))
        self.assertIn("R", dlg_handler._get_edge(dlg, QPoint(dlg.width() - 2, 250)))

        dlg.close()
        win.close()


