"""Dialog for adding or editing an application entry in AutoLaunch.

Allows picking from discovered .desktop files (with live search filter and icon previews)
or defining custom shell commands.
"""

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QWidget, QListWidget, QListWidgetItem,
    QSpinBox, QCheckBox, QFileDialog, QFormLayout, QMessageBox, QGroupBox
)
from PyQt6.QtGui import QIcon

from config import AppEntry
from desktop_scanner import DesktopAppInfo, DesktopScanner
from ui.frameless import FramelessDialogBase
from ui.icon_utils import resolve_icon


class AppDialog(FramelessDialogBase):
    """Dialog to create or edit an AppEntry."""

    def __init__(self, parent: Optional[QWidget] = None, app_entry: Optional[AppEntry] = None):
        title = "Edit Application" if app_entry else "Add Application"
        super().__init__(parent, title=title)
        self.existing_entry = app_entry
        self.selected_scanner_app: Optional[DesktopAppInfo] = None
        self.scanned_apps: List[DesktopAppInfo] = []

        self.setMinimumSize(660, 540)

        self._init_ui()
        self._load_scanned_apps()

        if self.existing_entry:
            self._populate_existing()

    def _init_ui(self) -> None:
        main_layout = self.content_layout
        main_layout.setSpacing(12)

        self.tab_widget = QTabWidget()

        # Tab 1: Installed Applications
        self.installed_tab = QWidget()
        installed_layout = QVBoxLayout(self.installed_tab)
        installed_layout.setSpacing(8)

        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by name or command...")
        self.search_input.textChanged.connect(self._filter_installed_apps)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        installed_layout.addLayout(search_layout)

        self.app_list_widget = QListWidget()
        self.app_list_widget.setIconSize(QSize(32, 32))
        self.app_list_widget.itemSelectionChanged.connect(self._on_installed_app_selected)
        installed_layout.addWidget(self.app_list_widget)

        # Details box for selected installed app
        installed_details_group = QGroupBox("Selected Application Details")
        inst_form = QFormLayout(installed_details_group)

        self.inst_name_input = QLineEdit()
        self.inst_cmd_input = QLineEdit()
        self.inst_delay_spin = QSpinBox()
        self.inst_delay_spin.setRange(0, 300)
        self.inst_delay_spin.setSuffix(" seconds")
        self.inst_enabled_check = QCheckBox("Enabled for launch")
        self.inst_enabled_check.setChecked(True)

        inst_form.addRow("Display Name:", self.inst_name_input)
        inst_form.addRow("Command / Exec:", self.inst_cmd_input)
        inst_form.addRow("Startup Delay:", self.inst_delay_spin)
        inst_form.addRow("", self.inst_enabled_check)

        installed_layout.addWidget(installed_details_group)
        self.tab_widget.addTab(self.installed_tab, "Installed Applications")

        # Tab 2: Custom Command
        self.custom_tab = QWidget()
        custom_layout = QVBoxLayout(self.custom_tab)
        custom_form = QFormLayout()

        self.custom_name_input = QLineEdit()
        self.custom_name_input.setPlaceholderText("e.g. My Script or WebApp")

        self.custom_cmd_input = QLineEdit()
        self.custom_cmd_input.setPlaceholderText("e.g. /usr/bin/python3 ~/myscript.py")

        icon_row = QHBoxLayout()
        self.custom_icon_input = QLineEdit()
        self.custom_icon_input.setPlaceholderText("Theme icon name (e.g. utilities-terminal) or image path")
        browse_icon_btn = QPushButton("Browse...")
        browse_icon_btn.clicked.connect(self._browse_custom_icon)
        icon_row.addWidget(self.custom_icon_input)
        icon_row.addWidget(browse_icon_btn)

        self.custom_delay_spin = QSpinBox()
        self.custom_delay_spin.setRange(0, 300)
        self.custom_delay_spin.setSuffix(" seconds")

        self.custom_enabled_check = QCheckBox("Enabled for launch")
        self.custom_enabled_check.setChecked(True)

        custom_form.addRow("Application Name:", self.custom_name_input)
        custom_form.addRow("Command Line:", self.custom_cmd_input)
        custom_form.addRow("Icon:", icon_row)
        custom_form.addRow("Startup Delay:", self.custom_delay_spin)
        custom_form.addRow("", self.custom_enabled_check)

        custom_layout.addLayout(custom_form)
        custom_layout.addStretch()
        self.tab_widget.addTab(self.custom_tab, "Custom Command")

        main_layout.addWidget(self.tab_widget)

        # Dialog Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Application")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setStyleSheet("""
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
        btn_layout.addWidget(self.save_btn)
        main_layout.addLayout(btn_layout)

    def _load_scanned_apps(self) -> None:
        self.scanned_apps = DesktopScanner.scan_all()
        self._populate_list(self.scanned_apps)

    def _populate_list(self, apps: List[DesktopAppInfo]) -> None:
        self.app_list_widget.clear()
        for app in apps:
            item = QListWidgetItem()
            icon = resolve_icon(app.icon_name, app.icon_path)
            item.setIcon(icon)
            desc = f" ({app.generic_name})" if app.generic_name else ""
            item.setText(f"{app.name}{desc}")
            item.setData(Qt.ItemDataRole.UserRole, app)
            self.app_list_widget.addItem(item)

    def _filter_installed_apps(self, query: str) -> None:
        q = query.strip().lower()
        if not q:
            self._populate_list(self.scanned_apps)
            return

        filtered = [a for a in self.scanned_apps if q in a.search_text()]
        self._populate_list(filtered)

    def _on_installed_app_selected(self) -> None:
        selected_items = self.app_list_widget.selectedItems()
        if not selected_items:
            return

        app_info: DesktopAppInfo = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.selected_scanner_app = app_info
        self.inst_name_input.setText(app_info.name)
        self.inst_cmd_input.setText(app_info.clean_command)

    def _browse_custom_icon(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon File",
            str(Path.home()),
            "Images (*.png *.svg *.xpm *.jpg *.jpeg);;All Files (*)"
        )
        if file_path:
            self.custom_icon_input.setText(file_path)

    def _populate_existing(self) -> None:
        entry = self.existing_entry
        if not entry:
            return

        # If desktop file exists, switch to installed tab and select or populate
        if entry.desktop_file:
            self.tab_widget.setCurrentIndex(0)
            self.inst_name_input.setText(entry.name)
            self.inst_cmd_input.setText(entry.command)
            self.inst_delay_spin.setValue(entry.delay_seconds)
            self.inst_enabled_check.setChecked(entry.enabled)
            # Find and select in list if present
            for i in range(self.app_list_widget.count()):
                item = self.app_list_widget.item(i)
                info: DesktopAppInfo = item.data(Qt.ItemDataRole.UserRole)
                if info.desktop_file == entry.desktop_file or info.desktop_id == entry.desktop_file:
                    self.app_list_widget.setCurrentItem(item)
                    self.selected_scanner_app = info
                    break
        else:
            self.tab_widget.setCurrentIndex(1)
            self.custom_name_input.setText(entry.name)
            self.custom_cmd_input.setText(entry.command)
            self.custom_icon_input.setText(entry.icon)
            self.custom_delay_spin.setValue(entry.delay_seconds)
            self.custom_enabled_check.setChecked(entry.enabled)

    def _on_save(self) -> None:
        current_tab = self.tab_widget.currentIndex()

        if current_tab == 0:
            # Installed App Tab
            name = self.inst_name_input.text().strip()
            cmd = self.inst_cmd_input.text().strip()
            delay = self.inst_delay_spin.value()
            enabled = self.inst_enabled_check.isChecked()

            if not name:
                QMessageBox.warning(self, "Validation Error", "Application name cannot be empty.")
                return

            if self.selected_scanner_app:
                desktop_file = self.selected_scanner_app.desktop_file
                icon = self.selected_scanner_app.icon_name or self.selected_scanner_app.icon_path or ""
                if not cmd:
                    cmd = self.selected_scanner_app.clean_command
            elif self.existing_entry:
                desktop_file = self.existing_entry.desktop_file
                icon = self.existing_entry.icon
            else:
                desktop_file = ""
                icon = ""

            if not cmd and not desktop_file:
                QMessageBox.warning(self, "Validation Error", "Please select an application or enter a command.")
                return

            entry_id = self.existing_entry.id if self.existing_entry else ""
            self.result_entry = AppEntry(
                id=entry_id or (Path(desktop_file).name if desktop_file else ""),
                name=name,
                command=cmd,
                desktop_file=desktop_file,
                icon=icon,
                enabled=enabled,
                delay_seconds=delay,
            )
            self.accept()

        else:
            # Custom Command Tab
            name = self.custom_name_input.text().strip()
            cmd = self.custom_cmd_input.text().strip()
            icon = self.custom_icon_input.text().strip()
            delay = self.custom_delay_spin.value()
            enabled = self.custom_enabled_check.isChecked()

            if not name:
                QMessageBox.warning(self, "Validation Error", "Application name cannot be empty.")
                return

            if not cmd:
                QMessageBox.warning(self, "Validation Error", "Command line cannot be empty.")
                return

            entry_id = self.existing_entry.id if self.existing_entry else ""
            self.result_entry = AppEntry(
                id=entry_id or "",
                name=name,
                command=cmd,
                desktop_file="",
                icon=icon,
                enabled=enabled,
                delay_seconds=delay,
            )
            self.accept()

    def get_result(self) -> Optional[AppEntry]:
        return getattr(self, "result_entry", None)
