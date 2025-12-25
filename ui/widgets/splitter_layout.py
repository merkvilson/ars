from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QRegion, QPainter, QColor
from PyQt6.QtWidgets import QWidget
from core.cursor_modifier import set_cursor, CursorModifier


class SplitterOverlay(QWidget):
    """Overlay with 4 resizable edge areas and a click-through center hole."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Edge sizes
        self.top_height = 70
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
    
    def _get_effective_sizes(self):
        th = self.top_height if self.top_widget else 0
        bh = self.bottom_height if self.bottom_widget else 0
        lw = self.left_width if self.left_widget else 0
        rw = self.right_width if self.right_widget else 0
        return th, bh, lw, rw

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
            self._update_mask()
        
        elif position == "left":
            if self.left_widget:
                self.left_widget.setParent(None)
                self.left_widget.deleteLater()
            
            self.left_widget = widget
            if self.left_widget:
                self.left_widget.setParent(self)
                self.left_widget.show()
            self._update_geometries()
            self._update_mask()

        elif position == "top":
            if self.top_widget:
                self.top_widget.setParent(None)
                self.top_widget.deleteLater()
            
            self.top_widget = widget
            if self.top_widget:
                self.top_widget.setParent(self)
                self.top_widget.show()
            self._update_geometries()
            self._update_mask()

        elif position == "right":
            if self.right_widget:
                self.right_widget.setParent(None)
                self.right_widget.deleteLater()
            
            self.right_widget = widget
            if self.right_widget:
                self.right_widget.setParent(self)
                self.right_widget.show()
            self._update_geometries()
            self._update_mask()

    def _update_geometries(self):
        offset = self.handle_size
        th, bh, lw, rw = self._get_effective_sizes()
        
        if self.bottom_widget:
            # Leave space for the handle
            self.bottom_widget.setGeometry(
                0, 
                self.height() - bh + offset, 
                self.width(), 
                max(0, bh - offset)
            )
            
        if self.left_widget:
            # Leave space for the handle
            self.left_widget.setGeometry(
                0,
                th, # Start below top area
                lw - offset,
                self.height() - th - bh
            )

        if self.top_widget:
            # Leave space for the handle
            self.top_widget.setGeometry(
                0,
                0,
                self.width(),
                max(0, th - offset)
            )

        if self.right_widget:
            # Leave space for the handle
            self.right_widget.setGeometry(
                self.width() - rw + offset,
                th,
                max(0, rw - offset),
                self.height() - th - bh
            )

    def _update_mask(self):
        """Create a mask with a hole in the center."""
        th, bh, lw, rw = self._get_effective_sizes()
        full = QRegion(self.rect())
        center = QRegion(QRect(
            lw, 
            th,
            self.width() - lw - rw,
            self.height() - th - bh
        ))
        self.setMask(full.subtracted(center))
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_mask()
        self._update_geometries()
    
    def _get_handle_at(self, pos) -> str | None:
        th, bh, lw, rw = self._get_effective_sizes()
        
        y_top = th
        y_bottom = self.height() - bh
        x_left = lw
        x_right = self.width() - rw
        hs = self.handle_size
        
        # Horizontal handles (top/bottom edges)
        if th > 0 and abs(pos.y() - y_top) < hs and x_left < pos.x() < x_right:
            return "top"
        if bh > 0 and abs(pos.y() - y_bottom) < hs and x_left < pos.x() < x_right:
            return "bottom"
        # Vertical handles (left/right edges)  
        if lw > 0 and abs(pos.x() - x_left) < hs and y_top < pos.y() < y_bottom:
            return "left"
        if rw > 0 and abs(pos.x() - x_right) < hs and y_top < pos.y() < y_bottom:
            return "right"
        return None
    
    def paintEvent(self, event):
        painter = QPainter(self)
        th, bh, lw, rw = self._get_effective_sizes()
        # Top
        if th > 0:
            painter.fillRect(0, 0, self.width(), th, self.bg_color)
        # Bottom
        if bh > 0:
            painter.fillRect(0, self.height() - bh, self.width(), bh, self.bg_color)
        # Left
        if lw > 0:
            painter.fillRect(0, th, lw, self.height() - th - bh, self.bg_color)
        # Right
        if rw > 0:
            painter.fillRect(self.width() - rw, th, rw, self.height() - th - bh, self.bg_color)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = self._get_handle_at(event.pos())
    
    def mouseMoveEvent(self, event):
        if self._dragging:
            pos = event.pos()
            min_size = 20
            max_center = 10
            th, bh, lw, rw = self._get_effective_sizes()
            
            if self._dragging == "top":
                self.top_height = max(min_size, min(pos.y(), self.height() - bh - max_center))
            elif self._dragging == "bottom":
                self.bottom_height = max(min_size, min(self.height() - pos.y(), self.height() - th - max_center))
            elif self._dragging == "left":
                self.left_width = max(min_size, min(pos.x(), self.width() - rw - max_center))
            elif self._dragging == "right":
                self.right_width = max(min_size, min(self.width() - pos.x(), self.width() - lw - max_center))
            
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
