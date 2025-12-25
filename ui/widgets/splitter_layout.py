from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QRegion, QPainter, QColor
from PyQt6.QtWidgets import QWidget
from core.cursor_modifier import set_cursor, CursorModifier


class SplitterOverlay(QWidget):
    """Overlay with 4 resizable edge areas and a click-through center hole."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Edge sizes
        self.top_height = 80
        self.bottom_height = 15
        self.left_width = 15
        self.right_width = 15
        
        self.handle_size = 8
        self._dragging = None
        
        self.bottom_widget = None
        self.left_widget = None
        self.top_widget = None
        self.right_widget = None

        # Colors (semi-transparent)
        self.bg_color = QColor(255, 255, 255, 0)
        
        self.cursor_modifier = CursorModifier(
            trigger_widget=self,
            axis="xy",
            teleport_back=False,
            cursor_type=None,
            active_condition=lambda e: self._get_handle_at(e.pos()) is not None
        )
        
        self.setMouseTracking(True)
        self._update_mask()
    
    def set_widget(self, position: str, widget: QWidget):
        if position == "bottom":
            if self.bottom_widget:
                self.bottom_widget.setParent(None)
                self.bottom_widget.deleteLater()
            
            self.bottom_widget = widget
            if self.bottom_widget:
                self.bottom_widget.setParent(self)
                self.bottom_widget.show()
                self._update_geometries()
        
        elif position == "left":
            if self.left_widget:
                self.left_widget.setParent(None)
                self.left_widget.deleteLater()
            
            self.left_widget = widget
            if self.left_widget:
                self.left_widget.setParent(self)
                self.left_widget.show()
                self._update_geometries()

        elif position == "top":
            if self.top_widget:
                self.top_widget.setParent(None)
                self.top_widget.deleteLater()
            
            self.top_widget = widget
            if self.top_widget:
                self.top_widget.setParent(self)
                self.top_widget.show()
                self._update_geometries()

        elif position == "right":
            if self.right_widget:
                self.right_widget.setParent(None)
                self.right_widget.deleteLater()
            
            self.right_widget = widget
            if self.right_widget:
                self.right_widget.setParent(self)
                self.right_widget.show()
                self._update_geometries()

    def _update_geometries(self):
        offset = self.handle_size
        
        if self.bottom_widget:
            # Leave space for the handle
            self.bottom_widget.setGeometry(
                0, 
                self.height() - self.bottom_height + offset, 
                self.width(), 
                max(0, self.bottom_height - offset)
            )
            
        if self.left_widget:
            # Leave space for the handle
            self.left_widget.setGeometry(
                0,
                self.top_height, # Start below top area
                self.left_width - offset,
                self.height() - self.top_height - self.bottom_height
            )

        if self.top_widget:
            # Leave space for the handle
            self.top_widget.setGeometry(
                0,
                0,
                self.width(),
                max(0, self.top_height - offset)
            )

        if self.right_widget:
            # Leave space for the handle
            self.right_widget.setGeometry(
                self.width() - self.right_width + offset,
                self.top_height,
                max(0, self.right_width - offset),
                self.height() - self.top_height - self.bottom_height
            )

    def _update_mask(self):
        """Create a mask with a hole in the center."""
        full = QRegion(self.rect())
        center = QRegion(QRect(
            self.left_width, 
            self.top_height,
            self.width() - self.left_width - self.right_width,
            self.height() - self.top_height - self.bottom_height
        ))
        self.setMask(full.subtracted(center))
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_mask()
        self._update_geometries()
    
    def _get_handle_at(self, pos) -> str | None:
        y_top = self.top_height
        y_bottom = self.height() - self.bottom_height
        x_left = self.left_width
        x_right = self.width() - self.right_width
        hs = self.handle_size
        
        # Horizontal handles (top/bottom edges)
        if abs(pos.y() - y_top) < hs and x_left < pos.x() < x_right:
            return "top"
        if abs(pos.y() - y_bottom) < hs and x_left < pos.x() < x_right:
            return "bottom"
        # Vertical handles (left/right edges)  
        if abs(pos.x() - x_left) < hs and y_top < pos.y() < y_bottom:
            return "left"
        if abs(pos.x() - x_right) < hs and y_top < pos.y() < y_bottom:
            return "right"
        return None
    
    def paintEvent(self, event):
        painter = QPainter(self)
        # Top
        painter.fillRect(0, 0, self.width(), self.top_height, self.bg_color)
        # Bottom
        painter.fillRect(0, self.height() - self.bottom_height, self.width(), self.bottom_height, self.bg_color)
        # Left
        painter.fillRect(0, self.top_height, self.left_width, self.height() - self.top_height - self.bottom_height, self.bg_color)
        # Right
        painter.fillRect(self.width() - self.right_width, self.top_height, self.right_width, self.height() - self.top_height - self.bottom_height, self.bg_color)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = self._get_handle_at(event.pos())
    
    def mouseMoveEvent(self, event):
        if self._dragging:
            pos = event.pos()
            min_size = 20
            max_center = 10
            
            if self._dragging == "top":
                self.top_height = max(min_size, min(pos.y(), self.height() - self.bottom_height - max_center))
            elif self._dragging == "bottom":
                self.bottom_height = max(min_size, min(self.height() - pos.y(), self.height() - self.top_height - max_center))
            elif self._dragging == "left":
                self.left_width = max(min_size, min(pos.x(), self.width() - self.right_width - max_center))
            elif self._dragging == "right":
                self.right_width = max(min_size, min(self.width() - pos.x(), self.width() - self.left_width - max_center))
            
            self._update_mask()
            self._update_geometries()
            self.update()
        else:
            handle = self._get_handle_at(event.pos())
            if handle in ("top", "bottom"):
                self.cursor_modifier.axis = "y"
                self.cursor_modifier.set_cursor_type("arrows-move-vertical", anchor="center")
                set_cursor("arrows-move-vertical", anchor="center")
            elif handle in ("left", "right"):
                self.cursor_modifier.axis = "x"
                self.cursor_modifier.set_cursor_type("arrows-move-horizontal", anchor="center")
                set_cursor("arrows-move-horizontal", anchor="center")
            else:
                set_cursor("cursor", anchor="top_left")
    
    def mouseReleaseEvent(self, event):
        self._dragging = None
        set_cursor("cursor", anchor="top_left")
    
    def leaveEvent(self, event):
        set_cursor("cursor", anchor="top_left")
        super().leaveEvent(event)
