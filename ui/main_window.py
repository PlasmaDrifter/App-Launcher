"""Main window for AutoLaunch.

Provides an intuitive desktop interface to manage, toggle, reorder,
and launch configured startup applications with profiles and a countdown timer.
"""

from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QListWidget, QListWidgetItem,
    QProgressBar, QMessageBox, QFrame, QSizePolicy, QApplication
)

from config import AppEntry, ConfigManager
from launcher import AppLauncher
from ui.app_dialog import AppDialog
from ui.icon_utils import resolve_icon
from ui.profile_dialog import ProfileDialog
from ui.settings_dialog import SettingsDialog


class AppRowWidget(QWidget):
    """Custom widget representing an application in the list."""

    def __init__(self, app: AppEntry, parent_window: "MainWindow"):
        super().__init__()
        self.app = app
        self.parent_window = parent_window
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)

        # Enabled Checkbox
        self.checkbox = QPushButton()
        self.checkbox.setCheckable(True)
        self.checkbox.setChecked(self.app.enabled)
        self.checkbox.setFixedSize(24, 24)
        self.checkbox.setStyleSheet("""
            QPushButton {
                border: 2px solid #555;
                border-radius: 4px;
                background-color: transparent;
            }
            QPushButton:checked {
                background-color: #3daee9;
                border-color: #3daee9;
            }
        """)
        self.checkbox.toggled.connect(self._on_toggled)
        layout.addWidget(self.checkbox)

        # App Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(36, 36)
        icon = resolve_icon(self.app.icon, self.app.desktop_file)
        pixmap = icon.pixmap(QSize(36, 36))
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setScaledContents(True)
        layout.addWidget(self.icon_label)

        # Name and Command Label
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)

        self.name_label = QLabel(self.app.name)
        bold_font = QFont()
        bold_font.setBold(True)
        bold_font.setPointSize(11)
        self.name_label.setFont(bold_font)
        name_layout.addWidget(self.name_label)

        if self.app.delay_seconds > 0:
            delay_badge = QLabel(f"+{self.app.delay_seconds}s delay")
            delay_badge.setStyleSheet(
                "background-color: #3a3f44; color: #8ec07c; "
                "border-radius: 4px; padding: 2px 6px; font-size: 10px;"
            )
            name_layout.addWidget(delay_badge)

        name_layout.addStretch()
        text_layout.addLayout(name_layout)

        subtitle_text = self.app.desktop_file or self.app.command
        self.subtitle_label = QLabel(subtitle_text)
        self.subtitle_label.setStyleSheet("color: #888; font-size: 11px;")
        text_layout.addWidget(self.subtitle_label)

        layout.addLayout(text_layout, stretch=1)

        # Move Up / Down Buttons
        self.up_btn = QPushButton("▲")
        self.up_btn.setFixedSize(28, 28)
        self.up_btn.setToolTip("Move application up in launch order")
        self.up_btn.clicked.connect(self._on_move_up)
        layout.addWidget(self.up_btn)

        self.down_btn = QPushButton("▼")
        self.down_btn.setFixedSize(28, 28)
        self.down_btn.setToolTip("Move application down in launch order")
        self.down_btn.clicked.connect(self._on_move_down)
        layout.addWidget(self.down_btn)

        # Edit Button
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setFixedSize(54, 28)
        self.edit_btn.clicked.connect(self._on_edit)
        layout.addWidget(self.edit_btn)

        # Delete Button
        self.delete_btn = QPushButton("Remove")
        self.delete_btn.setFixedSize(68, 28)
        self.delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(self.delete_btn)

    def _on_toggled(self, checked: bool) -> None:
        self.app.enabled = checked
        self.parent_window.on_app_toggled(self.app)

    def _on_move_up(self) -> None:
        self.parent_window.move_app(self.app, -1)

    def _on_move_down(self) -> None:
        self.parent_window.move_app(self.app, 1)

    def _on_edit(self) -> None:
        self.parent_window.edit_app(self.app)

    def _on_delete(self) -> None:
        self.parent_window.delete_app(self.app)


