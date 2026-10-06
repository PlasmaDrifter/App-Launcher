"""Settings dialog for AutoLaunch.

Configures countdown duration, auto-launch enablement, and desktop autostart.
Strictly dynamic path handling (no hardcoded user paths).
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QCheckBox, QGroupBox, QFormLayout, QMessageBox, QWidget,
    QComboBox
)

from autostart import AutostartManager
from config import ConfigManager
from ui.frameless import FramelessDialogBase


class SettingsDialog(FramelessDialogBase):
    """Dialog for editing global AutoLaunch settings."""

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent, title="AutoLaunch Settings")
        self.config_manager = config_manager
        self.setMinimumWidth(500)
        self.resize(520, 780)

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = self.content_layout
        main_layout.setSpacing(14)

        # Countdown Group
        countdown_group = QGroupBox("Countdown & Auto-Launch Timer")
        countdown_vbox = QVBoxLayout(countdown_group)
        countdown_vbox.setSpacing(10)

        self.enable_countdown_check = QCheckBox("Automatically launch apps after countdown timer")
        self.enable_countdown_check.setChecked(self.config_manager.enable_countdown)
        self.enable_countdown_check.toggled.connect(self._on_countdown_toggled)
        countdown_vbox.addWidget(self.enable_countdown_check)

        countdown_desc = QLabel(
            "When enabled, opening AutoLaunch starts a countdown bar. When it reaches 0s, "
            "it launches your apps and exits. If unchecked, the app waits on screen until you "
            "manually click 'Launch All Apps Now'."
        )
        countdown_desc.setWordWrap(True)
        countdown_desc.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 20px;")
        countdown_vbox.addWidget(countdown_desc)

        duration_layout = QHBoxLayout()
        duration_layout.setContentsMargins(20, 0, 0, 0)
        duration_lbl = QLabel("Timer duration:")
        duration_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        duration_layout.addWidget(duration_lbl)

        from ui.widgets import StepperSpinBox
        self.countdown_spin = StepperSpinBox(
            minimum=1,
            maximum=120,
            value=self.config_manager.countdown_seconds,
            suffix=" seconds",
            step=1
        )
        self.countdown_spin.setEnabled(self.config_manager.enable_countdown)
        duration_layout.addWidget(self.countdown_spin)
        duration_layout.addStretch()
        countdown_vbox.addLayout(duration_layout)

        main_layout.addWidget(countdown_group)

        # Autostart Group
        autostart_group = QGroupBox("Desktop Startup Integration")
        autostart_layout = QVBoxLayout(autostart_group)
        autostart_layout.setSpacing(10)

        self.autostart_check = QCheckBox("Start AutoLaunch on system boot / login")
        self.autostart_check.setChecked(AutostartManager.is_autostart_enabled())
        autostart_layout.addWidget(self.autostart_check)

        autostart_desc = QLabel(
            "Places autolaunch in your desktop autostart so this window appears on login."
        )
        autostart_desc.setWordWrap(True)
        autostart_desc.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 20px;")
        autostart_layout.addWidget(autostart_desc)

        install_menu_btn = QPushButton("Register AutoLaunch in Application Menu")
        install_menu_btn.clicked.connect(self._install_desktop_entry)
        autostart_layout.addWidget(install_menu_btn)

        main_layout.addWidget(autostart_group)

        # Application Window Behavior Group
        behavior_group = QGroupBox("Application Window Behavior")
        behavior_layout = QVBoxLayout(behavior_group)
        behavior_layout.setSpacing(10)

        self.launch_minimized_check = QCheckBox("Launch all applications minimized")
        self.launch_minimized_check.setChecked(self.config_manager.launch_minimized)
        behavior_layout.addWidget(self.launch_minimized_check)

        behavior_desc = QLabel(
            "When checked, all launched applications will be minimized to the taskbar upon opening. "
            "You can also configure this individually per application."
        )
        behavior_desc.setWordWrap(True)
        behavior_desc.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 20px;")
        behavior_layout.addWidget(behavior_desc)

        main_layout.addWidget(behavior_group)

        # Appearance / Visual Theme Group
        theme_group = QGroupBox("Appearance / Interface Style")
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setSpacing(8)

        theme_picker_layout = QHBoxLayout()
        theme_lbl = QLabel("Interface Look:")
        theme_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        theme_picker_layout.addWidget(theme_lbl)

        self.style_combo = QComboBox()
        self.style_combo.addItem("Modern Acrylic (Cards & Toggles)", "modern")
        self.style_combo.addItem("Classic Plain (Standard Desktop Rows)", "classic")
        current_style = getattr(self.config_manager, "ui_style", "modern")
        if current_style == "classic":
            self.style_combo.setCurrentIndex(1)
        else:
            self.style_combo.setCurrentIndex(0)
        theme_picker_layout.addWidget(self.style_combo)
        theme_picker_layout.addStretch()
        theme_layout.addLayout(theme_picker_layout)

        theme_desc = QLabel(
            "Switch between the sleek modern acrylic portrait card design and the original clean, "
            "plain desktop row interface without losing any profiles or settings."
        )
        theme_desc.setWordWrap(True)
        theme_desc.setStyleSheet("color: #64748b; font-size: 11px;")
        theme_layout.addWidget(theme_desc)

        main_layout.addWidget(theme_group)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Settings")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 7px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #3b82f6);
            }
        """)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

    def _on_countdown_toggled(self, checked: bool) -> None:
        self.countdown_spin.setEnabled(checked)

    def _install_desktop_entry(self) -> None:
        success = AutostartManager.install_desktop_entry()
        if success:
            QMessageBox.information(
                self,
                "Success",
                "AutoLaunch desktop entry has been installed to your application menu (~/.local/share/applications/autolaunch.desktop)."
            )
        else:
            QMessageBox.critical(self, "Error", "Failed to write desktop entry.")

    def _on_save(self) -> None:
        self.config_manager.enable_countdown = self.enable_countdown_check.isChecked()
        self.config_manager.countdown_seconds = self.countdown_spin.value()
        self.config_manager.launch_minimized = self.launch_minimized_check.isChecked()
        self.config_manager.autostart_enabled = self.autostart_check.isChecked()
        self.config_manager.ui_style = str(self.style_combo.currentData() or "modern")

        # Update system autostart desktop file
        AutostartManager.set_autostart(self.autostart_check.isChecked())

        self.config_manager.save()
        self.accept()
