"""Frameless window support and custom window headers for AutoLaunch.

Provides Wayland-native window dragging via QWindow.startSystemMove(),
custom window control buttons (minimize, close), and drop-shadow acrylic frames.
Complies with zero-emoji guidelines and dynamic path resolution.
"""

from typing import Optional

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QFont, QMouseEvent
from PyQt6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QPushButton, QVBoxLayout, QWidget
)


class WindowControls(QWidget):
    """Custom minimize and close window buttons for frameless windows."""

    def __init__(self, parent_window: QWidget, show_minimize: bool = True):
        super().__init__()
        self.parent_window = parent_window

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        btn_base_style = """
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: 1px solid transparent;
                border-radius: 6px;
                font-family: monospace;
                font-size: 13px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
        """

        if show_minimize:
            self.min_btn = QPushButton("-")
            self.min_btn.setFixedSize(28, 28)
            self.min_btn.setStyleSheet(btn_base_style)
            self.min_btn.setToolTip("Minimize")
            self.min_btn.clicked.connect(self.parent_window.showMinimized)
            layout.addWidget(self.min_btn)

        self.close_btn = QPushButton("x")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: 1px solid transparent;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self.parent_window.close)
        layout.addWidget(self.close_btn)


class DraggableHeader(QFrame):
    """A custom header bar that moves frameless windows using Wayland system move."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._drag_pos: Optional[QPoint] = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            # If native Wayland system move is available, trigger it
            wh = win.windowHandle()
            if wh and hasattr(wh, "startSystemMove") and wh.startSystemMove():
                event.accept()
                return

            self._drag_pos = event.globalPosition().toPoint() - win.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class FramelessDialogBase(QDialog):
    """Base modal dialog with frameless window styling and custom title bar."""

    def __init__(self, parent: Optional[QWidget] = None, title: str = ""):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Outer layout with padding for drop shadow
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        # Elevated body frame
        self.body_frame = QFrame()
        self.body_frame.setStyleSheet("""
            QFrame {
                background-color: #0d121f;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self.body_frame)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 6)
        self.body_frame.setGraphicsEffect(shadow)

        self.content_layout = QVBoxLayout(self.body_frame)
        self.content_layout.setContentsMargins(16, 12, 16, 16)
        self.content_layout.setSpacing(12)

        # Header bar
        self.dialog_header = DraggableHeader()
        self.dialog_header.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(self.dialog_header)
        header_layout.setContentsMargins(4, 2, 4, 4)

        self.title_label = QLabel(title)
        title_font = QFont("Inter, Segoe UI, sans-serif", 13, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #f1f5f9; background: transparent; border: none;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.controls = WindowControls(self, show_minimize=False)
        header_layout.addWidget(self.controls)

        self.content_layout.addWidget(self.dialog_header)
        outer_layout.addWidget(self.body_frame)
