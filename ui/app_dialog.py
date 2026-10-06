"""Dialog for adding or editing an application entry in AutoLaunch.

Provides a modern, high-efficiency two-pane picker:
- Left pane: Instant live search, category chips, and application card list.
- Right pane: Application inspector and settings (preview icon, startup delay steppers,
  start minimized toggle, and optional command override).
- Supports batch "Add to Profile" without closing the dialog, or "Add & Close".
- Clean dedicated edit mode when modifying an existing application.
"""

from pathlib import Path
from typing import Callable, List, Optional

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QButtonGroup, QCheckBox, QFileDialog, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QVBoxLayout, QWidget
)

from config import AppEntry
from desktop_scanner import DesktopAppInfo, DesktopScanner
from ui.frameless import FramelessDialogBase
from ui.icon_utils import resolve_icon
from ui.widgets import FlowLayout, StepperSpinBox


class AppDialog(FramelessDialogBase):
    """Modern two-pane application addition and editing dialog."""

    app_added = pyqtSignal(AppEntry)

    CATEGORIES = [
        ("All", None),
        ("Internet", ["Network", "WebBrowser", "Email", "Chat", "Feed"]),
        ("Development", ["Development", "IDE", "Building", "Debugger"]),
        ("Utilities", ["Utility", "System", "Settings", "FileManager", "FileTools", "Archiving", "Compression"]),
        ("Media", ["AudioVideo", "Audio", "Video", "Player", "Recorder", "Graphics"]),
        ("Games", ["Game", "Emulator"]),
        ("Custom Command", "CUSTOM"),
    ]

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        app_entry: Optional[AppEntry] = None,
        on_app_added: Optional[Callable[[AppEntry], None]] = None
    ):
        self.is_edit_mode = app_entry is not None
        title = "Edit Application" if self.is_edit_mode else "Add Application"
        super().__init__(parent, title=title)
        self.existing_entry = app_entry
        self.on_app_added_callback = on_app_added
        self.result_entry: Optional[AppEntry] = None

        self.selected_scanner_app: Optional[DesktopAppInfo] = None
        self.scanned_apps: List[DesktopAppInfo] = []
        self.current_category_filter: Optional[List[str]] = None
        self.is_custom_mode: bool = False
        self.added_count: int = 0

        self.setMinimumSize(640, 480)
        self.resize(760, 520)

        self._init_ui()
        self._load_scanned_apps()

        if self.is_edit_mode and self.existing_entry:
            self._populate_edit_mode()
        else:
            # Select first application by default
            if self.app_list_widget.count() > 0:
                self.app_list_widget.setCurrentRow(0)

    def _init_ui(self) -> None:
        main_layout = self.content_layout
        main_layout.setSpacing(12)

        content_container = QHBoxLayout()
        content_container.setSpacing(14)

        # ----------------- LEFT PANE: Search, Categories, App List -----------------
        left_pane = QVBoxLayout()
        left_pane.setSpacing(8)

        # Search box with clear button
        search_box = QHBoxLayout()
        search_box.setSpacing(6)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search applications by name, generic name, or command...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.setFixedHeight(34)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #111827;
                color: #f8fafc;
                border: 1px solid #28354f;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #38bdf8;
                background-color: #141d30;
            }
        """)
        search_box.addWidget(self.search_input)
        left_pane.addLayout(search_box)

        # Category Chips (FlowLayout wrapped so all categories are immediately visible)
        category_container = QWidget()
        category_layout = FlowLayout(category_container, margin=0, spacing=6)

        self.category_group = QButtonGroup(self)
        self.category_group.setExclusive(True)

        chip_style = """
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 13px;
                padding: 4px 11px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
            QPushButton:checked {
                background-color: rgba(56, 189, 248, 0.2);
                border-color: #38bdf8;
                color: #38bdf8;
                font-weight: bold;
            }
        """

        for idx, (label, filter_val) in enumerate(self.CATEGORIES):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(chip_style)
            if idx == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, val=filter_val: self._on_category_clicked(val))
            self.category_group.addButton(btn, idx)
            category_layout.addWidget(btn)

        left_pane.addWidget(category_container)

        # Application List
        self.app_list_widget = QListWidget()
        self.app_list_widget.setIconSize(QSize(28, 28))
        self.app_list_widget.setSpacing(1)
        self.app_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.app_list_widget.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.app_list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #1e293b;
                border-radius: 8px;
                background-color: #0d1322;
                padding: 2px;
                outline: none;
            }
            QListWidget::item {
                border: 1px solid transparent;
                border-radius: 5px;
                padding: 3px 8px;
                margin: 0px;
                color: #e2e8f0;
                background: transparent;
                height: 32px;
            }
            QListWidget::item:hover {
                background-color: #17233c;
                border-color: #28354f;
            }
            QListWidget::item:selected {
                background-color: #1e3a8a;
                border-color: #3b82f6;
                color: #ffffff;
            }
        """)
        self.app_list_widget.itemSelectionChanged.connect(self._on_app_selected)
        self.app_list_widget.itemDoubleClicked.connect(self._on_app_double_clicked)
        left_pane.addWidget(self.app_list_widget, stretch=1)

        # Summary label
        self.list_summary_label = QLabel("Loading applications...")
        self.list_summary_label.setStyleSheet("color: #64748b; font-size: 11px;")
        left_pane.addWidget(self.list_summary_label)

        content_container.addLayout(left_pane, stretch=5)

        # ----------------- RIGHT PANE: Inspector & Configuration -----------------
        right_frame = QFrame()
        right_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1f2b42;
                border-radius: 10px;
            }
        """)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(16, 14, 16, 14)
        right_layout.setSpacing(12)

        # Large Header Card Preview
        header_card = QHBoxLayout()
        header_card.setSpacing(12)

        self.preview_icon_label = QLabel()
        self.preview_icon_label.setFixedSize(52, 52)
        self.preview_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_icon_label.setStyleSheet("""
            QLabel {
                background-color: #0b0f19;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
        """)
        header_card.addWidget(self.preview_icon_label)

        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)
        self.preview_title_label = QLabel("Select an Application")
        self.preview_title_label.setFont(QFont("Inter, Segoe UI, sans-serif", 12, QFont.Weight.Bold))
        self.preview_title_label.setStyleSheet("color: #f8fafc; border: none; background: transparent;")
        header_text_layout.addWidget(self.preview_title_label)

        self.preview_desc_label = QLabel("Pick from installed applications or create a custom command.")
        self.preview_desc_label.setStyleSheet("color: #64748b; font-size: 11px; border: none; background: transparent;")
        self.preview_desc_label.setWordWrap(True)
        header_text_layout.addWidget(self.preview_desc_label)

        header_card.addLayout(header_text_layout, stretch=1)
        right_layout.addLayout(header_card)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #1e293b; max-height: 1px; border: none;")
        right_layout.addWidget(divider)

        # Settings Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Display name")
        form_layout.addRow("Display Name:", self.name_input)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Command to execute")
        form_layout.addRow("Command / Exec:", self.cmd_input)

        # Custom Icon Row (visible for custom commands)
        self.icon_row_widget = QWidget()
        icon_row_layout = QHBoxLayout(self.icon_row_widget)
        icon_row_layout.setContentsMargins(0, 0, 0, 0)
        icon_row_layout.setSpacing(6)
        self.custom_icon_input = QLineEdit()
        self.custom_icon_input.setPlaceholderText("Icon name or image path")
        self.custom_icon_input.textChanged.connect(self._on_custom_icon_text_changed)
        browse_icon_btn = QPushButton("Browse...")
        browse_icon_btn.clicked.connect(self._browse_custom_icon)
        icon_row_layout.addWidget(self.custom_icon_input)
        icon_row_layout.addWidget(browse_icon_btn)
        form_layout.addRow("Icon:", self.icon_row_widget)
        self.icon_row_widget.hide()

        self.delay_spin = StepperSpinBox(minimum=0, maximum=300, value=0, suffix=" seconds", step=1)
        form_layout.addRow("Startup Delay:", self.delay_spin)

        self.minimized_check = QCheckBox("Start minimized to taskbar")
        self.minimized_check.setChecked(False)
        form_layout.addRow("", self.minimized_check)

        self.enabled_check = QCheckBox("Enabled for launch")
        self.enabled_check.setChecked(True)
        form_layout.addRow("", self.enabled_check)

        right_layout.addLayout(form_layout)
        right_layout.addStretch()

        # Added toast/badge feedback label
        self.feedback_label = QLabel()
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_label.setStyleSheet("color: #34d399; font-size: 11px; font-weight: bold; border: none;")
        self.feedback_label.hide()
        right_layout.addWidget(self.feedback_label)

        content_container.addWidget(right_frame, stretch=4)
        main_layout.addLayout(content_container, stretch=1)

        # ----------------- BOTTOM DIALOG ACTIONS -----------------
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        if not self.is_edit_mode:
            # Multi-add batch button
            self.add_another_btn = QPushButton("+ Add to Profile")
            self.add_another_btn.setFixedHeight(34)
            self.add_another_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    color: #38bdf8;
                    border: 1px solid rgba(56, 189, 248, 0.4);
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 0 16px;
                }
                QPushButton:hover {
                    background-color: rgba(56, 189, 248, 0.15);
                    border-color: #38bdf8;
                    color: #ffffff;
                }
            """)
            self.add_another_btn.setToolTip("Adds this application to your profile without closing this picker")
            self.add_another_btn.clicked.connect(self._on_add_to_profile_only)
            btn_layout.addWidget(self.add_another_btn)

        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Done" if not self.is_edit_mode else "Cancel")
        self.cancel_btn.setFixedHeight(34)
        self.cancel_btn.clicked.connect(self._on_close_clicked)
        btn_layout.addWidget(self.cancel_btn)

        save_btn_text = "Save Changes" if self.is_edit_mode else "Add and Close"
        self.save_btn = QPushButton(save_btn_text)
        self.save_btn.setFixedHeight(34)
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._on_save_and_close)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
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

        # Add top item: Custom Command / Script
        custom_item = QListWidgetItem()
        custom_item.setIcon(resolve_icon("utilities-terminal", ""))
        custom_item.setText("+ Custom Command / Shell Script")
        custom_item.setData(Qt.ItemDataRole.UserRole, "CUSTOM")
        self.app_list_widget.addItem(custom_item)

        for app in apps:
            item = QListWidgetItem()
            icon = resolve_icon(app.icon_name, app.icon_path)
            item.setIcon(icon)
            
            # Clean display label: keep item text focused on application name, full details in tooltip
            display_name = app.name.strip()
            if app.generic_name and app.generic_name.lower() not in display_name.lower():
                display_text = f"{display_name} ({app.generic_name})"
            else:
                display_text = display_name
            
            # Truncate text cleanly if exceedingly long
            if len(display_text) > 34:
                truncated_text = display_text[:32] + "..."
            else:
                truncated_text = display_text

            item.setText(truncated_text)
            item.setToolTip(f"{app.name}\n{app.generic_name or app.comment or app.clean_command}")
            item.setData(Qt.ItemDataRole.UserRole, app)
            self.app_list_widget.addItem(item)

        count = len(apps)
        self.list_summary_label.setText(f"{count} application{'s' if count != 1 else ''} available")

    def _on_category_clicked(self, category_filter) -> None:
        if category_filter == "CUSTOM":
            self.is_custom_mode = True
            self.current_category_filter = None
            self._filter_list()
            # Select the custom item directly
            self.app_list_widget.setCurrentRow(0)
            return

        self.is_custom_mode = False
        self.current_category_filter = category_filter
        self._filter_list()

    def _on_search_text_changed(self, query: str) -> None:
        self._filter_list()

    def _filter_list(self) -> None:
        q = self.search_input.text().strip().lower()

        filtered: List[DesktopAppInfo] = []
        for app in self.scanned_apps:
            # Check search text query
            if q and q not in app.search_text():
                continue

            # Check category filter
            if self.current_category_filter:
                cats = app.categories or []
                if not any(c in self.current_category_filter for c in cats):
                    continue

            filtered.append(app)

        self._populate_list(filtered)

    def _on_app_selected(self) -> None:
        selected_items = self.app_list_widget.selectedItems()
        if not selected_items:
            return

        data = selected_items[0].data(Qt.ItemDataRole.UserRole)

        if data == "CUSTOM":
            self._set_custom_mode()
            return

        app_info: DesktopAppInfo = data
        self.is_custom_mode = False
        self.selected_scanner_app = app_info
        self.icon_row_widget.hide()

        # Update preview card
        icon = resolve_icon(app_info.icon_name, app_info.icon_path)
        pix = icon.pixmap(48, 48)
        self.preview_icon_label.setPixmap(pix)
        self.preview_title_label.setText(app_info.name)
        desc = app_info.generic_name or app_info.comment or Path(app_info.desktop_file).name
        self.preview_desc_label.setText(desc)

        # Update form inputs
        self.name_input.setText(app_info.name)
        self.cmd_input.setText(app_info.clean_command)

    def _set_custom_mode(self) -> None:
        self.is_custom_mode = True
        self.selected_scanner_app = None
        self.icon_row_widget.show()

        icon = resolve_icon("utilities-terminal", "")
        pix = icon.pixmap(48, 48)
        self.preview_icon_label.setPixmap(pix)
        self.preview_title_label.setText("Custom Command")
        self.preview_desc_label.setText("Run any system executable, Python script, or terminal tool.")

        if not self.is_edit_mode:
            self.name_input.clear()
            self.cmd_input.clear()
            self.custom_icon_input.clear()

    def _browse_custom_icon(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon File",
            str(Path.home()),
            "Images (*.png *.svg *.xpm *.jpg *.jpeg);;All Files (*)"
        )
        if file_path:
            self.custom_icon_input.setText(file_path)

    def _on_custom_icon_text_changed(self, text: str) -> None:
        if self.is_custom_mode:
            icon = resolve_icon(text.strip(), text.strip())
            pix = icon.pixmap(48, 48)
            self.preview_icon_label.setPixmap(pix)

    def _populate_edit_mode(self) -> None:
        entry = self.existing_entry
        if not entry:
            return

        self.name_input.setText(entry.name)
        self.cmd_input.setText(entry.command)
        self.delay_spin.setValue(entry.delay_seconds)
        self.minimized_check.setChecked(entry.start_minimized)
        self.enabled_check.setChecked(entry.enabled)

        if entry.desktop_file:
            self.is_custom_mode = False
            self.icon_row_widget.hide()
            # Match item in list if possible
            for i in range(self.app_list_widget.count()):
                item = self.app_list_widget.item(i)
                data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(data, DesktopAppInfo):
                    if data.desktop_file == entry.desktop_file or data.desktop_id == entry.desktop_file:
                        self.app_list_widget.setCurrentItem(item)
                        self.selected_scanner_app = data
                        break
        else:
            self._set_custom_mode()
            self.custom_icon_input.setText(entry.icon)

    def _create_app_entry_from_form(self) -> Optional[AppEntry]:
        name = self.name_input.text().strip()
        cmd = self.cmd_input.text().strip()
        delay = self.delay_spin.value()
        enabled = self.enabled_check.isChecked()
        minimized = self.minimized_check.isChecked()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Please provide a display name for the application.")
            return None

        if self.is_custom_mode:
            if not cmd:
                QMessageBox.warning(self, "Validation Error", "Please enter a valid command line.")
                return None
            icon = self.custom_icon_input.text().strip()
            desktop_file = ""
            entry_id = self.existing_entry.id if self.existing_entry else ""
        else:
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
                QMessageBox.warning(self, "Validation Error", "Please select an application or specify a command.")
                return None

            entry_id = self.existing_entry.id if self.existing_entry else (Path(desktop_file).name if desktop_file else "")

        return AppEntry(
            id=entry_id or "",
            name=name,
            command=cmd,
            desktop_file=desktop_file,
            icon=icon,
            enabled=enabled,
            delay_seconds=delay,
            start_minimized=minimized,
        )

    def _on_add_to_profile_only(self) -> None:
        """Adds current configuration to the profile, updates feedback, and remains open."""
        entry = self._create_app_entry_from_form()
        if not entry:
            return

        self.added_count += 1
        self.app_added.emit(entry)
        if self.on_app_added_callback:
            self.on_app_added_callback(entry)

        # Show brief confirmation message in dialog
        self.feedback_label.setText(f"Added '{entry.name}' to profile! ({self.added_count} added)")
        self.feedback_label.show()
        self.cancel_btn.setText("Close")

    def _on_save_and_close(self) -> None:
        """Saves current entry and closes dialog."""
        entry = self._create_app_entry_from_form()
        if not entry:
            return

        self.result_entry = entry
        self.app_added.emit(entry)
        if not self.is_edit_mode and self.on_app_added_callback:
            self.on_app_added_callback(entry)

        self.accept()

    def _on_app_double_clicked(self, item: QListWidgetItem) -> None:
        """Double clicking an application immediately adds it and closes."""
        self._on_save_and_close()

    def _on_close_clicked(self) -> None:
        if self.added_count > 0:
            self.accept()
        else:
            self.reject()

    def get_result(self) -> Optional[AppEntry]:
        return self.result_entry

