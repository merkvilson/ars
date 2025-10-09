# cursor_modifier.py
from PyQt6.QtWidgets import QWidget, QApplication, QGraphicsObject, QGraphicsView
from PyQt6.QtCore import QObject, QEvent, Qt, QPoint, QSize
from PyQt6.QtGui import QCursor, QPixmap, QMouseEvent, QColor, QPainter, QPaintEvent
from PyQt6.QtSvg import QSvgRenderer
import os

# -----------------------------------------------------------------------------
# NEW CURSOR WIDGET & HELPER FUNCTIONS
# -----------------------------------------------------------------------------

class CursorIconWidget(QWidget):
    """A frameless, transparent widget to display a custom cursor pixmap."""
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.ToolTip  # ToolTip helps it stay on top and avoid the taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating) # Prevents stealing focus
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def set_pixmap(self, pixmap: QPixmap):
        """Sets the pixmap to display and resizes the widget to match."""
        self._pixmap = pixmap
        self.setFixedSize(pixmap.size())
        self.update() # Trigger a repaint

    def paintEvent(self, event: QPaintEvent):
        """Draws the stored pixmap on the widget."""
        if self._pixmap:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self._pixmap)

def create_qcursor(name: str, bg_color: QColor | None = None, anchor: str = "top_left") -> QCursor:
    """Renders an SVG icon into a QCursor object."""
    icon_path = os.path.join("res", "icons", "cursor", f"{name}.svg")
    renderer = QSvgRenderer(icon_path)
    if not renderer.isValid():
        print(f"Warning: Could not load cursor SVG: {icon_path}. Falling back to default.")
        return QCursor(Qt.CursorShape.ArrowCursor)
    icon_size = renderer.defaultSize()
    radius = 22
    diameter = radius * 2
    canvas_size = QSize(diameter, diameter) if bg_color else icon_size
    icon_pixmap = QPixmap(icon_size)
    icon_pixmap.fill(Qt.GlobalColor.transparent)
    icon_painter = QPainter(icon_pixmap)
    renderer.render(icon_painter)
    icon_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    cursor_color = QColor(255, 255, 255, 180)
    icon_painter.fillRect(icon_pixmap.rect(), cursor_color)
    icon_painter.end()
    final_pixmap = QPixmap(canvas_size)
    final_pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(final_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if bg_color:
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, diameter, diameter)
    icon_x = (canvas_size.width() - icon_size.width()) / 2
    icon_y = (canvas_size.height() - icon_size.height()) / 2
    painter.drawPixmap(int(icon_x), int(icon_y), icon_pixmap)
    painter.end()
    hot_x, hot_y = 0, 0
    if anchor == "center":
        hot_x = final_pixmap.width() // 2
        hot_y = final_pixmap.height() // 2
    return QCursor(final_pixmap, hot_x, hot_y)

def set_default_cursor(cursor_name: str):
    """Sets the default, application-wide cursor."""
    app = QApplication.instance()
    if not app:
        print("Warning: QApplication instance not found. Cannot set default cursor.")
        return
    default_cursor = create_qcursor(cursor_name, bg_color=None, anchor="top_left")
    QApplication.setOverrideCursor(default_cursor)

def show_cursor(value: bool = True):
    """Shows or hides the application-wide cursor."""
    app = QApplication.instance()
    if not app:
        print("Warning: QApplication instance not found. Cannot modify cursor visibility.")
        return
    current = QApplication.overrideCursor()
    if value:
        # Show: remove any BlankCursor overrides from the top of the stack
        while current and current.shape() == Qt.CursorShape.BlankCursor:
            QApplication.restoreOverrideCursor()
            current = QApplication.overrideCursor()
    else:
        # Hide: set to BlankCursor if not already
        if not current or current.shape() != Qt.CursorShape.BlankCursor:
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))

# -----------------------------------------------------------------------------
# UPDATED MODIFIER CLASS
# -----------------------------------------------------------------------------

