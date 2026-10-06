"""Custom modern UI widgets for AutoLaunch.

Provides an animated toggle switch and custom badge pills.
Complies with zero-emoji guidelines.
"""

from typing import Optional

from PyQt6.QtCore import (
    QEasingCurve, QPropertyAnimation, QPoint, QRect, QRectF, QSize, Qt, pyqtProperty, pyqtSignal
)
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QAbstractButton, QLabel, QWidget, QLayout, QLayoutItem


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
        # Inactive: #334155 (slate-700), Active: #0369a1 (muted dark sky/cyan-slate)
        t = self._thumb_position
        r = int(51 + (3 - 51) * t)
        g = int(65 + (105 - 65) * t)
        b = int(85 + (161 - 85) * t)
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

        # Thumb body (soft off-white)
        p.setBrush(QBrush(QColor(226, 232, 240)))
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


class CheckMarkBox(QAbstractButton):
    """Clean desktop checkbox with an explicit vector checkmark when checked."""

    def __init__(self, parent: Optional[QWidget] = None, size: int = 18):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event: QPaintEvent) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        r = QRectF(1.0, 1.0, w - 2.0, h - 2.0)

        if self.isChecked():
            # Checked: Breeze blue accent with crisp white checkmark
            p.setBrush(QBrush(QColor("#3daee9")))
            p.setPen(QPen(QColor("#3daee9"), 1.0))
            p.drawRoundedRect(r, 3.0, 3.0)

            pen = QPen(QColor("#ffffff"), 2.0)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)

            # Checkmark polyline
            p.drawLine(int(w * 0.25), int(h * 0.52), int(w * 0.44), int(h * 0.72))
            p.drawLine(int(w * 0.44), int(h * 0.72), int(w * 0.75), int(h * 0.28))
        else:
            # Unchecked: Dark inset with border
            p.setBrush(QBrush(QColor("#1b1e20")))
            p.setPen(QPen(QColor("#4f5b66"), 1.5))
            p.drawRoundedRect(r, 3.0, 3.0)

        p.end()


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


class FlowLayout(QLayout):
    """Standard Qt FlowLayout that wraps child widgets across multiple lines."""

    def __init__(self, parent: Optional[QWidget] = None, margin: int = 0, spacing: int = 6):
        super().__init__(parent)
        self.item_list: list[QLayoutItem] = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def addItem(self, item: QLayoutItem) -> None:
        self.item_list.append(item)

    def count(self) -> int:
        return len(self.item_list)

    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        margins = self.contentsMargins()
        effective_rect = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self.item_list:
            wid = item.widget()
            if wid and not wid.isVisible():
                continue

            space_x = spacing
            space_y = spacing
            next_x = x + item.sizeHint().width() + space_x

            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + margins.bottom()


