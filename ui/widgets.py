"""Custom modern UI widgets for AutoLaunch.

Provides an animated toggle switch and custom badge pills.
Complies with zero-emoji guidelines.
"""

from typing import Optional

from PyQt6.QtCore import (
    QEasingCurve, QPropertyAnimation, QPoint, QRect, QRectF, QSize, Qt, pyqtProperty, pyqtSignal
)
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPaintEvent
from PyQt6.QtWidgets import (
    QAbstractButton, QHBoxLayout, QLabel, QLayout, QLayoutItem, QPushButton,
    QToolTip, QWidget, QSizePolicy
)


class HelpBadge(QPushButton):
    """Circular '?' badge providing helpful configuration info via tooltip and click."""

    def __init__(self, info_text: str, parent: Optional[QWidget] = None, max_pixel_width: int = 290):
        super().__init__("?", parent)
        self._raw_text = info_text
        self._blocked_text = self._wrap_by_pixels(info_text.strip(), max_pixel_width)
        self.setFixedSize(18, 18)
        self.setStyleSheet("""
            QPushButton {
                background-color: #202024;
                color: #4f78a4;
                border: 1.5px solid #4f78a4;
                border-radius: 9px;
                font-size: 11px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #28282e;
                color: #6891bd;
                border: 1.5px solid #6891bd;
            }
        """)
        self.clicked.connect(self._show_info)

    def leaveEvent(self, event) -> None:
        QToolTip.hideText()
        super().leaveEvent(event)

    @staticmethod
    def _wrap_by_pixels(text: str, max_px: int) -> str:
        f = QFont()
        f.setPixelSize(14)
        fm = QFontMetrics(f)
        lines = []
        for paragraph in text.split("\n"):
            words = paragraph.split()
            curr_line = []
            for word in words:
                trial = " ".join(curr_line + [word])
                if fm.horizontalAdvance(trial) > max_px and curr_line:
                    lines.append(" ".join(curr_line))
                    curr_line = [word]
                else:
                    curr_line.append(word)
            if curr_line:
                lines.append(" ".join(curr_line))
        return "\n".join(lines)

    def _show_info(self) -> None:
        # Show tooltip without an early auto-dismiss timeout (-1 or large duration).
        # It stays visible until leaveEvent calls QToolTip.hideText() when the mouse moves away.
        QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), self._blocked_text, self, self.rect(), 300000)


class ElidedLabel(QLabel):
    """A QLabel that automatically truncates and elides text with ellipsis (...) to fit available layout space."""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self._full_text = text
        self.setToolTip(text)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def setText(self, text: str) -> None:
        self._full_text = text
        self.setToolTip(text)
        super().setText(text)
        self.update()

    def minimumSizeHint(self) -> QSize:
        return QSize(20, self.fontMetrics().height())

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.setFont(self.font())
        metrics = self.fontMetrics()
        elided = metrics.elidedText(self._full_text, Qt.TextElideMode.ElideRight, max(0, self.width()))
        painter.drawText(self.rect(), self.alignment() | Qt.AlignmentFlag.AlignVCenter, elided)


class ToggleSwitch(QAbstractButton):
    """Modern iOS/macOS-style animated toggle switch."""

    def __init__(self, parent: Optional[QWidget] = None, width: int = 38, height: int = 20):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(width, height)

        # 0.0 = unchecked (left), 1.0 = checked (right)
        self._thumb_position = 1.0 if self.isChecked() else 0.0
        self._active_color: QColor = QColor(42, 85, 120)
        self._inactive_color: QColor = QColor(51, 65, 85)

        self._animation = QPropertyAnimation(self, b"thumb_position", self)
        self._animation.setDuration(160)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.toggled.connect(self._on_toggled)

    def set_track_colors(self, active: QColor, inactive: Optional[QColor] = None) -> None:
        self._active_color = active
        if inactive is not None:
            self._inactive_color = inactive
        self.update()

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

        t = self._thumb_position
        r = int(self._inactive_color.red() + (self._active_color.red() - self._inactive_color.red()) * t)
        g = int(self._inactive_color.green() + (self._active_color.green() - self._inactive_color.green()) * t)
        b = int(self._inactive_color.blue() + (self._active_color.blue() - self._inactive_color.blue()) * t)
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
        bg_color: str = "rgba(70, 115, 150, 0.15)",
        text_color: str = "#6297bf",
        border_color: str = "rgba(98, 151, 191, 0.4)",
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


