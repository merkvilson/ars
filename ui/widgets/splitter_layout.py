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
        self.bottom_height = 80
        self.left_width = 150
        self.right_width = 150
        
        self.handle_size = 8
        self._dragging = None
        
        # Colors (semi-transparent)
        self.top_color = QColor(180, 60, 60, 10)
        self.bottom_color = QColor(60, 180, 60, 10)
        self.left_color = QColor(60, 60, 180, 10)
        self.right_color = QColor(180, 180, 60, 10)
        
        self.cursor_modifier = CursorModifier(
            trigger_widget=self,
            axis="xy",
            teleport_back=False,
            cursor_type=None,
            active_condition=lambda e: self._get_handle_at(e.pos()) is not None
        )
        
        self.setMouseTracking(True)
        self._update_mask()
    
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
        painter.fillRect(0, 0, self.width(), self.top_height, self.top_color)
        # Bottom
        painter.fillRect(0, self.height() - self.bottom_height, self.width(), self.bottom_height, self.bottom_color)
        # Left
        painter.fillRect(0, self.top_height, self.left_width, self.height() - self.top_height - self.bottom_height, self.left_color)
        # Right
        painter.fillRect(self.width() - self.right_width, self.top_height, self.right_width, self.height() - self.top_height - self.bottom_height, self.right_color)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = self._get_handle_at(event.pos())
    
    def mouseMoveEvent(self, event):
        if self._dragging:
            pos = event.pos()
            min_size = 20
            max_center = 100
            
            if self._dragging == "top":
                self.top_height = max(min_size, min(pos.y(), self.height() - self.bottom_height - max_center))
            elif self._dragging == "bottom":
                self.bottom_height = max(min_size, min(self.height() - pos.y(), self.height() - self.top_height - max_center))
            elif self._dragging == "left":
                self.left_width = max(min_size, min(pos.x(), self.width() - self.right_width - max_center))
            elif self._dragging == "right":
                self.right_width = max(min_size, min(self.width() - pos.x(), self.width() - self.left_width - max_center))
            
            self._update_mask()
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
