"""Settings dialog for AutoLaunch.

Configures countdown duration, auto-launch enablement, and desktop autostart.
Strictly dynamic path handling (no hardcoded user paths).
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QVBoxLayout, QWidget
)

from autostart import AutostartManager
from config import ConfigManager
from ui.frameless import FramelessDialogBase
from ui.widgets import HelpBadge, StepperSpinBox


class SettingsDialog(FramelessDialogBase):
    """Dialog for editing global AutoLaunch settings."""

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent, title="AutoLaunch Settings")
        self.config_manager = config_manager
        self.setMinimumWidth(480)
        self.resize(480, 500)

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = self.content_layout
        main_layout.setSpacing(10)

        def make_setting_row(widget: QWidget, tooltip_text: str) -> QHBoxLayout:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)
            row.addWidget(widget)
            row.addStretch()
            if tooltip_text:
                row.addWidget(HelpBadge(tooltip_text))
            return row

        grp_style = """
            QGroupBox {
                border: 1px solid #1e293b;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                padding-left: 10px;
                padding-right: 10px;
                padding-bottom: 8px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 6px;
                color: #f8fafc;
                font-size: 14px;
                font-weight: 600;
                background-color: #0b0f19;
            }
            QCheckBox {
                color: #f8fafc;
                font-size: 14px;
                font-weight: 600;
                spacing: 9px;
            }
        """

        # Countdown Group
        countdown_group = QGroupBox("Countdown && Auto-Launch Timer")
        countdown_group.setStyleSheet(grp_style)
        countdown_vbox = QVBoxLayout(countdown_group)
        countdown_vbox.setSpacing(8)

        self.enable_countdown_check = QCheckBox("Automatically launch apps after countdown timer")
        self.enable_countdown_check.setChecked(self.config_manager.enable_countdown)
        self.enable_countdown_check.toggled.connect(self._on_countdown_toggled)
        countdown_vbox.addLayout(make_setting_row(
            self.enable_countdown_check,
            "When enabled, opening AutoLaunch starts a countdown bar. When it reaches 0s, "
            "it launches your apps and exits. If unchecked, the app waits on screen until you "
            "manually click 'Launch All Apps Now'."
        ))

        self.countdown_autostart_only_check = QCheckBox("Only activate countdown on desktop login / boot")
        self.countdown_autostart_only_check.setChecked(self.config_manager.countdown_autostart_only)
        self.countdown_autostart_only_check.setEnabled(self.config_manager.enable_countdown)
        countdown_vbox.addLayout(make_setting_row(
            self.countdown_autostart_only_check,
            "When checked, the countdown timer only runs when started automatically on desktop login. "
            "Opening AutoLaunch from the application menu opens in configuration mode without a timer, "
            "so you can make changes at your own pace."
        ))

        duration_layout = QHBoxLayout()
        duration_layout.setContentsMargins(0, 0, 0, 0)
        duration_layout.setSpacing(8)
        duration_lbl = QLabel("Timer duration:")
        duration_lbl.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: 600;")
        duration_layout.addWidget(duration_lbl)

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
        duration_layout.addWidget(HelpBadge("Number of seconds to wait before launching applications."))
        countdown_vbox.addLayout(duration_layout)

        main_layout.addWidget(countdown_group)

        # Autostart Group
        autostart_group = QGroupBox("Desktop Startup Integration")
        autostart_group.setStyleSheet(grp_style)
        autostart_layout = QVBoxLayout(autostart_group)
        autostart_layout.setSpacing(8)

        self.autostart_check = QCheckBox("Start AutoLaunch on system boot / login")
        self.autostart_check.setChecked(AutostartManager.is_autostart_enabled())
        autostart_layout.addLayout(make_setting_row(
            self.autostart_check,
            "Places AutoLaunch in your desktop autostart so this window appears on login."
        ))

        install_menu_btn = QPushButton("Register AutoLaunch in Application Menu")
        install_menu_btn.setFixedHeight(30)
        install_menu_btn.setStyleSheet("color: #f8fafc; font-size: 13px;")
        install_menu_btn.clicked.connect(self._install_desktop_entry)
        autostart_layout.addWidget(install_menu_btn)

        main_layout.addWidget(autostart_group)

        # Application Window Behavior Group
        behavior_group = QGroupBox("Application Window Behavior")
        behavior_group.setStyleSheet(grp_style)
        behavior_layout = QVBoxLayout(behavior_group)
        behavior_layout.setSpacing(8)

        self.launch_minimized_check = QCheckBox("Launch all applications minimized")
        self.launch_minimized_check.setChecked(self.config_manager.launch_minimized)
        behavior_layout.addLayout(make_setting_row(
            self.launch_minimized_check,
            "When checked, all launched applications will be minimized to the taskbar upon opening. "
            "You can also configure this individually per application."
        ))

        main_layout.addWidget(behavior_group)

        # Startup Profile Group
        profile_group = QGroupBox("Default Profile")
        profile_group.setStyleSheet(grp_style)
        profile_layout = QVBoxLayout(profile_group)
        profile_layout.setSpacing(8)

        prof_select_layout = QHBoxLayout()
        prof_select_layout.setContentsMargins(0, 0, 0, 0)
        prof_select_layout.setSpacing(8)
        prof_lbl = QLabel("Startup profile:")
        prof_lbl.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: 600;")
        prof_select_layout.addWidget(prof_lbl)

        self.default_profile_combo = QComboBox()
        self.default_profile_combo.setFixedHeight(28)
        self.default_profile_combo.setMinimumWidth(160)
        for name in sorted(self.config_manager.profiles.keys()):
            self.default_profile_combo.addItem(name)
        self.default_profile_combo.setCurrentText(self.config_manager.default_profile)
        prof_select_layout.addWidget(self.default_profile_combo)
        prof_select_layout.addStretch()
        prof_select_layout.addWidget(HelpBadge(
            "Specifies which profile is automatically selected and launched when AutoLaunch starts on system boot."
        ))
        profile_layout.addLayout(prof_select_layout)

        main_layout.addWidget(profile_group)

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
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #255577, stop:1 #2d4f7c);
                color: #e2e8f0;
                font-weight: bold;
                border: 1px solid #376388;
                border-radius: 6px;
                padding: 7px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2e668f, stop:1 #375f94);
                border-color: #4578a3;
                color: #ffffff;
            }
        """)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

    def _on_countdown_toggled(self, checked: bool) -> None:
        self.countdown_spin.setEnabled(checked)
        self.countdown_autostart_only_check.setEnabled(checked)

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
        self.config_manager.countdown_autostart_only = self.countdown_autostart_only_check.isChecked()
        self.config_manager.countdown_seconds = self.countdown_spin.value()
        self.config_manager.launch_minimized = self.launch_minimized_check.isChecked()
        self.config_manager.autostart_enabled = self.autostart_check.isChecked()

        # Update system autostart desktop file
        AutostartManager.set_autostart(self.autostart_check.isChecked())

        chosen_profile = self.default_profile_combo.currentText()
        if chosen_profile in self.config_manager.profiles:
            self.config_manager.default_profile = chosen_profile

        self.config_manager.save()
        self.accept()
