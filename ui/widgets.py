"""Custom modern UI widgets for AutoLaunch.

Provides an animated toggle switch and custom badge pills.
Complies with zero-emoji guidelines.
"""

from typing import Optional

from PyQt6.QtCore import (
    QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, pyqtProperty, pyqtSignal
)
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPaintEvent
from PyQt6.QtWidgets import QAbstractButton, QLabel, QWidget


class ToggleSwitch(QAbstractButton):
    """Modern iOS/macOS-style animated toggle switch."""

    def __init__(self, parent: Optional[QWidget] = None, width: int = 38, height: int = 20):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(width, height)

        # 0.0 = unchecked (left), 1.0 = checked (right)
        self._thumb_position = 1.0 if self.isChecked() else 0.0

        self._animation = QPropertyAnimation(self, b"thumb_position", self)
        self._animation.setDuration(160)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.toggled.connect(self._on_toggled)

    @pyqtProperty(float)
    def thumb_position(self) -> float:
        return self._thumb_position

    @thumb_position.setter
    def thumb_position(self, pos: float) -> None:
        self._thumb_position = pos
        self.update()

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        self._thumb_position = 1.0 if checked else 0.0
        self.update()

    def _on_toggled(self, checked: bool) -> None:
        self._animation.stop()
        self._animation.setStartValue(self._thumb_position)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def sizeHint(self) -> QSize:
        return QSize(44, 24)

    def paintEvent(self, event: QPaintEvent) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        radius = h / 2.0

        # Background track color: interpolate between inactive and active
        # Inactive: #334155, Active: #38bdf8
        t = self._thumb_position
        r = int(51 + (56 - 51) * t)
        g = int(65 + (189 - 65) * t)
        b = int(85 + (248 - 85) * t)
        track_color = QColor(r, g, b)

        # Draw track
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(track_color))
        p.drawRoundedRect(QRectF(0, 0, w, h), radius, radius)

        # Thumb
        thumb_diameter = h - 6
        thumb_x = 3 + self._thumb_position * (w - thumb_diameter - 6)
        thumb_y = 3

        # Thumb shadow (soft ring)
        p.setBrush(QBrush(QColor(0, 0, 0, 40)))
        p.drawEllipse(QRectF(thumb_x - 0.5, thumb_y + 0.5, thumb_diameter + 1, thumb_diameter + 1))

        # Thumb body
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.drawEllipse(QRectF(thumb_x, thumb_y, thumb_diameter, thumb_diameter))

        p.end()


class BadgePill(QLabel):
    """Sleek pill-shaped badge for statuses, tags, or delay indicators."""

    def __init__(
        self,
        text: str,
        bg_color: str = "rgba(56, 189, 248, 0.15)",
        text_color: str = "#38bdf8",
        border_color: str = "rgba(56, 189, 248, 0.35)",
        parent: Optional[QWidget] = None
    ):
        super().__init__(text, parent)
        self.setFont(QFont("Inter, Segoe UI, sans-serif", 9, QFont.Weight.Medium))
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 9px;
                padding: 2px 8px;
            }}
        """)
