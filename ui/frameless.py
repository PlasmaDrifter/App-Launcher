"""Frameless window support and custom window headers for AutoLaunch.

Provides Wayland-native window dragging via QWindow.startSystemMove(),
custom window control buttons (minimize, close), and drop-shadow acrylic frames.
Complies with zero-emoji guidelines and dynamic path resolution.
"""

from typing import Optional

from PyQt6.QtCore import QPoint, QRect, Qt, QTimer, QEvent, QObject
from PyQt6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import (
    QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
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
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        # Hover background & glow
        if self._hovered:
            if self.kind == "close":
                bg_color = QColor(185, 75, 75) if self._pressed else QColor(185, 75, 75, 190)
                border_color = QColor(210, 105, 105, 170)
                glyph_color = QColor("#ffffff")
            else:
                bg_color = QColor(45, 85, 120) if self._pressed else QColor(45, 85, 120, 180)
                border_color = QColor(70, 115, 155, 160)
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


class WindowControls(QWidget):
    """Clean minimize and close window buttons in the upper right without bounding box."""

    def __init__(self, parent_window: QWidget, show_minimize: bool = True):
        super().__init__()
        self.parent_window = parent_window

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        if show_minimize:
            self.min_btn = WindowButton("minimize")
            self.min_btn.setToolTip("Minimize")
            self.min_btn.clicked.connect(self.parent_window.showMinimized)
            layout.addWidget(self.min_btn)

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


class FramelessResizeHandler(QObject):
    """Provides interactive border hovering and manual resizing for frameless windows and dialogs."""

    BORDER_WIDTH = 10
    CORNER_SIZE = 16

    EDGE_MAP = {
        "T": Qt.Edge.TopEdge,
        "B": Qt.Edge.BottomEdge,
        "L": Qt.Edge.LeftEdge,
        "R": Qt.Edge.RightEdge,
        "TL": Qt.Edge.TopEdge | Qt.Edge.LeftEdge,
        "TR": Qt.Edge.TopEdge | Qt.Edge.RightEdge,
        "BL": Qt.Edge.BottomEdge | Qt.Edge.LeftEdge,
        "BR": Qt.Edge.BottomEdge | Qt.Edge.RightEdge,
    }

    def __init__(self, target_window: QWidget):
        super().__init__(target_window)
        self.window = target_window
        self.window.setMouseTracking(True)
        self.resizing_edge: Optional[str] = None
        self.drag_start_pos: Optional[QPoint] = None
        self.drag_start_geo: Optional[QRect] = None
        self._cursor_overridden = False
        self._cursor_shape: Optional[Qt.CursorShape] = None

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        self.window.destroyed.connect(self.cleanup)

        self._enable_mouse_tracking(self.window)

    def cleanup(self) -> None:
        self._restore_cursor()
        app = QApplication.instance()
        if app is not None:
            try:
                app.removeEventFilter(self)
            except Exception:
                pass

    def attach_to_widget(self, widget: QWidget) -> None:
        """Enables mouse tracking on a widget and its children to ensure mouse move events are delivered."""
        self._enable_mouse_tracking(widget)

    def _enable_mouse_tracking(self, widget: QWidget) -> None:
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)

    def _set_resize_cursor(self, cursor_shape: Qt.CursorShape) -> None:
        if self._cursor_shape == cursor_shape:
            return
        if self._cursor_overridden:
            QApplication.restoreOverrideCursor()
            self._cursor_overridden = False
        QApplication.setOverrideCursor(cursor_shape)
        self._cursor_overridden = True
        self._cursor_shape = cursor_shape

    def _restore_cursor(self) -> None:
        if self._cursor_overridden:
            QApplication.restoreOverrideCursor()
            self._cursor_overridden = False
            self._cursor_shape = None

    def _get_edge(self, watched: QWidget, pos_in_watched: QPoint) -> str:
        # Avoid intercepting window buttons (Close, Minimize)
        if isinstance(watched, WindowButton):
            return ""

        # Map position accurately to window coordinates
        local_pos = watched.mapTo(self.window, pos_in_watched)
        x = local_pos.x()
        y = local_pos.y()
        w = self.window.width()
        h = self.window.height()

        if x < 0 or x > w or y < 0 or y > h:
            return ""

        # Check corners first
        if x <= self.CORNER_SIZE and y <= self.CORNER_SIZE:
            return "TL"
        if x >= w - self.CORNER_SIZE and y <= self.CORNER_SIZE:
            return "TR"
        if x <= self.CORNER_SIZE and y >= h - self.CORNER_SIZE:
            return "BL"
        if x >= w - self.CORNER_SIZE and y >= h - self.CORNER_SIZE:
            return "BR"

        # Check edges
        if y <= self.BORDER_WIDTH:
            return "T"
        if y >= h - self.BORDER_WIDTH:
            return "B"
        if x <= self.BORDER_WIDTH:
            return "L"
        if x >= w - self.BORDER_WIDTH:
            return "R"

        return ""

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not isinstance(watched, QWidget) or watched.window() != self.window:
            return super().eventFilter(watched, event)

        # Dynamically ensure mouse tracking is active as widgets receive hover
        if event.type() in (QEvent.Type.Enter, QEvent.Type.ChildAdded, QEvent.Type.Show):
            if not watched.hasMouseTracking():
                watched.setMouseTracking(True)

        if event.type() == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
            if self.resizing_edge is not None and self.drag_start_pos is not None and self.drag_start_geo is not None:
                delta = event.globalPosition().toPoint() - self.drag_start_pos
                geo = self.drag_start_geo

                min_w = self.window.minimumWidth()
                min_h = self.window.minimumHeight()

                new_x = geo.x()
                new_y = geo.y()
                new_w = geo.width()
                new_h = geo.height()

                if "R" in self.resizing_edge:
                    new_w = max(min_w, geo.width() + delta.x())
                elif "L" in self.resizing_edge:
                    new_w = max(min_w, geo.width() - delta.x())
                    new_x = geo.right() - new_w + 1

                if "B" in self.resizing_edge:
                    new_h = max(min_h, geo.height() + delta.y())
                elif "T" in self.resizing_edge:
                    new_h = max(min_h, geo.height() - delta.y())
                    new_y = geo.bottom() - new_h + 1

                self.window.setGeometry(new_x, new_y, new_w, new_h)
                event.accept()
                return True

            edge = self._get_edge(watched, event.position().toPoint())
            if edge in ("L", "R"):
                self._set_resize_cursor(Qt.CursorShape.SizeHorCursor)
            elif edge in ("T", "B"):
                self._set_resize_cursor(Qt.CursorShape.SizeVerCursor)
            elif edge in ("TL", "BR"):
                self._set_resize_cursor(Qt.CursorShape.SizeFDiagCursor)
            elif edge in ("TR", "BL"):
                self._set_resize_cursor(Qt.CursorShape.SizeBDiagCursor)
            elif self._cursor_overridden:
                self._restore_cursor()

        elif event.type() == QEvent.Type.MouseButtonPress and isinstance(event, QMouseEvent):
            if event.button() == Qt.MouseButton.LeftButton:
                edge = self._get_edge(watched, event.position().toPoint())
                if edge:
                    edge_flag = self.EDGE_MAP.get(edge)
                    wh = self.window.windowHandle()
                    if not wh and hasattr(self.window, "winId"):
                        self.window.winId()
                        wh = self.window.windowHandle()

                    if wh and edge_flag is not None and hasattr(wh, "startSystemResize"):
                        self._restore_cursor()
                        if wh.startSystemResize(edge_flag):
                            event.accept()
                            return True

                    self.resizing_edge = edge
                    self.drag_start_pos = event.globalPosition().toPoint()
                    self.drag_start_geo = self.window.geometry()
                    event.accept()
                    return True

        elif event.type() == QEvent.Type.MouseButtonRelease and isinstance(event, QMouseEvent):
            if self.resizing_edge is not None:
                self.resizing_edge = None
                self.drag_start_pos = None
                self.drag_start_geo = None
                self._restore_cursor()
                event.accept()
                return True

        elif event.type() == QEvent.Type.Leave and watched == self.window:
            if self.resizing_edge is None and self._cursor_overridden:
                self._restore_cursor()

        return super().eventFilter(watched, event)


