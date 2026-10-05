"""Modern, portrait desktop interface for AutoLaunch.

Features a tall, narrow aspect ratio with compact acrylic cards, animated toggle switches,
badge pills, glowing progress indicators, and streamlined vertical layout.
Complies with zero-emoji guidelines and dynamic path resolution.
"""

from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QListWidget, QListWidgetItem,
    QProgressBar, QMessageBox, QFrame, QApplication, QSizePolicy
)

from config import AppEntry, ConfigManager
from launcher import AppLauncher
from ui.app_dialog import AppDialog
from ui.frameless import DraggableHeader, WindowControls
from ui.icon_utils import resolve_icon
from ui.profile_dialog import ProfileDialog
from ui.settings_dialog import SettingsDialog
from ui.widgets import BadgePill, ToggleSwitch


class AppCardWidget(QFrame):
    """Compact elevated card representing a configured application."""

    def __init__(self, app: AppEntry, parent_window: "MainWindow"):
        super().__init__()
        self.app = app
        self.parent_window = parent_window
        self._init_ui()

    def _init_ui(self) -> None:
        self.setObjectName("AppCard")
        self.setStyleSheet("""
            QFrame#AppCard {
                background-color: #131b2e;
                border: 1px solid #1f2b42;
                border-radius: 10px;
            }
            QFrame#AppCard:hover {
                background-color: #17233c;
                border: 1px solid #38bdf8;
            }
        """)

        card_layout = QHBoxLayout(self)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(8)

        # 1. Compact Animated Toggle Switch
        self.toggle = ToggleSwitch(width=36, height=20)
        self.toggle.setChecked(self.app.enabled)
        self.toggle.toggled.connect(self._on_toggle)
        self.toggle.setToolTip("Enable or disable this application on startup")
        card_layout.addWidget(self.toggle)

        # 2. Compact Icon Box
        icon_box = QFrame()
        icon_box.setFixedSize(34, 34)
        icon_box.setStyleSheet("""
            background-color: #1a233a;
            border: 1px solid #28354f;
            border-radius: 8px;
        """)
        icon_box_layout = QVBoxLayout(icon_box)
        icon_box_layout.setContentsMargins(0, 0, 0, 0)
        icon_box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        qicon = resolve_icon(self.app.icon, self.app.desktop_file)
        icon_label.setPixmap(qicon.pixmap(QSize(24, 24)))
        icon_label.setScaledContents(True)
        icon_label.setStyleSheet("background: transparent; border: none;")
        icon_box_layout.addWidget(icon_label)

        card_layout.addWidget(icon_box)

        # 3. Compact App Details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)

        name_label = QLabel(self.app.name)
        title_font = QFont("Inter, Segoe UI, sans-serif", 10, QFont.Weight.Bold)
        name_label.setFont(title_font)
        name_label.setStyleSheet("color: #f8fafc; background: transparent; border: none;")
        title_row.addWidget(name_label)

        # Small delay badge if configured
        if self.app.delay_seconds > 0:
            delay_badge = BadgePill(
                f"+{self.app.delay_seconds}s",
                bg_color="rgba(16, 185, 129, 0.15)",
                text_color="#34d399",
                border_color="rgba(16, 185, 129, 0.35)"
            )
            title_row.addWidget(delay_badge)

        title_row.addStretch()
        details_layout.addLayout(title_row)

        subtitle_text = self.app.desktop_file or self.app.command
        # Truncate subtitle for compact look
        if len(subtitle_text) > 42:
            subtitle_display = subtitle_text[:40] + "..."
        else:
            subtitle_display = subtitle_text

        subtitle_label = QLabel(subtitle_display)
        subtitle_label.setToolTip(subtitle_text)
        subtitle_label.setStyleSheet("color: #64748b; font-size: 10px; background: transparent; border: none;")
        details_layout.addWidget(subtitle_label)

        card_layout.addLayout(details_layout, stretch=1)

        # 4. Compact Micro-Action Buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(4)

        micro_btn_style = """
            QPushButton {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 4px;
                font-size: 10px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
                border-color: #38bdf8;
            }
        """

        self.up_btn = QPushButton("▲")
        self.up_btn.setFixedSize(22, 22)
        self.up_btn.setStyleSheet(micro_btn_style)
        self.up_btn.setToolTip("Move up")
        self.up_btn.clicked.connect(self._on_move_up)
        action_layout.addWidget(self.up_btn)

        self.down_btn = QPushButton("▼")
        self.down_btn.setFixedSize(22, 22)
        self.down_btn.setStyleSheet(micro_btn_style)
        self.down_btn.setToolTip("Move down")
        self.down_btn.clicked.connect(self._on_move_down)
        action_layout.addWidget(self.down_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setFixedSize(32, 22)
        self.edit_btn.setStyleSheet(micro_btn_style)
        self.edit_btn.setToolTip("Edit application details")
        self.edit_btn.clicked.connect(self._on_edit)
        action_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("x")
        self.delete_btn.setFixedSize(22, 22)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.12);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.25);
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
                border-color: #ef4444;
            }
        """)
        self.delete_btn.setToolTip("Remove application")
        self.delete_btn.clicked.connect(self._on_delete)
        action_layout.addWidget(self.delete_btn)

        card_layout.addLayout(action_layout)

    def _on_toggle(self, checked: bool) -> None:
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
    """Main window for AutoLaunch with portrait, narrow orientation."""

    def __init__(self, config_manager: ConfigManager, autostart_mode: bool = False):
        super().__init__()
        self.config_manager = config_manager
        self.autostart_mode = autostart_mode

        self.remaining_seconds = self.config_manager.countdown_seconds
        self.is_paused = False

        self.setWindowTitle("AutoLaunch")
        # Portrait orientation: taller and narrower
        self.setMinimumSize(420, 680)
        self.resize(460, 760)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)

        # Countdown timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer_tick)

        self._init_ui()
        self._load_profiles_combo()
        self._refresh_app_list()

        if self.config_manager.enable_countdown and self.config_manager.countdown_seconds > 0:
            self._start_countdown()
        else:
            self.countdown_card.hide()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        central_widget.setStyleSheet("""
            QWidget#CentralWidget {
                background-color: #0b0f19;
            }
        """)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 12, 14, 14)
        main_layout.setSpacing(10)

        # Top Header Bar (Draggable, 2 compact rows)
        header_frame = DraggableHeader()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 4px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 8, 10, 8)
        header_layout.setSpacing(8)

        # Row 1: Brand & Window Controls
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)

        title_lbl = QLabel("AutoLaunch")
        title_font = QFont("Inter, Segoe UI, sans-serif", 13, QFont.Weight.Bold)
        title_lbl.setFont(title_font)
        title_lbl.setStyleSheet("color: #f8fafc; border: none; background: transparent;")

        sub_lbl = QLabel("Startup Application Orchestrator")
        sub_lbl.setStyleSheet("color: #64748b; font-size: 10px; border: none; background: transparent;")

        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        row1.addLayout(title_box)

        row1.addStretch()

        self.window_controls = WindowControls(self, show_minimize=True)
        row1.addWidget(self.window_controls)
        header_layout.addLayout(row1)

        # Row 2: Profile Selector & Quick Actions
        row2 = QHBoxLayout()
        row2.setSpacing(5)

        prof_lbl = QLabel("Profile:")
        prof_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        row2.addWidget(prof_lbl)

        self.profile_combo = QComboBox()
        self.profile_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.profile_combo.currentTextChanged.connect(self._on_profile_changed)
        row2.addWidget(self.profile_combo)

        btn_header_style = """
            QPushButton {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 5px;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #38bdf8;
                color: #ffffff;
            }
        """

        self.new_profile_btn = QPushButton("+")
        self.new_profile_btn.setFixedSize(26, 26)
        self.new_profile_btn.setStyleSheet(btn_header_style)
        self.new_profile_btn.setToolTip("Create a new profile")
        self.new_profile_btn.clicked.connect(self._on_new_profile)
        row2.addWidget(self.new_profile_btn)

        self.rename_profile_btn = QPushButton("Ren")
        self.rename_profile_btn.setFixedSize(34, 26)
        self.rename_profile_btn.setStyleSheet(btn_header_style)
        self.rename_profile_btn.setToolTip("Rename active profile")
        self.rename_profile_btn.clicked.connect(self._on_rename_profile)
        row2.addWidget(self.rename_profile_btn)

        self.delete_profile_btn = QPushButton("Del")
        self.delete_profile_btn.setFixedSize(34, 26)
        self.delete_profile_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 5px;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 6px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.15);
                border-color: #ef4444;
            }
        """)
        self.delete_profile_btn.setToolTip("Delete active profile")
        self.delete_profile_btn.clicked.connect(self._on_delete_profile)
        row2.addWidget(self.delete_profile_btn)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setStyleSheet(btn_header_style)
        self.settings_btn.setFixedHeight(26)
        self.settings_btn.clicked.connect(self._on_open_settings)
        row2.addWidget(self.settings_btn)

        header_layout.addLayout(row2)
        main_layout.addWidget(header_frame)

        # Center: Application Cards List (Compact)
        self.app_list_widget = QListWidget()
        self.app_list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.app_list_widget.setSpacing(4)
        self.app_list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #1e293b;
                border-radius: 10px;
                background-color: #0b1120;
                padding: 4px;
            }
            QListWidget::item {
                border: none;
                background: transparent;
                padding: 0px;
            }
        """)
        main_layout.addWidget(self.app_list_widget, stretch=1)

        # Empty State Card
        self.empty_card = QFrame()
        self.empty_card.setStyleSheet("""
            QFrame {
                border: 1px solid #1e293b;
                border-radius: 10px;
                background-color: #0f172a;
                padding: 24px;
            }
        """)
        empty_layout = QVBoxLayout(self.empty_card)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(10)

        empty_title = QLabel("No applications configured")
        empty_title.setFont(QFont("Inter, Segoe UI, sans-serif", 12, QFont.Weight.Bold))
        empty_title.setStyleSheet("color: #94a3b8; border: none; background: transparent;")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty_desc = QLabel(
            "Add your startup applications, Zen Browser profiles, or custom scripts."
        )
        empty_desc.setWordWrap(True)
        empty_desc.setStyleSheet("color: #64748b; font-size: 11px; border: none; background: transparent;")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        add_first_btn = QPushButton("+ Add First Application")
        add_first_btn.setFixedSize(180, 34)
        add_first_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #3b82f6);
            }
        """)
        add_first_btn.clicked.connect(self._on_add_app)

        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_desc)
        empty_layout.addWidget(add_first_btn)

        main_layout.addWidget(self.empty_card)

        # Countdown Progress Card (Compact)
        self.countdown_card = QFrame()
        self.countdown_card.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
        """)
        countdown_layout = QVBoxLayout(self.countdown_card)
        countdown_layout.setContentsMargins(12, 8, 12, 8)
        countdown_layout.setSpacing(6)

        countdown_header = QHBoxLayout()
        self.countdown_status_label = QLabel("Auto-launching in 5s...")
        self.countdown_status_label.setFont(QFont("Inter, Segoe UI, sans-serif", 10, QFont.Weight.Medium))
        self.countdown_status_label.setStyleSheet("color: #38bdf8; border: none; background: transparent;")
        countdown_header.addWidget(self.countdown_status_label)

        countdown_header.addStretch()

        self.pause_resume_btn = QPushButton("Pause")
        self.pause_resume_btn.setFixedSize(60, 24)
        self.pause_resume_btn.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        self.pause_resume_btn.clicked.connect(self._toggle_pause_countdown)
        countdown_header.addWidget(self.pause_resume_btn)

        self.cancel_countdown_btn = QPushButton("Cancel")
        self.cancel_countdown_btn.setFixedSize(60, 24)
        self.cancel_countdown_btn.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        self.cancel_countdown_btn.clicked.connect(self._cancel_countdown)
        countdown_header.addWidget(self.cancel_countdown_btn)

        countdown_layout.addLayout(countdown_header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, max(1, self.config_manager.countdown_seconds))
        self.progress_bar.setValue(self.config_manager.countdown_seconds)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #0f172a;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #3b82f6);
                border-radius: 3px;
            }
        """)
        countdown_layout.addWidget(self.progress_bar)

        main_layout.addWidget(self.countdown_card)

        # Bottom Action Bar (Streamlined for portrait layout)
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(8)

        row_buttons = QHBoxLayout()
        row_buttons.setSpacing(8)

        self.add_app_btn = QPushButton("+ Add Application")
        self.add_app_btn.setFixedHeight(34)
        self.add_app_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 6px;
                font-weight: bold;
                padding: 0 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(56, 189, 248, 0.15);
                border-color: #38bdf8;
                color: #ffffff;
            }
        """)
        self.add_app_btn.clicked.connect(self._on_add_app)
        row_buttons.addWidget(self.add_app_btn, stretch=1)

        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedSize(70, 34)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
        """)
        self.close_btn.setToolTip("Close AutoLaunch without launching applications")
        self.close_btn.clicked.connect(self.close)
        row_buttons.addWidget(self.close_btn)

        bottom_layout.addLayout(row_buttons)

        # Full-width prominent launch button
        self.launch_now_btn = QPushButton("Launch Selected Now")
        self.launch_now_btn.setFixedHeight(38)
        self.launch_now_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 #10b981);
            }
            QPushButton:pressed {
                background: #047857;
            }
        """)
        self.launch_now_btn.clicked.connect(self.launch_selected_apps)
        bottom_layout.addWidget(self.launch_now_btn)

        main_layout.addLayout(bottom_layout)

    def _start_countdown(self) -> None:
        self.remaining_seconds = self.config_manager.countdown_seconds
        self.is_paused = False
        self.progress_bar.setRange(0, max(1, self.config_manager.countdown_seconds))
        self.progress_bar.setValue(self.remaining_seconds)
        self.pause_resume_btn.setText("Pause")
        self._update_countdown_label()
        self.countdown_card.show()
        self.timer.start(1000)

    def _update_countdown_label(self) -> None:
        current_profile = self.config_manager.get_current_profile()
        enabled_count = sum(1 for a in current_profile.apps if a.enabled)
        sec_str = "s" if self.remaining_seconds != 1 else "s"
        self.countdown_status_label.setText(
            f"Auto-launching in {self.remaining_seconds}{sec_str} ({enabled_count} apps enabled)"
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
            self.countdown_status_label.setText(f"Paused at {self.remaining_seconds}s")
        else:
            self.pause_resume_btn.setText("Pause")
            self._update_countdown_label()

    def _cancel_countdown(self) -> None:
        self.timer.stop()
        self.countdown_card.hide()

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
            self.empty_card.show()
        else:
            self.empty_card.hide()
            self.app_list_widget.show()

            for app in profile.apps:
                item = QListWidgetItem(self.app_list_widget)
                card_widget = AppCardWidget(app, self)
                item.setSizeHint(card_widget.sizeHint())
                self.app_list_widget.setItemWidget(item, card_widget)

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

        self.close()
        QApplication.quit()
