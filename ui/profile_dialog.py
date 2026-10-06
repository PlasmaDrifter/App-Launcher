"""Dialog for creating or renaming profiles in AutoLaunch."""

from typing import Optional

from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QWidget
)

from ui.frameless import FramelessDialogBase


class ProfileDialog(FramelessDialogBase):
    """Simple modal dialog to get a new or updated profile name."""

    def __init__(self, parent: Optional[QWidget] = None, current_name: str = "", title: str = "New Profile"):
        super().__init__(parent, title=title)
        self.result_name: str = ""
        self.setMinimumWidth(360)

        main_layout = self.content_layout
        main_layout.setSpacing(12)

        label = QLabel("Profile Name:")
        label.setStyleSheet("color: #d4d4d8; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        self.name_input = QLineEdit()
        self.name_input.setText(current_name)
        self.name_input.setPlaceholderText("e.g. Work, Gaming, Daily")
        self.name_input.setStyleSheet("""
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

        main_layout.addWidget(label)
        main_layout.addWidget(self.name_input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #202024;
                color: #71717a;
                border: 1px solid #2f2f37;
                border-radius: 6px;
                padding: 7px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #28282e;
                color: #ffffff;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #202024;
                color: #ffffff;
                font-weight: bold;
                border: 1px solid rgba(226, 232, 240, 0.45);
                border-radius: 6px;
                padding: 7px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(226, 232, 240, 0.15);
                border-color: #ffffff;
                color: #ffffff;
            }
        """)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

    def _on_save(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Profile name cannot be empty.")
            return
        self.result_name = name
        self.accept()

    def get_profile_name(self) -> str:
        return self.result_name