class FramelessDialogBase(QDialog):
    """Base modal dialog with frameless window styling and custom title bar."""

    def __init__(self, parent: Optional[QWidget] = None, title: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title or "AutoLaunch Dialog")
        self.setWindowRole("dialog")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet("background-color: #0d121f;")

        self.resize_handler = FramelessResizeHandler(self)

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

    def center_over_parent(self) -> None:
        """Positions the dialog centered over its parent window, or screen center if no parent."""
        parent = self.parentWidget()
        dlg_width = self.width() if self.width() > 0 else self.sizeHint().width()
        dlg_height = self.height() if self.height() > 0 else self.sizeHint().height()

        if parent:
            parent_geo = parent.frameGeometry()
            # Align dialog center with the parent window's center
            x = parent_geo.x() + (parent_geo.width() - dlg_width) // 2
            y = parent_geo.y() + (parent_geo.height() - dlg_height) // 2
            self.move(x, y)
        else:
            screen = self.screen()
            if screen:
                screen_geo = screen.availableGeometry()
                x = screen_geo.left() + (screen_geo.width() - dlg_width) // 2
                y = screen_geo.top() + (screen_geo.height() - dlg_height) // 2
                self.move(x, y)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.center_over_parent()
        # Schedule an immediate adjustment on the event loop in case compositor/window manager
        # sets initial geometry during window map
        QTimer.singleShot(0, self.center_over_parent)
