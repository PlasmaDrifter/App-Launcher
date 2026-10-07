"""Settings dialog for AutoLaunch.

Configures countdown duration, auto-launch enablement, and desktop autostart.
Strictly dynamic path handling (no hardcoded user paths).
"""

import threading
from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel,
    QListView, QMessageBox, QPushButton, QVBoxLayout, QWidget
)

from autostart import AutostartManager
from config import ConfigManager
from ui.frameless import FramelessDialogBase
from ui.themes import (
    CHECKMARK_ICON_PATH,
    build_primary_btn_stylesheet,
    get_theme,
)
from ui.widgets import HelpBadge, StepperSpinBox
from updater import APP_VERSION, GITHUB_REPO, apply_self_update, check_github_update, restart_application


class SettingsDialog(FramelessDialogBase):
    """Dialog for editing global AutoLaunch settings."""

    _update_check_done_signal = pyqtSignal(dict)
    _update_apply_done_signal = pyqtSignal(bool, str)
    dismiss_changed = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent, title="AutoLaunch Settings")
        self.config_manager = config_manager
        self._target_update_tag = ""
        self._update_check_done_signal.connect(self._handle_update_check_result)
        self._update_apply_done_signal.connect(self._handle_update_apply_result)
        self.setMinimumWidth(500)
        self.resize(500, 680)

        self._init_ui()
        self._apply_dialog_theme(self.config_manager.theme)

        cached = check_github_update(force=False)
        if cached.get("ok") and cached.get("has_update"):
            self._handle_update_check_result(cached)

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
                color: #d4d4d8;
                font-size: 14px;
                font-weight: 600;
                background-color: #0b0f19;
            }
            QLabel {
                color: #d4d4d8;
            }
            QCheckBox {
                color: #d4d4d8;
                font-size: 13px;
                font-weight: 500;
                spacing: 9px;
            }
        """

        # Countdown Group
        self.countdown_group = QGroupBox("Countdown && Auto-Launch Timer")
        self.countdown_group.setStyleSheet(grp_style)
        countdown_vbox = QVBoxLayout(self.countdown_group)
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

        self.spacebar_hint_lbl = QLabel("Use the spacebar to pause")
        self.spacebar_hint_lbl.setStyleSheet("color: #71717a; font-size: 11px; margin-left: 28px; margin-top: -4px;")
        countdown_vbox.addWidget(self.spacebar_hint_lbl)

        duration_layout = QHBoxLayout()
        duration_layout.setContentsMargins(0, 0, 0, 0)
        duration_layout.setSpacing(8)
        duration_lbl = QLabel("Timer duration:")
        duration_lbl.setStyleSheet("color: #d4d4d8; font-size: 14px; font-weight: 600;")
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

        main_layout.addWidget(self.countdown_group)

        # Autostart Group
        self.autostart_group = QGroupBox("Desktop Startup Integration")
        self.autostart_group.setStyleSheet(grp_style)
        autostart_layout = QVBoxLayout(self.autostart_group)
        autostart_layout.setSpacing(8)

        self.autostart_check = QCheckBox("Start AutoLaunch on system boot / login")
        self.autostart_check.setChecked(AutostartManager.is_autostart_enabled())
        autostart_layout.addLayout(make_setting_row(
            self.autostart_check,
            "Places AutoLaunch in your desktop autostart so this window appears on login."
        ))

        install_menu_btn = QPushButton("Register AutoLaunch in Application Menu")
        install_menu_btn.setFixedHeight(30)
        install_menu_btn.setStyleSheet("""
            QPushButton {
                background-color: #202024;
                color: #d4d4d8;
                border: 1px solid #2f2f37;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #28282e;
                border-color: #475569;
                color: #d4d4d8;
            }
        """)
        install_menu_btn.clicked.connect(self._install_desktop_entry)
        autostart_layout.addWidget(install_menu_btn)

        main_layout.addWidget(self.autostart_group)

        # Application Window Behavior Group
        self.behavior_group = QGroupBox("Application Window Behavior")
        self.behavior_group.setStyleSheet(grp_style)
        behavior_layout = QVBoxLayout(self.behavior_group)
        behavior_layout.setSpacing(8)

        self.launch_minimized_check = QCheckBox("Launch all applications minimized")
        self.launch_minimized_check.setChecked(self.config_manager.launch_minimized)
        behavior_layout.addLayout(make_setting_row(
            self.launch_minimized_check,
            "When checked, all launched applications will be minimized to the taskbar upon opening. "
            "You can also configure this individually per application."
        ))

        main_layout.addWidget(self.behavior_group)

        # Startup Profile Group
        self.profile_group = QGroupBox("Default Profile")
        self.profile_group.setStyleSheet(grp_style)
        profile_layout = QVBoxLayout(self.profile_group)
        profile_layout.setSpacing(8)

        prof_select_layout = QHBoxLayout()
        prof_select_layout.setContentsMargins(0, 0, 0, 0)
        prof_select_layout.setSpacing(8)
        prof_lbl = QLabel("Startup profile:")
        prof_lbl.setStyleSheet("color: #d4d4d8; font-size: 14px; font-weight: 600;")
        prof_select_layout.addWidget(prof_lbl)

        self.default_profile_combo = QComboBox()
        self.default_profile_combo.setView(QListView())
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

        main_layout.addWidget(self.profile_group)

        # About & Updates Group
        self.about_group = QGroupBox("About && Updates")
        self.about_group.setStyleSheet(grp_style)
        about_layout = QVBoxLayout(self.about_group)
        about_layout.setSpacing(14)

        # Row 1: Clickable GitHub Link & Check for Updates
        link_row = QHBoxLayout()
        link_row.setContentsMargins(0, 0, 0, 0)
        link_row.setSpacing(8)
        link_lbl = QLabel("GitHub:")
        link_lbl.setStyleSheet("color: #d4d4d8; font-size: 13px; font-weight: 600;")
        self.link_url_lbl = QLabel(
            f'<a href="https://github.com/{GITHUB_REPO}" style="color: #6297bf; text-decoration: underline;">{GITHUB_REPO}</a>'
        )
        self.link_url_lbl.setOpenExternalLinks(True)
        self.link_url_lbl.setStyleSheet("font-size: 13px;")
        link_row.addWidget(link_lbl)
        link_row.addWidget(self.link_url_lbl)
        link_row.addStretch()

        self.check_updates_btn = QPushButton("Check for Updates")
        self.check_updates_btn.setFixedSize(140, 28)
        self.check_updates_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #6297bf;
                border: 1px solid rgba(98, 151, 191, 0.4);
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: rgba(70, 115, 150, 0.15);
                border-color: #6297bf;
                color: #cbd5e1;
            }
        """)
        self.check_updates_btn.clicked.connect(self._on_check_for_updates)
        link_row.addWidget(self.check_updates_btn)
        about_layout.addLayout(link_row)

        # Row 2: Installed Version & Update Action
        self.update_row = QHBoxLayout()
        self.update_row.setContentsMargins(0, 0, 0, 0)
        self.update_row.setSpacing(8)

        self.version_status_lbl = QLabel(f"Installed Version: <span style='color: #d4d4d8; font-weight: 600;'>v{APP_VERSION}</span>")
        self.version_status_lbl.setStyleSheet("color: #d4d4d8; font-size: 13px; font-weight: 600;")
        self.update_row.addWidget(self.version_status_lbl)

        self.update_row.addStretch()

        self.dismiss_update_btn = QPushButton("Dismiss")
        self.dismiss_update_btn.setFixedHeight(28)
        self.dismiss_update_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #cbd5e1;
            }
        """)
        self.dismiss_update_btn.clicked.connect(self._on_dismiss_update)
        self.dismiss_update_btn.hide()
        self.update_row.addWidget(self.dismiss_update_btn)

        self.update_now_btn = QPushButton("Update Now")
        self.update_now_btn.setFixedSize(140, 28)
        self.update_now_btn.setStyleSheet("""
            QPushButton {
                background-color: #1b2f29;
                color: #7ab89b;
                border: 1px solid #2e5548;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #244239;
                color: #d1fae5;
                border-color: #3f6e5e;
            }
        """)
        self.update_now_btn.clicked.connect(self._on_apply_update)
        self.update_now_btn.hide()
        self.update_row.addWidget(self.update_now_btn)
        about_layout.addLayout(self.update_row)

        main_layout.addWidget(self.about_group)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)
        main_layout.addLayout(btn_layout)

        self._apply_dialog_theme("modern_minimalist")

    def _apply_dialog_theme(self, theme_key: str = "modern_minimalist") -> None:
        theme = get_theme(theme_key)
        self.setStyleSheet(f"background-color: {theme.bg_base};")
        if hasattr(self, "dialog_header") and self.dialog_header:
            self.dialog_header.setStyleSheet(f"""
                QFrame {{
                    background-color: {theme.bg_header};
                    border: 1px solid {theme.border_subtle};
                    border-radius: 10px;
                    padding: 4px;
                }}
            """)
        if hasattr(self, "title_label") and self.title_label:
            self.title_label.setStyleSheet("color: #d4d4d8; background: transparent; border: none;")

        grp_style = f"""
            QGroupBox {{
                border: 1px solid {theme.border_subtle};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                padding-left: 10px;
                padding-right: 10px;
                padding-bottom: 8px;
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 6px;
                color: #d4d4d8;
                font-size: 14px;
                font-weight: 600;
                background-color: {theme.bg_base};
            }}
            QLabel {{
                color: #d4d4d8;
            }}
            QCheckBox {{
                color: #d4d4d8;
                font-size: 13px;
                font-weight: 500;
                spacing: 9px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #64748b;
                background-color: {theme.bg_surface};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {theme.border_focus};
                background-color: {theme.bg_card};
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid #d4d4d8;
                background-color: #334155;
                image: url("{CHECKMARK_ICON_PATH}");
            }}
            QCheckBox::indicator:checked:hover {{
                border: 2px solid #d4d4d8;
                background-color: #475569;
                image: url("{CHECKMARK_ICON_PATH}");
            }}
        """
        for grp in [
            self.countdown_group,
            self.autostart_group,
            self.behavior_group,
            self.profile_group,
            self.about_group,
        ]:
            grp.setStyleSheet(grp_style)

        if hasattr(self, "spacebar_hint_lbl") and self.spacebar_hint_lbl:
            self.spacebar_hint_lbl.setStyleSheet(f"color: {theme.text_muted}; font-size: 11px; margin-left: 28px; margin-top: -4px;")

        if hasattr(self, "cancel_btn") and self.cancel_btn:
            self.cancel_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.bg_card};
                    color: #d4d4d8;
                    border: 1px solid {theme.border_subtle};
                    border-radius: 6px;
                    padding: 7px 18px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {theme.card_hover};
                    color: #d4d4d8;
                    border-color: {theme.border_focus};
                }}
            """)

        if hasattr(self, "save_btn") and self.save_btn:
            self.save_btn.setStyleSheet(build_primary_btn_stylesheet(theme))

        if hasattr(self, "check_updates_btn") and self.check_updates_btn:
            self.check_updates_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.bg_card};
                    color: {theme.accent_hover};
                    border: 1px solid {theme.accent_border};
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 0 8px;
                }}
                QPushButton:hover {{
                    background-color: {theme.accent_subtle};
                    border-color: {theme.accent_hover};
                    color: #d4d4d8;
                }}
            """)

        if hasattr(self, "dismiss_update_btn") and self.dismiss_update_btn:
            self.dismiss_update_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.bg_card};
                    color: {theme.text_muted};
                    border: 1px solid {theme.border_subtle};
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 500;
                    padding: 0 10px;
                }}
                QPushButton:hover {{
                    background-color: {theme.card_hover};
                    color: {theme.text_primary};
                }}
            """)

        if hasattr(self, "update_now_btn") and self.update_now_btn:
            self.update_now_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme.bg_card};
                    color: {theme.success};
                    border: 1px solid {theme.success};
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 0 8px;
                }}
                QPushButton:hover {{
                    background-color: rgba(74, 222, 128, 0.15);
                    color: {theme.success_hover};
                    border-color: {theme.success_hover};
                }}
            """)

        if hasattr(self, "link_url_lbl") and self.link_url_lbl:
            self.link_url_lbl.setText(
                f'<a href="https://github.com/{GITHUB_REPO}" style="color: {theme.accent_hover}; text-decoration: underline;">{GITHUB_REPO}</a>'
            )

    def _on_countdown_toggled(self, checked: bool) -> None:
        self.countdown_spin.setEnabled(checked)
        self.countdown_autostart_only_check.setEnabled(checked)
        if hasattr(self, "spacebar_hint_lbl") and self.spacebar_hint_lbl:
            self.spacebar_hint_lbl.setEnabled(checked)

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

    def _on_check_for_updates(self) -> None:
        self.check_updates_btn.setEnabled(False)
        self.check_updates_btn.setText("Checking...")
        self.version_status_lbl.setText("Checking GitHub for updates...")

        def _worker():
            res = check_github_update(force=True)
            self._update_check_done_signal.emit(res)

        threading.Thread(target=_worker, daemon=True).start()

    def _handle_update_check_result(self, res: dict) -> None:
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText("Check for Updates")

        if not res.get("ok"):
            self.version_status_lbl.setText(
                f"Installed: <span style='color: #f8fafc;'>v{APP_VERSION}</span> "
                f"<span style='color: #f87171;'>(Check failed: {res.get('error', 'Network error')})</span>"
            )
            self.dismiss_update_btn.hide()
            self.update_now_btn.hide()
            return

        if res.get("has_update"):
            latest = res.get("latest_version", "")
            self._target_update_tag = latest
            is_dismissed = (self.config_manager.dismissed_update_version == latest)
            if is_dismissed:
                self.version_status_lbl.setText(
                    f"Installed: <span style='color: #d4d4d8;'>v{APP_VERSION}</span> "
                    f"| <span style='color: #94a3b8;'>{latest} dismissed</span>"
                )
                self.dismiss_update_btn.setText("Restore")
                self.dismiss_update_btn.show()
                self.update_now_btn.hide()
            else:
                self.version_status_lbl.setText(
                    f"Installed: <span style='color: #d4d4d8;'>v{APP_VERSION}</span> "
                    f"| <span style='color: #38bdf8; font-weight: bold;'>Update: {latest}</span>"
                )
                self.dismiss_update_btn.setText("Dismiss")
                self.dismiss_update_btn.show()
                self.update_now_btn.setText(f"Update to {latest}")
                self.update_now_btn.show()
        else:
            self.version_status_lbl.setText(
                f"Installed: <span style='color: #d4d4d8;'>v{APP_VERSION}</span> "
                f"<span style='color: #4ade80;'> (Up to date)</span>"
            )
            self.dismiss_update_btn.hide()
            self.update_now_btn.hide()

    def _on_dismiss_update(self) -> None:
        latest = self._target_update_tag
        if not latest:
            return

        if self.config_manager.dismissed_update_version == latest:
            # Undismiss / Restore
            self.config_manager.dismissed_update_version = None
            self.config_manager.save()
            self.version_status_lbl.setText(
                f"Installed: <span style='color: #d4d4d8;'>v{APP_VERSION}</span> "
                f"| <span style='color: #38bdf8; font-weight: bold;'>Update: {latest}</span>"
            )
            self.dismiss_update_btn.setText("Dismiss")
            self.update_now_btn.setText(f"Update to {latest}")
            self.update_now_btn.show()
        else:
            # Dismiss
            self.config_manager.dismissed_update_version = latest
            self.config_manager.save()
            self.version_status_lbl.setText(
                f"Installed: <span style='color: #d4d4d8;'>v{APP_VERSION}</span> "
                f"| <span style='color: #94a3b8;'>{latest} dismissed</span>"
            )
            self.dismiss_update_btn.setText("Restore")
            self.update_now_btn.hide()

        self.dismiss_changed.emit()

    def _on_apply_update(self) -> None:
        tag = self._target_update_tag or "latest"
        reply = QMessageBox.question(
            self,
            "Confirm Update",
            f"Are you sure you want to update AutoLaunch to {tag}?\n\nThe application will update and restart automatically.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.update_now_btn.setEnabled(False)
        self.check_updates_btn.setEnabled(False)
        self.update_now_btn.setText("Updating...")
        self.version_status_lbl.setText("<span style='color: #38bdf8;'>Downloading and installing update...</span>")

        def _worker():
            try:
                apply_self_update(self._target_update_tag)
                self._update_apply_done_signal.emit(True, "")
            except Exception as e:
                self._update_apply_done_signal.emit(False, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _handle_update_apply_result(self, success: bool, err_str: str) -> None:
        tag = self._target_update_tag or "latest"
        if success:
            self.version_status_lbl.setText(
                "<span style='color: #4ade80;'>Update successful! Restarting...</span>"
            )
            restart_application()
        else:
            self.update_now_btn.setEnabled(True)
            self.check_updates_btn.setEnabled(True)
            self.update_now_btn.setText(f"Update to {tag}")
            self.version_status_lbl.setText(
                f"<span style='color: #f87171;'>Update failed: {err_str}</span>"
            )
            QMessageBox.critical(self, "Update Failed", f"Failed to apply update:\n{err_str}")
