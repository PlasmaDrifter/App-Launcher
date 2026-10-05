"""Settings dialog for AutoLaunch.

Configures countdown duration, auto-launch enablement, and desktop autostart.
Strictly dynamic path handling (no hardcoded user paths).
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QCheckBox, QGroupBox, QFormLayout, QMessageBox, QWidget
)

from autostart import AutostartManager
from config import ConfigManager


class SettingsDialog(QDialog):
    """Dialog for editing global AutoLaunch settings."""

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("AutoLaunch Settings")
        self.setMinimumWidth(420)

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)

        # Countdown Group
        countdown_group = QGroupBox("Countdown & Auto-Launch")
        countdown_form = QFormLayout(countdown_group)

        self.enable_countdown_check = QCheckBox("Enable auto-launch countdown")
        self.enable_countdown_check.setChecked(self.config_manager.enable_countdown)
        self.enable_countdown_check.toggled.connect(self._on_countdown_toggled)

        self.countdown_spin = QSpinBox()
        self.countdown_spin.setRange(1, 120)
        self.countdown_spin.setValue(self.config_manager.countdown_seconds)
        self.countdown_spin.setSuffix(" seconds")
        self.countdown_spin.setEnabled(self.config_manager.enable_countdown)

        countdown_form.addRow(self.enable_countdown_check)
        countdown_form.addRow("Countdown duration:", self.countdown_spin)
        main_layout.addWidget(countdown_group)

        # Autostart Group
        autostart_group = QGroupBox("Desktop Startup Integration")
        autostart_layout = QVBoxLayout(autostart_group)

        self.autostart_check = QCheckBox("Launch AutoLaunch automatically when logging into desktop")
        self.autostart_check.setChecked(AutostartManager.is_autostart_enabled())
        autostart_layout.addWidget(self.autostart_check)

        install_menu_btn = QPushButton("Register AutoLaunch in Application Menu")
        install_menu_btn.clicked.connect(self._install_desktop_entry)
        autostart_layout.addWidget(install_menu_btn)

        main_layout.addWidget(autostart_group)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Settings")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(cancel_btn)
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
        self.config_manager.autostart_enabled = self.autostart_check.isChecked()

        # Update system autostart desktop file
        AutostartManager.set_autostart(self.autostart_check.isChecked())

        self.config_manager.save()
        self.accept()
