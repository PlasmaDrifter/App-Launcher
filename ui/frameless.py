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


class WindowButton(QPushButton):
    """Refined window action button with vector-drawn glyphs and animated hover effects."""

    def __init__(self, kind: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.kind = kind  # 'minimize' or 'close'
        self.setFixedSize(26, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False
        self._pressed = False

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        from PyQt6.QtGui import QPainter, QPainterPath, QPen, QColor, QRadialGradient

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        # Hover background & glow
        if self._hovered:
            if self.kind == "close":
                bg_color = QColor("#ef4444") if self._pressed else QColor(239, 68, 68, 210)
                border_color = QColor(248, 113, 113, 200)
                glyph_color = QColor("#ffffff")
            else:
                bg_color = QColor("#2563eb") if self._pressed else QColor(37, 99, 235, 180)
                border_color = QColor(96, 165, 250, 180)
                glyph_color = QColor("#ffffff")

            painter.setBrush(bg_color)
            painter.setPen(QPen(border_color, 1.0))
            painter.drawRoundedRect(1, 1, w - 2, h - 2, 6, 6)
        else:
            glyph_color = QColor("#7d8fa6")

        # Crisp vector glyphs
        pen = QPen(glyph_color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        if self.kind == "close":
            arm = 4.2
            painter.drawLine(int(cx - arm), int(cy - arm), int(cx + arm), int(cy + arm))
            painter.drawLine(int(cx - arm), int(cy + arm), int(cx + arm), int(cy - arm))
        elif self.kind == "minimize":
            arm = 4.5
            painter.drawLine(int(cx - arm), int(cy + 1), int(cx + arm), int(cy + 1))


class WindowControls(QFrame):
    """Custom minimize and close window controls pill with polished glassmorphism aesthetics."""

    def __init__(self, parent_window: QWidget, show_minimize: bool = True):
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("WindowControlsBox")
        self.setStyleSheet("""
            QFrame#WindowControlsBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a2333, stop:1 #111827);
                border: 1px solid #28374f;
                border-radius: 8px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        if show_minimize:
            self.min_btn = WindowButton("minimize")
            self.min_btn.setToolTip("Minimize")
            self.min_btn.clicked.connect(self.parent_window.showMinimized)
            layout.addWidget(self.min_btn)

            # Elegant micro-divider between minimize and close
            sep = QFrame()
            sep.setFixedSize(1, 14)
            sep.setStyleSheet("background-color: #243247; border: none;")
            layout.addWidget(sep)

        self.close_btn = WindowButton("close")
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
        self.setStyleSheet("background-color: #0d121f;")

        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(16, 12, 16, 16)
        self.content_layout.setSpacing(12)

        # Header bar
        self.dialog_header = DraggableHeader()
        self.dialog_header.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 4px;
            }
        """)
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
