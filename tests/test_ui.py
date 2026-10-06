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

    def test_app_dialog_add_and_close_workflow(self):
        from ui.app_dialog import AppDialog
        from config import AppEntry

        added_apps = []
        dlg = AppDialog(on_app_added=lambda app: added_apps.append(app))
        dlg.show()
        self.assertEqual(dlg.add_btn.text(), "Add")
        self.assertEqual(dlg.close_btn.text(), "Close")

        # Simulate adding an application
        dlg.name_input.setText("App One")
        dlg.cmd_input.setText("app-one")
        dlg.add_btn.click()

        self.assertEqual(len(added_apps), 1)
        self.assertEqual(added_apps[0].name, "App One")
        self.assertTrue(dlg.feedback_label.isVisible())
        self.assertIn("1 added", dlg.feedback_label.text())

        # Simulate adding a second application
        dlg.name_input.setText("App Two")
        dlg.cmd_input.setText("app-two")
        dlg.add_btn.click()

        self.assertEqual(len(added_apps), 2)
        self.assertEqual(added_apps[1].name, "App Two")
        self.assertIn("2 added", dlg.feedback_label.text())

        # Simulate closing
        dlg.close_btn.click()
        self.assertFalse(dlg.isVisible())

        # Verify Edit Mode uses Cancel and Save
        existing = AppEntry(name="Existing App", command="existing-cmd")
        edit_dlg = AppDialog(app_entry=existing)
        self.assertEqual(edit_dlg.cancel_btn.text(), "Cancel")
        self.assertEqual(edit_dlg.save_btn.text(), "Save")
        edit_dlg.close()

    def test_default_profile_ui_workflow(self):
        from ui.settings_dialog import SettingsDialog

        self.cfg.add_profile("Work")
        win = MainWindow(self.cfg, autostart_mode=False)
        win.show()

        # Initially "Default" is default profile and active profile
        self.assertEqual(self.cfg.default_profile, "Default")
        self.assertEqual(win.set_default_btn.text(), "Default")
        self.assertFalse(win.set_default_btn.isEnabled())
        self.assertIn("Default (Default)", win.profile_combo.currentText())

        # Switch to "Work" profile
        work_idx = win.profile_combo.findData("Work")
        self.assertGreaterEqual(work_idx, 0)
        win.profile_combo.setCurrentIndex(work_idx)

        self.assertEqual(self.cfg.active_profile, "Work")
        self.assertEqual(win.set_default_btn.text(), "Set Default")
        self.assertTrue(win.set_default_btn.isEnabled())

        # Click Set Default button
        win.set_default_btn.click()
        self.assertEqual(self.cfg.default_profile, "Work")
        self.assertEqual(win.set_default_btn.text(), "Default")
        self.assertFalse(win.set_default_btn.isEnabled())
        self.assertIn("Work (Default)", win.profile_combo.currentText())

        # Verify SettingsDialog shows default profile combo
        settings_dlg = SettingsDialog(self.cfg, win)
        self.assertEqual(settings_dlg.default_profile_combo.currentText(), "Work")
        def_idx = settings_dlg.default_profile_combo.findText("Default")
        settings_dlg.default_profile_combo.setCurrentIndex(def_idx)
        settings_dlg._on_save()
        self.assertEqual(self.cfg.default_profile, "Default")

        settings_dlg.close()
        win.close()

    def test_app_dialog_two_column_table(self):
        from ui.app_dialog import AppDialog
        dlg = AppDialog()
        self.assertEqual(dlg.app_list_widget.columnCount(), 2)
        self.assertGreater(dlg.app_list_widget.count(), 0)
        # Verify first item is custom command
        item_0_0 = dlg.app_list_widget.item(0, 0)
        self.assertIsNotNone(item_0_0)
        self.assertIn("Custom Command", item_0_0.text())
        dlg.close()