class MainWindow(QMainWindow):
    """Main window for AutoLaunch."""

    def __init__(self, config_manager: ConfigManager, autostart_mode: bool = False):
        super().__init__()
        self.config_manager = config_manager
        self.autostart_mode = autostart_mode

        self.remaining_seconds = self.config_manager.countdown_seconds
        self.is_paused = False

        self.setWindowTitle("AutoLaunch")
        self.setMinimumSize(680, 520)

        # Countdown timer (ticks every 1000ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer_tick)

        self._init_ui()
        self._load_profiles_combo()
        self._refresh_app_list()

        # Start countdown if enabled in configuration
        if self.config_manager.enable_countdown and self.config_manager.countdown_seconds > 0:
            self._start_countdown()
        else:
            self.countdown_container.hide()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Top Bar: Profile & Global Settings
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        profile_lbl = QLabel("Profile:")
        bold_font = QFont()
        bold_font.setBold(True)
        profile_lbl.setFont(bold_font)
        top_bar.addWidget(profile_lbl)

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(180)
        self.profile_combo.currentTextChanged.connect(self._on_profile_changed)
        top_bar.addWidget(self.profile_combo)

        self.new_profile_btn = QPushButton("New")
        self.new_profile_btn.setToolTip("Create a new profile")
        self.new_profile_btn.clicked.connect(self._on_new_profile)
        top_bar.addWidget(self.new_profile_btn)

        self.rename_profile_btn = QPushButton("Rename")
        self.rename_profile_btn.setToolTip("Rename current profile")
        self.rename_profile_btn.clicked.connect(self._on_rename_profile)
        top_bar.addWidget(self.rename_profile_btn)

        self.delete_profile_btn = QPushButton("Delete")
        self.delete_profile_btn.setToolTip("Delete current profile")
        self.delete_profile_btn.clicked.connect(self._on_delete_profile)
        top_bar.addWidget(self.delete_profile_btn)

        top_bar.addStretch()

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self._on_open_settings)
        top_bar.addWidget(self.settings_btn)

        main_layout.addLayout(top_bar)

        # App List Area
        self.app_list_widget = QListWidget()
        self.app_list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.app_list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #444;
                border-radius: 6px;
                background-color: #232629;
            }
            QListWidget::item {
                border-bottom: 1px solid #31363b;
            }
        """)
        main_layout.addWidget(self.app_list_widget, stretch=1)

        # Placeholder message when empty
        self.empty_label = QLabel(
            "No applications configured in this profile.\n"
            "Click 'Add Application' below to choose apps to launch on startup."
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #888; font-size: 13px; padding: 40px;")
        main_layout.addWidget(self.empty_label)

        # Countdown Progress Area
        self.countdown_container = QFrame()
        self.countdown_container.setStyleSheet("""
            QFrame {
                background-color: #2d3238;
                border: 1px solid #3daee9;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        countdown_layout = QVBoxLayout(self.countdown_container)
        countdown_layout.setContentsMargins(10, 8, 10, 8)
        countdown_layout.setSpacing(6)

        countdown_header = QHBoxLayout()
        self.countdown_status_label = QLabel("Auto-launching in 5 seconds...")
        countdown_header.addWidget(self.countdown_status_label)
        countdown_header.addStretch()

        self.pause_resume_btn = QPushButton("Pause")
        self.pause_resume_btn.setFixedWidth(70)
        self.pause_resume_btn.clicked.connect(self._toggle_pause_countdown)
        countdown_header.addWidget(self.pause_resume_btn)

        self.cancel_countdown_btn = QPushButton("Cancel Timer")
        self.cancel_countdown_btn.clicked.connect(self._cancel_countdown)
        countdown_header.addWidget(self.cancel_countdown_btn)

        countdown_layout.addLayout(countdown_header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, max(1, self.config_manager.countdown_seconds))
        self.progress_bar.setValue(self.config_manager.countdown_seconds)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #1b1e20;
            }
            QProgressBar::chunk {
                background-color: #3daee9;
                border-radius: 4px;
            }
        """)
        countdown_layout.addWidget(self.progress_bar)

        main_layout.addWidget(self.countdown_container)

        # Bottom Action Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.add_app_btn = QPushButton("Add Application")
        self.add_app_btn.setFixedHeight(34)
        self.add_app_btn.clicked.connect(self._on_add_app)
        bottom_bar.addWidget(self.add_app_btn)

        bottom_bar.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedHeight(34)
        self.close_btn.setToolTip("Close AutoLaunch without launching applications")
        self.close_btn.clicked.connect(self.close)
        bottom_bar.addWidget(self.close_btn)

        self.launch_now_btn = QPushButton("Launch Selected Now")
        self.launch_now_btn.setFixedHeight(34)
        self.launch_now_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: #ffffff;
                font-weight: bold;
                border: 1px solid #1b5e20;
                border-radius: 4px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
            QPushButton:pressed {
                background-color: #1b5e20;
            }
        """)
        self.launch_now_btn.clicked.connect(self.launch_selected_apps)
        bottom_bar.addWidget(self.launch_now_btn)

        main_layout.addLayout(bottom_bar)

    def _start_countdown(self) -> None:
        self.remaining_seconds = self.config_manager.countdown_seconds
        self.is_paused = False
        self.progress_bar.setRange(0, max(1, self.config_manager.countdown_seconds))
        self.progress_bar.setValue(self.remaining_seconds)
        self.pause_resume_btn.setText("Pause")
        self._update_countdown_label()
        self.countdown_container.show()
        self.timer.start(1000)

    def _update_countdown_label(self) -> None:
        current_profile = self.config_manager.get_current_profile()
        enabled_count = sum(1 for a in current_profile.apps if a.enabled)
        sec_str = "second" if self.remaining_seconds == 1 else "seconds"
        self.countdown_status_label.setText(
            f"Auto-launching in {self.remaining_seconds} {sec_str}... ({enabled_count} apps enabled)"
        )
        self.progress_bar.setValue(self.remaining_seconds)

    def _on_timer_tick(self) -> None:
        if self.is_paused:
            return

        self.remaining_seconds -= 1
        self._update_countdown_label()

        if self.remaining_seconds <= 0:
            self.timer.stop()
            self.launch_selected_apps()

    def _toggle_pause_countdown(self) -> None:
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_resume_btn.setText("Resume")
            self.countdown_status_label.setText(f"Countdown paused at {self.remaining_seconds}s")
        else:
            self.pause_resume_btn.setText("Pause")
            self._update_countdown_label()

    def _cancel_countdown(self) -> None:
        self.timer.stop()
        self.countdown_container.hide()

    def _pause_for_user_action(self) -> None:
        """Pauses the countdown when the user interacts with the UI."""
        if self.timer.isActive() and not self.is_paused:
            self._toggle_pause_countdown()

    def _load_profiles_combo(self) -> None:
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for name in sorted(self.config_manager.profiles.keys()):
            self.profile_combo.addItem(name)
        self.profile_combo.setCurrentText(self.config_manager.active_profile)
        self.profile_combo.blockSignals(False)
        self._update_profile_buttons()

    def _update_profile_buttons(self) -> None:
        has_multiple = len(self.config_manager.profiles) > 1
        self.delete_profile_btn.setEnabled(has_multiple)

    def _on_profile_changed(self, profile_name: str) -> None:
        if profile_name and profile_name in self.config_manager.profiles:
            self.config_manager.set_active_profile(profile_name)
            self._refresh_app_list()

    def _on_new_profile(self) -> None:
        self._pause_for_user_action()
        dialog = ProfileDialog(self, title="Create New Profile")
        if dialog.exec():
            new_name = dialog.get_profile_name()
            if self.config_manager.add_profile(new_name):
                self.config_manager.set_active_profile(new_name)
                self._load_profiles_combo()
                self._refresh_app_list()
            else:
                QMessageBox.warning(self, "Error", f"A profile named '{new_name}' already exists.")

    def _on_rename_profile(self) -> None:
        self._pause_for_user_action()
        current = self.config_manager.active_profile
        dialog = ProfileDialog(self, current_name=current, title="Rename Profile")
        if dialog.exec():
            new_name = dialog.get_profile_name()
            if self.config_manager.rename_profile(current, new_name):
                self._load_profiles_combo()
            else:
                QMessageBox.warning(self, "Error", f"Could not rename profile to '{new_name}'.")

    def _on_delete_profile(self) -> None:
        self._pause_for_user_action()
        current = self.config_manager.active_profile
        if len(self.config_manager.profiles) <= 1:
            QMessageBox.information(self, "Info", "Cannot delete the only remaining profile.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete profile '{current}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.config_manager.remove_profile(current)
            self._load_profiles_combo()
            self._refresh_app_list()

    def _on_open_settings(self) -> None:
        self._pause_for_user_action()
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec():
            if self.config_manager.enable_countdown and self.config_manager.countdown_seconds > 0:
                self._start_countdown()
            else:
                self._cancel_countdown()

    def _refresh_app_list(self) -> None:
        self.app_list_widget.clear()
        profile = self.config_manager.get_current_profile()

        if not profile.apps:
            self.app_list_widget.hide()
            self.empty_label.show()
        else:
            self.empty_label.hide()
            self.app_list_widget.show()

            for app in profile.apps:
                item = QListWidgetItem(self.app_list_widget)
                item_widget = AppRowWidget(app, self)
                item.setSizeHint(item_widget.sizeHint())
                self.app_list_widget.setItemWidget(item, item_widget)

    def on_app_toggled(self, app: AppEntry) -> None:
        self.config_manager.save()
        if self.timer.isActive():
            self._update_countdown_label()

    def move_app(self, app: AppEntry, direction: int) -> None:
        self._pause_for_user_action()
        profile = self.config_manager.get_current_profile()
        idx = -1
        for i, a in enumerate(profile.apps):
            if a.id == app.id:
                idx = i
                break

        if idx == -1:
            return

        new_idx = idx + direction
        if 0 <= new_idx < len(profile.apps):
            profile.apps[idx], profile.apps[new_idx] = profile.apps[new_idx], profile.apps[idx]
            self.config_manager.save()
            self._refresh_app_list()

    def _on_add_app(self) -> None:
        self._pause_for_user_action()
        dialog = AppDialog(self)
        if dialog.exec():
            new_app = dialog.get_result()
            if new_app:
                profile_name = self.config_manager.active_profile
                self.config_manager.add_app_to_profile(profile_name, new_app)
                self._refresh_app_list()
                if self.timer.isActive():
                    self._update_countdown_label()

    def edit_app(self, app: AppEntry) -> None:
        self._pause_for_user_action()
        dialog = AppDialog(self, app_entry=app)
        if dialog.exec():
            updated_app = dialog.get_result()
            if updated_app:
                profile_name = self.config_manager.active_profile
                self.config_manager.update_app_in_profile(profile_name, updated_app)
                self._refresh_app_list()

    def delete_app(self, app: AppEntry) -> None:
        self._pause_for_user_action()
        reply = QMessageBox.question(
            self,
            "Confirm Remove",
            f"Remove '{app.name}' from profile '{self.config_manager.active_profile}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            profile_name = self.config_manager.active_profile
            self.config_manager.remove_app_from_profile(profile_name, app.id)
            self._refresh_app_list()
            if self.timer.isActive():
                self._update_countdown_label()

    def launch_selected_apps(self) -> None:
        """Launches all enabled applications in the active profile and exits cleanly."""
        self.timer.stop()
        profile = self.config_manager.get_current_profile()
        enabled_apps = [a for a in profile.apps if a.enabled]

        if enabled_apps:
            AppLauncher.launch_many(enabled_apps)

        # Close the window and cleanly quit AutoLaunch
        self.close()
        QApplication.quit()
