"""Dialog for adding or editing an application entry in AutoLaunch.

Provides a modern, high-efficiency two-pane picker:
- Left pane: Instant live search, category chips, and application card list.
- Right pane: Application inspector and settings (preview icon, startup delay steppers,
  start minimized toggle, and optional command override).
- Supports batch "Add to Profile" without closing the dialog, or "Add & Close".
- Clean dedicated edit mode when modifying an existing application.
"""

import html
import uuid
from pathlib import Path
from typing import Callable, List, Optional

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QCheckBox, QFileDialog, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)

from config import AppEntry
from desktop_scanner import DesktopAppInfo, DesktopScanner
from ui.frameless import FramelessDialogBase
from ui.icon_utils import resolve_icon
from ui.widgets import FlowLayout, StepperSpinBox


class TwoColumnAppTableWidget(QTableWidget):
    """Rigid two-column grid table for application picker with automatic text elision."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setDefaultSectionSize(36)
        self.setShowGrid(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.setIconSize(QSize(26, 26))
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #2f2f37;
                border-radius: 8px;
                background-color: #18181b;
                padding: 3px;
                outline: none;
            }
            QTableWidget::item {
                border: 1px solid transparent;
                border-radius: 5px;
                padding: 3px 8px;
                margin: 1px;
                color: #d4d4d8;
                background: transparent;
            }
            QTableWidget::item:hover {
                background-color: #28282e;
                border-color: #2f2f37;
                color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: rgba(226, 232, 240, 0.15);
                border-color: rgba(226, 232, 240, 0.45);
                color: #ffffff;
            }
        """)

    def count(self) -> int:
        """Returns total valid items in table."""
        total = 0
        for r in range(self.rowCount()):
            for c in range(2):
                item = self.item(r, c)
                if item is not None and item.data(Qt.ItemDataRole.UserRole) is not None:
                    total += 1
        return total


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

        self.setMinimumSize(480, 700)
        self.resize(600, 780)

        self._init_ui()
        self._load_scanned_apps()

        if self.is_edit_mode and self.existing_entry:
            self._populate_edit_mode()
        else:
            # Select first application by default
            if self.app_list_widget.count() > 0:
                self.app_list_widget.setCurrentCell(0, 0)

    def _init_ui(self) -> None:
        main_layout = self.content_layout
        main_layout.setSpacing(10)

        # ----------------- TOP AREA: Search, Categories, Full-Width App List -----------------
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
                background-color: #18181b;
                color: #ffffff;
                border: 1px solid #2f2f37;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #e2e8f0;
                background-color: #202024;
            }
        """)
        search_box.addWidget(self.search_input)
        main_layout.addLayout(search_box)

        # Category Chips (FlowLayout wrapped so all categories are immediately visible)
        category_container = QWidget()
        category_layout = FlowLayout(category_container, margin=0, spacing=6)

        self.category_group = QButtonGroup(self)
        self.category_group.setExclusive(True)

        chip_style = """
            QPushButton {
                background-color: #202024;
                color: #71717a;
                border: 1px solid #2f2f37;
                border-radius: 13px;
                padding: 4px 11px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #28282e;
                color: #ffffff;
                border-color: #475569;
            }
            QPushButton:checked {
                background-color: rgba(226, 232, 240, 0.15);
                border-color: rgba(226, 232, 240, 0.45);
                color: #ffffff;
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

        main_layout.addWidget(category_container)

        # 2-Column Application Table Widget
        self.app_list_widget = TwoColumnAppTableWidget()
        self.app_list_widget.itemSelectionChanged.connect(self._on_app_selected)
        self.app_list_widget.itemDoubleClicked.connect(self._on_app_double_clicked)
        main_layout.addWidget(self.app_list_widget, stretch=1)

        # Summary label
        self.list_summary_label = QLabel("Loading applications...")
        self.list_summary_label.setStyleSheet("color: #71717a; font-size: 11px;")
        main_layout.addWidget(self.list_summary_label)

        # ----------------- BOTTOM AREA: Inspector & Configuration -----------------
        self.inspector_frame = QFrame()
        self.inspector_frame.setStyleSheet("""
            QFrame {
                background-color: #1c1c20;
                border: 1px solid #2f2f37;
                border-radius: 10px;
            }
        """)
        inspector_layout = QVBoxLayout(self.inspector_frame)
        inspector_layout.setContentsMargins(14, 10, 14, 10)
        inspector_layout.setSpacing(8)

        # Selected App Preview Header (Horizontal)
        header_card = QHBoxLayout()
        header_card.setSpacing(10)
        header_card.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.preview_icon_label = QLabel()
        self.preview_icon_label.setFixedSize(40, 40)
        self.preview_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_icon_label.setStyleSheet("""
            QLabel {
                background-color: #121214;
                border: 1px solid #2f2f37;
                border-radius: 8px;
            }
        """)
        header_card.addWidget(self.preview_icon_label)

        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)
        self.preview_title_label = QLabel("Select an Application")
        self.preview_title_label.setFont(QFont("Inter, Segoe UI, sans-serif", 12, QFont.Weight.Bold))
        self.preview_title_label.setStyleSheet("color: #ffffff; border: none; background: transparent;")
        header_text_layout.addWidget(self.preview_title_label)

        self.preview_desc_label = QLabel("Pick from installed applications or create a custom command.")
        self.preview_desc_label.setStyleSheet("color: #71717a; font-size: 11px; border: none; background: transparent;")
        self.preview_desc_label.setWordWrap(True)
        header_text_layout.addWidget(self.preview_desc_label)

        header_card.addLayout(header_text_layout, stretch=1)

        # Inline feedback badge (e.g. "Added 'App' (1 added)")
        self.feedback_label = QLabel()
        self.feedback_label.setStyleSheet("color: #34d399; font-size: 11px; font-weight: 600; border: none; background: transparent; padding-right: 4px;")
        self.feedback_label.hide()
        header_card.addWidget(self.feedback_label)

        inspector_layout.addLayout(header_card)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #2f2f37; max-height: 1px; border: none;")
        inspector_layout.addWidget(divider)

        # Row 1: Display Name + Startup Delay (compact) + Checkboxes
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(10)
        row1_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        name_lbl = QLabel("Display Name:")
        name_lbl.setStyleSheet("color: #d4d4d8; font-size: 12px; font-weight: 500; border: none; background: transparent;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Display name")
        self.name_input.setFixedHeight(30)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #18181b;
                color: #ffffff;
                border: 1px solid #2f2f37;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #e2e8f0;
                background-color: #202024;
            }
        """)
        row1_layout.addWidget(name_lbl)
        row1_layout.addWidget(self.name_input, stretch=3)

        delay_lbl = QLabel("Delay:")
        delay_lbl.setStyleSheet("color: #d4d4d8; font-size: 12px; font-weight: 500; border: none; background: transparent;")
        self.delay_spin = StepperSpinBox(minimum=0, maximum=300, value=0, suffix="s", step=1, compact=True)
        row1_layout.addWidget(delay_lbl)
        row1_layout.addWidget(self.delay_spin)

        self.minimized_check = QCheckBox("Start min")
        self.minimized_check.setChecked(False)
        self.minimized_check.setStyleSheet("border: none; background: transparent;")
        row1_layout.addWidget(self.minimized_check)

        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(True)
        self.enabled_check.setStyleSheet("border: none; background: transparent;")
        row1_layout.addWidget(self.enabled_check)

        inspector_layout.addLayout(row1_layout)

        # Row 2: Full-Width Command / Exec
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(10)
        row2_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        cmd_lbl = QLabel("Command / Exec:")
        cmd_lbl.setStyleSheet("color: #d4d4d8; font-size: 12px; font-weight: 500; border: none; background: transparent;")
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Command to execute")
        self.cmd_input.setFixedHeight(32)
        self.cmd_input.setStyleSheet("""
            QLineEdit {
                background-color: #18181b;
                color: #ffffff;
                border: 1px solid #2f2f37;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #e2e8f0;
                background-color: #202024;
            }
        """)
        row2_layout.addWidget(cmd_lbl)
        row2_layout.addWidget(self.cmd_input, stretch=1)
        inspector_layout.addLayout(row2_layout)

        # Row 3: Custom Icon Row (visible for custom commands)
        self.icon_row_widget = QWidget()
        self.icon_row_widget.setStyleSheet("border: none; background: transparent;")
        icon_row_layout = QHBoxLayout(self.icon_row_widget)
        icon_row_layout.setContentsMargins(0, 0, 0, 0)
        icon_row_layout.setSpacing(10)
        icon_lbl = QLabel("Custom Icon:")
        icon_lbl.setStyleSheet("color: #d4d4d8; font-size: 12px; font-weight: 500; border: none; background: transparent;")
        self.custom_icon_input = QLineEdit()
        self.custom_icon_input.setPlaceholderText("Icon name or image path (.png, .svg)")
        self.custom_icon_input.setFixedHeight(30)
        self.custom_icon_input.setStyleSheet("""
            QLineEdit {
                background-color: #18181b;
                color: #ffffff;
                border: 1px solid #2f2f37;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #e2e8f0;
                background-color: #202024;
            }
        """)
        self.custom_icon_input.textChanged.connect(self._on_custom_icon_text_changed)
        browse_icon_btn = QPushButton("Browse...")
        browse_icon_btn.setFixedHeight(30)
        browse_icon_btn.setStyleSheet("""
            QPushButton {
                background-color: #202024;
                color: #d4d4d8;
                border: 1px solid #2f2f37;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #28282e;
                color: #ffffff;
                border-color: #475569;
            }
        """)
        browse_icon_btn.clicked.connect(self._browse_custom_icon)
        icon_row_layout.addWidget(icon_lbl)
        icon_row_layout.addWidget(self.custom_icon_input, stretch=1)
        icon_row_layout.addWidget(browse_icon_btn)
        inspector_layout.addWidget(self.icon_row_widget)
        self.icon_row_widget.hide()

        main_layout.addWidget(self.inspector_frame)

        # ----------------- BOTTOM DIALOG ACTIONS -----------------
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 4, 0, 0)
        btn_layout.setSpacing(10)

        if self.is_edit_mode:
            self.save_btn = QPushButton("Save Changes")
            self.save_btn.setFixedHeight(36)
            self.save_btn.setDefault(True)
            self.save_btn.clicked.connect(self._on_save_and_close)
            self.save_btn.setStyleSheet("""
                QPushButton {
                    background-color: #202024;
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 13px;
                    border: 1px solid rgba(226, 232, 240, 0.45);
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: rgba(226, 232, 240, 0.15);
                    border-color: #ffffff;
                    color: #ffffff;
                }
            """)
            btn_layout.addWidget(self.save_btn, stretch=1)

            self.cancel_btn = QPushButton("Cancel")
            self.cancel_btn.setFixedHeight(36)
            self.cancel_btn.setMinimumWidth(100)
            self.cancel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #202024;
                    color: #71717a;
                    border: 1px solid #2f2f37;
                    border-radius: 6px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #28282e;
                    color: #ffffff;
                }
            """)
            self.cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(self.cancel_btn, stretch=0)
        else:
            self.add_btn = QPushButton("+ Add Application to Profile")
            self.add_btn.setFixedHeight(36)
            self.add_btn.setDefault(True)
            self.add_btn.clicked.connect(self._on_add_clicked)
            self.add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #202024;
                    color: #e2e8f0;
                    border: 1px solid rgba(226, 232, 240, 0.45);
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 0 12px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: rgba(226, 232, 240, 0.15);
                    border-color: #ffffff;
                    color: #ffffff;
                }
            """)
            btn_layout.addWidget(self.add_btn, stretch=1)

            self.close_btn = QPushButton("Close")
            self.close_btn.setFixedHeight(36)
            self.close_btn.setMinimumWidth(100)
            self.close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #202024;
                    color: #71717a;
                    border: 1px solid #2f2f37;
                    border-radius: 6px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #28282e;
                    color: #ffffff;
                }
            """)
            self.close_btn.clicked.connect(self._on_close_clicked)
            btn_layout.addWidget(self.close_btn, stretch=0)

            # Compatibility aliases
            self.cancel_btn = self.close_btn
            self.save_btn = self.add_btn

        main_layout.addLayout(btn_layout)

    def _load_scanned_apps(self) -> None:
        self.scanned_apps = DesktopScanner.scan_all()
        self._populate_list(self.scanned_apps)

    def _populate_list(self, apps: List[DesktopAppInfo]) -> None:
        self.app_list_widget.clear()
        total_items = 1 + len(apps)
        rows = (total_items + 1) // 2
        self.app_list_widget.setRowCount(rows)

        # Add top item: Custom Command / Script at cell (0, 0)
        custom_item = QTableWidgetItem("+ Custom Command / Shell Script")
        custom_item.setIcon(resolve_icon("utilities-terminal", ""))
        custom_item.setToolTip("Create a custom command or shell script entry")
        custom_item.setData(Qt.ItemDataRole.UserRole, "CUSTOM")
        custom_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.app_list_widget.setItem(0, 0, custom_item)

        for idx, app in enumerate(apps):
            pos = idx + 1
            r = pos // 2
            c = pos % 2

            item = QTableWidgetItem(app.name.strip())
            icon = resolve_icon(app.icon_name, app.icon_path)
            item.setIcon(icon)

            escaped_name = html.escape(app.name.strip())
            tooltip_html = [
                f'<div style="font-family: sans-serif; line-height: 1.4;">',
                f'  <div style="font-size: 14px; font-weight: bold; color: #f8fafc; margin-bottom: 4px;">{escaped_name}</div>'
            ]
            if app.generic_name:
                escaped_cat = html.escape(app.generic_name.strip())
                tooltip_html.append(f'  <div style="font-size: 13px; color: #7bb2db;">Category: <span style="color: #f8fafc;">{escaped_cat}</span></div>')
            if app.comment:
                escaped_desc = html.escape(app.comment.strip())
                tooltip_html.append(f'  <div style="font-size: 13px; color: #7bb2db;">Description: <span style="color: #f8fafc;">{escaped_desc}</span></div>')
            if app.clean_command:
                escaped_cmd = html.escape(app.clean_command.strip())
                tooltip_html.append(f'  <div style="font-size: 13px; color: #7bb2db;">Command: <span style="color: #6ee7b7;">{escaped_cmd}</span></div>')
            tooltip_html.append('</div>')

            item.setToolTip("\n".join(tooltip_html))

            item.setData(Qt.ItemDataRole.UserRole, app)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.app_list_widget.setItem(r, c, item)

        count = len(apps)
        self.list_summary_label.setText(f"{count} application{'s' if count != 1 else ''} available")

        # Always start at the top of the category / list
        self.app_list_widget.verticalScrollBar().setValue(0)
        self.app_list_widget.horizontalScrollBar().setValue(0)
        if self.app_list_widget.rowCount() > 0:
            top_item = self.app_list_widget.item(0, 0)
            if top_item is not None:
                self.app_list_widget.scrollToItem(top_item, QAbstractItemView.ScrollHint.PositionAtTop)
                self.app_list_widget.setCurrentCell(0, 0)

    def _on_category_clicked(self, category_filter) -> None:
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
        if not data:
            return

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
            matched = False
            for r in range(self.app_list_widget.rowCount()):
                for c in range(2):
                    item = self.app_list_widget.item(r, c)
                    if item:
                        data = item.data(Qt.ItemDataRole.UserRole)
                        if isinstance(data, DesktopAppInfo):
                            if data.desktop_file == entry.desktop_file or data.desktop_id == entry.desktop_file:
                                self.app_list_widget.setCurrentItem(item)
                                self.selected_scanner_app = data
                                matched = True
                                break
                if matched:
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
            entry_id = self.existing_entry.id if self.existing_entry else str(uuid.uuid4())
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

            entry_id = self.existing_entry.id if self.existing_entry else str(uuid.uuid4())

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

    def _on_add_clicked(self) -> None:
        """Adds current configuration to the profile, updates feedback, and remains open to add more."""
        entry = self._create_app_entry_from_form()
        if not entry:
            return

        self.added_count += 1
        self.result_entry = entry
        self.app_added.emit(entry)
        if self.on_app_added_callback:
            self.on_app_added_callback(entry)

        count_text = f"{self.added_count} added" if self.added_count > 1 else "1 added"
        self.feedback_label.setText(f"Added '{entry.name}' ({count_text})")
        self.feedback_label.show()

    def _on_add_to_profile_only(self) -> None:
        """Compatibility wrapper for batch adding without closing."""
        self._on_add_clicked()

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

    def _on_app_double_clicked(self, item: QTableWidgetItem) -> None:
        """Double clicking an application adds it in add mode, or saves in edit mode."""
        if not item or not item.data(Qt.ItemDataRole.UserRole):
            return
        if self.is_edit_mode:
            self._on_save_and_close()
        else:
            self._on_add_clicked()

    def _on_close_clicked(self) -> None:
        """Closes the dialog."""
        if self.added_count > 0:
            self.accept()
        else:
            self.reject()

    def get_result(self) -> Optional[AppEntry]:
        return self.result_entry

