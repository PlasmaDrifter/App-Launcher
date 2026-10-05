"""Dialog for creating or renaming profiles in AutoLaunch."""

from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QWidget
)


class ProfileDialog(QDialog):
    """Simple modal dialog to get a new or updated profile name."""

    def __init__(self, parent: Optional[QWidget] = None, current_name: str = "", title: str = "New Profile"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(340)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        label = QLabel("Profile Name:")
        self.name_input = QLineEdit()
        self.name_input.setText(current_name)
        self.name_input.setPlaceholderText("e.g. Work, Gaming, Daily")

        main_layout.addWidget(label)
        main_layout.addWidget(self.name_input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(cancel_btn)
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
        return getattr(self, "result_name", "")