STEPPER_BTN_STYLE = """
    QPushButton {
        background-color: #202024;
        color: #d4d4d8;
        border: 1px solid #2f2f37;
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
        background-color: #28282e;
        border-color: #475569;
        color: #d4d4d8;
    }
    QPushButton:pressed {
        background-color: #18181b;
    }
    QPushButton:disabled {
        background-color: #18181b;
        color: #71717a;
        border-color: #2f2f37;
    }
"""

STEPPER_BTN_COMPACT_STYLE = """
    QPushButton {
        background-color: #1e293b;
        color: #f1f5f9;
        border: 1px solid #334155;
        border-radius: 4px;
        font-size: 13px;
        font-weight: bold;
        padding: 0px;
        min-width: 22px;
        max-width: 22px;
        min-height: 24px;
        max-height: 24px;
    }
    QPushButton:hover {
        background-color: #334155;
        border-color: #4a6d8c;
        color: #6297bf;
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

STEPPER_LABEL_STYLE_ENABLED = """
    QLabel {
        background-color: #18181b;
        color: #d4d4d8;
        border: 1px solid #2f2f37;
        border-radius: 6px;
        padding: 5px 14px;
        font-weight: 600;
        font-size: 13px;
        min-width: 90px;
        min-height: 20px;
    }
"""

STEPPER_LABEL_STYLE_DISABLED = """
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
"""

STEPPER_LABEL_COMPACT_ENABLED = """
    QLabel {
        background-color: #111827;
        color: #f8fafc;
        border: 1px solid #28354f;
        border-radius: 4px;
        padding: 2px 6px;
        font-weight: 600;
        font-size: 11px;
        min-width: 44px;
        min-height: 18px;
    }
"""

STEPPER_LABEL_COMPACT_DISABLED = """
    QLabel {
        background-color: #0f172a;
        color: #475569;
        border: 1px solid #1e293b;
        border-radius: 4px;
        padding: 2px 6px;
        font-weight: 600;
        font-size: 11px;
        min-width: 44px;
        min-height: 18px;
    }
"""


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
        compact: bool = False,
    ):
        super().__init__(parent)
        self._minimum = minimum
        self._maximum = maximum
        self._value = max(minimum, min(value, maximum))
        self._suffix = suffix
        self._step = step
        self._compact = compact

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4 if compact else 6)

        btn_style = STEPPER_BTN_COMPACT_STYLE if compact else STEPPER_BTN_STYLE
        label_style = STEPPER_LABEL_COMPACT_ENABLED if compact else STEPPER_LABEL_STYLE_ENABLED

        self.minus_btn = QPushButton("−")
        self.minus_btn.setStyleSheet(btn_style)
        self.minus_btn.clicked.connect(self._decrement)

        self.display_label = QLabel()
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display_label.setStyleSheet(label_style)

        self.plus_btn = QPushButton("+")
        self.plus_btn.setStyleSheet(btn_style)
        self.plus_btn.clicked.connect(self._increment)

        layout.addWidget(self.minus_btn)
        layout.addWidget(self.display_label)
        layout.addWidget(self.plus_btn)
        if not compact:
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
        self._update_display()

    def setMaximum(self, val: int) -> None:
        self._maximum = val
        self.setValue(self._value)
        self._update_display()

    def setRange(self, minimum: int, maximum: int) -> None:
        self._minimum = minimum
        self._maximum = maximum
        self.setValue(self._value)
        self._update_display()

    def setSuffix(self, suffix: str) -> None:
        self._suffix = suffix
        self._update_display()

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self.display_label.setEnabled(enabled)
        if not enabled:
            self.minus_btn.setEnabled(False)
            self.plus_btn.setEnabled(False)
            self.display_label.setStyleSheet(
                STEPPER_LABEL_COMPACT_DISABLED if self._compact else STEPPER_LABEL_STYLE_DISABLED
            )
        else:
            self.display_label.setStyleSheet(
                STEPPER_LABEL_COMPACT_ENABLED if self._compact else STEPPER_LABEL_STYLE_ENABLED
            )
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