class CursorModifier(QObject):
    """
    Minimal, robust cursor modifier that:
      - Locks cursor movement along 'x', 'y' or 'xy'
      - Optionally teleports cursor to `target` while active and teleports back on release
      - Supports QWidget / QGraphicsObject (QObject) triggers AND QGraphicsItem triggers
        (by checking scene.itemAt(view.mapToScene(event.pos()))).
    Notes (minimal behavior):
      - IMPORTANT: this modifier does NOT consume MouseMove or MouseButtonRelease events.
        That lets the target widget (slider/handle) receive its release/move events and
        clear drag state properly.
    """
    def __init__(self,
                 trigger_widget,
                 target: QPoint | tuple[int, int] | None = None,
                 teleport_back: bool = True,
                 hide_on_press: bool = False,
                 cursor_type: str | tuple[str, str, str] | None = None,
                 bg_color: QColor | None = None,
                 anchor: str = "top_left",
                 axis: str = "xy",
                 mouse_button: Qt.MouseButton = Qt.MouseButton.LeftButton,
                 parent: QObject | None = None):
        super().__init__(parent)
        if axis not in ("xy", "x", "y"):
            raise ValueError("Argument 'axis' must be one of 'xy', 'x', or 'y'.")
        if anchor not in ("top_left", "center"):
            raise ValueError("Argument 'anchor' must be one of 'top_left' or 'center'.")
        self.trigger_widget = trigger_widget
        self.teleport_back = teleport_back
        self.hide_on_press = hide_on_press
        self.mouse_button = mouse_button
        self.cursor_type = cursor_type
        self.bg_color = bg_color
        self.anchor = anchor
        self.axis = axis
        self._cursor_variants: list[QCursor] = []
        self._custom_cursor: QCursor | None = None
        if isinstance(cursor_type, str):
            self._custom_cursor = self._make_cursor(cursor_type)
        elif isinstance(cursor_type, (tuple, list)) and len(cursor_type) == 3:
            self._cursor_variants = [self._make_cursor(icon) for icon in cursor_type]
        elif cursor_type is not None:
            raise ValueError("cursor_type must be None, a string, or a tuple/list of three strings")
        self.target_pos = QPoint(*target) if isinstance(target, tuple) else target
        self._is_active = False
        self._original_pos: QPoint | None = None
        self._lock_pos: QPoint | None = None
        self._start_pos: QPoint | None = None
        self._icon_widget: CursorIconWidget | None = None
        self._current_cursor_obj: QCursor | None = None
        self._has_install = hasattr(self.trigger_widget, "installEventFilter") and callable(getattr(self.trigger_widget, "installEventFilter"))
        if self._has_install:
            try:
                self.trigger_widget.installEventFilter(self)
            except Exception:
                self._has_install = False
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        self._is_graphics_item = hasattr(self.trigger_widget, "scene") and callable(getattr(self.trigger_widget, "scene"))

    def _make_cursor(self, name: str) -> QCursor:
        return create_qcursor(name, self.bg_color, self.anchor)

    def _start_modification(self):
        if self._is_active:
            return
        self._is_active = True
        self._original_pos = QCursor.pos()
        self._start_pos = QPoint(self._original_pos)
        self._lock_pos = QPoint(self.target_pos) if self.target_pos is not None else QPoint(self._original_pos)
        self._current_cursor_obj = self._custom_cursor or (self._cursor_variants[0] if self._cursor_variants else None)

        if self.axis in ('x', 'y') and self._current_cursor_obj:
            QApplication.setOverrideCursor(Qt.CursorShape.BlankCursor)
            self._icon_widget = CursorIconWidget()
            self._icon_widget.set_pixmap(self._current_cursor_obj.pixmap())
            start_widget_pos = self.target_pos if self.target_pos is not None else self._original_pos
            hotspot = self._current_cursor_obj.hotSpot()
            self._icon_widget.move(start_widget_pos - hotspot)
            self._icon_widget.show()
            if self.target_pos is not None:
                QCursor.setPos(self.target_pos)
        else:
            if self._current_cursor_obj:
                QApplication.setOverrideCursor(self._current_cursor_obj)
            elif self.hide_on_press:
                QApplication.setOverrideCursor(Qt.CursorShape.BlankCursor)
            if self.target_pos is not None:
                QCursor.setPos(self.target_pos)

    def _stop_modification(self):
        if not self._is_active:
            return
        if self._icon_widget and self._current_cursor_obj:
            hotspot = self._current_cursor_obj.hotSpot()
            final_pos = self._icon_widget.pos() + hotspot
            QCursor.setPos(final_pos)
            self._icon_widget.hide()
            self._icon_widget.deleteLater()
            self._icon_widget = None
        QApplication.restoreOverrideCursor()
        if self.teleport_back and self._original_pos is not None:
            QCursor.setPos(self._original_pos)
        self._original_pos = None
        self._lock_pos = None
        self._start_pos = None
        self._is_active = False

    def _is_press_on_graphics_trigger(self, watched_obj, event: QMouseEvent) -> bool:
        try:
            scene = self.trigger_widget.scene()
            if scene is None: return False
            for view in scene.views():
                if watched_obj is view or (hasattr(view, "viewport") and watched_obj is view.viewport()):
                    scene_pos = view.mapToScene(event.pos())
                    item = scene.itemAt(scene_pos, view.transform())
                    if item is self.trigger_widget: return True
        except Exception: return False
        return False

    def eventFilter(self, watched_obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress and isinstance(event, QMouseEvent) and event.button() == self.mouse_button:
            if self._has_install and watched_obj is self.trigger_widget:
                if not self._is_active: self._start_modification()
                return False
            if self._is_graphics_item:
                if self._is_press_on_graphics_trigger(watched_obj, event):
                    if not self._is_active: self._start_modification()
                    return False
        if event.type() == QEvent.Type.MouseButtonRelease and isinstance(event, QMouseEvent) and event.button() == self.mouse_button:
            if self._is_active: self._stop_modification()
            return False

        if self._is_active and event.type() == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
            current_pos = event.globalPosition().toPoint()
            if self._icon_widget:
                hotspot = self._current_cursor_obj.hotSpot()
                new_widget_pos = QPoint()
                if self.axis == "x":
                    new_widget_pos.setX(current_pos.x() - hotspot.x())
                    new_widget_pos.setY(self._lock_pos.y() - hotspot.y())
                elif self.axis == "y":
                    new_widget_pos.setX(self._lock_pos.x() - hotspot.x())
                    new_widget_pos.setY(current_pos.y() - hotspot.y())
                self._icon_widget.move(new_widget_pos)
                if self._cursor_variants and self._start_pos is not None:
                    dist_vec = current_pos - self._start_pos
                    new_cursor = self._cursor_variants[0]
                    if dist_vec.manhattanLength() > 22:
                        if self.axis == "x":
                            new_cursor = self._cursor_variants[1] if dist_vec.x() < 0 else self._cursor_variants[2]
                        elif self.axis == "y":
                            new_cursor = self._cursor_variants[2] if dist_vec.y() < 0 else self._cursor_variants[1]
                    if new_cursor is not self._current_cursor_obj:
                        self._current_cursor_obj = new_cursor
                        self._icon_widget.set_pixmap(new_cursor.pixmap())
            else:
                if self.axis == "x" and self._lock_pos is not None:
                    QCursor.setPos(QPoint(current_pos.x(), int(self._lock_pos.y())))
                elif self.axis == "y" and self._lock_pos is not None:
                    QCursor.setPos(QPoint(int(self._lock_pos.x()), current_pos.y()))
                if self._cursor_variants and self.axis in ("x", "y") and self._start_pos is not None:
                    dist_vec = current_pos - self._start_pos
                    new_cursor = self._cursor_variants[0]
                    if dist_vec.manhattanLength() > 22:
                        if self.axis == "x":
                            new_cursor = self._cursor_variants[1] if dist_vec.x() < 0 else self._cursor_variants[2]
                        elif self.axis == "y":
                            new_cursor = self._cursor_variants[2] if dist_vec.y() < 0 else self._cursor_variants[1]
                    if QApplication.overrideCursor() is not new_cursor:
                        QApplication.changeOverrideCursor(new_cursor)
            return False
        return super().eventFilter(watched_obj, event)