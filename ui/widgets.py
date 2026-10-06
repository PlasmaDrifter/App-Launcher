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


class StepperSpinBox(QWidget):
    """SpinBox with prominent +/- stepper buttons and read-only value display."""

    valueChanged = pyqtSignal(int)

    def __init__(
        self,
        minimum: int = 0,
        maximum: int = 300,
        value: int = 0,
        suffix: str = " seconds",
        step: int = 1,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._minimum = minimum
        self._maximum = maximum
        self._value = max(minimum, min(value, maximum))
        self._suffix = suffix
        self._step = step

        from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        stepper_btn_style = """
            QPushButton {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
                padding: 0px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #38bdf8;
                color: #38bdf8;
            }
            QPushButton:pressed {
                background-color: #0f172a;
            }
            QPushButton:disabled {
                background-color: #111827;
                color: #475569;
                border-color: #1f2937;
            }
        """

        self.minus_btn = QPushButton("−")
        self.minus_btn.setStyleSheet(stepper_btn_style)
        self.minus_btn.clicked.connect(self._decrement)

        self.display_label = QLabel()
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display_label.setStyleSheet("""
            QLabel {
                background-color: #111827;
                color: #f8fafc;
                border: 1px solid #28354f;
                border-radius: 6px;
                padding: 5px 14px;
                font-weight: 600;
                font-size: 13px;
                min-width: 90px;
                min-height: 20px;
            }
        """)

        self.plus_btn = QPushButton("+")
        self.plus_btn.setStyleSheet(stepper_btn_style)
        self.plus_btn.clicked.connect(self._increment)

        layout.addWidget(self.minus_btn)
        layout.addWidget(self.display_label)
        layout.addWidget(self.plus_btn)
        layout.addStretch()

        self._update_display()

    def _decrement(self) -> None:
        self.setValue(self._value - self._step)

    def _increment(self) -> None:
        self.setValue(self._value + self._step)

    def _update_display(self) -> None:
        self.display_label.setText(f"{self._value}{self._suffix}")
        self.minus_btn.setEnabled(self._value > self._minimum and self.isEnabled())
        self.plus_btn.setEnabled(self._value < self._maximum and self.isEnabled())

    def value(self) -> int:
        return self._value

    def setValue(self, val: int) -> None:
        clamped = max(self._minimum, min(val, self._maximum))
        if clamped != self._value:
            self._value = clamped
            self._update_display()
            self.valueChanged.emit(self._value)

    def setMinimum(self, val: int) -> None:
        self._minimum = val
        self.setValue(self._value)

    def setMaximum(self, val: int) -> None:
        self._maximum = val
        self.setValue(self._value)

    def setRange(self, minimum: int, maximum: int) -> None:
        self._minimum = minimum
        self._maximum = maximum
        self.setValue(self._value)

    def setSuffix(self, suffix: str) -> None:
        self._suffix = suffix
        self._update_display()

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self.display_label.setEnabled(enabled)
        if not enabled:
            self.minus_btn.setEnabled(False)
            self.plus_btn.setEnabled(False)
            self.display_label.setStyleSheet("""
                QLabel {
                    background-color: #0f172a;
                    color: #475569;
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                    padding: 5px 14px;
                    font-weight: 600;
                    font-size: 13px;
                    min-width: 90px;
                    min-height: 20px;
                }
            """)
        else:
            self.display_label.setStyleSheet("""
                QLabel {
                    background-color: #111827;
                    color: #f8fafc;
                    border: 1px solid #28354f;
                    border-radius: 6px;
                    padding: 5px 14px;
                    font-weight: 600;
                    font-size: 13px;
                    min-width: 90px;
                    min-height: 20px;
                }
            """)
            self._update_display()

