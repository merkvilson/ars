import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import QColor, QPainter, QTransform, QCursor
from core.cursor_modifier import set_cursor


class ScreenshotOverlay(QWidget):
    def __init__(self, screenshot,  paretn_callback):
        super().__init__()
        self.screenshot = screenshot
        self.current_color = QColor(0, 0, 0)
        self.mouse_pos = None
        self.paretn_callback = paretn_callback
        
        # Zoom and pan state
        self.zoom_level = 1.0
        self.min_zoom = 1.0
        self.max_zoom = 20.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.is_zoomed = False
        self.last_mouse_pos = None
        self.last_global_pos = None
        
        # Virtual cursor for smooth tracking
        self.virtual_cursor_pos = None
        
        # Timer for tracking raw mouse movement
        self.mouse_timer = QTimer()
        self.mouse_timer.timeout.connect(self.check_mouse_movement)
        self.mouse_timer.setInterval(16)  # ~60 FPS
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setMouseTracking(True)
        self.showFullScreen()
        self.mouse_timer.start()
        
        # Hide cursor using cursor modifier
        set_cursor("invisible")
        
        # Initialize virtual cursor at center
        screen_geo = self.screen().geometry()
        self.virtual_cursor_pos = QPointF(screen_geo.width() / 2, screen_geo.height() / 2)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Apply zoom and pan transformation
        painter.save()
        painter.translate(self.offset_x, self.offset_y)
        painter.scale(self.zoom_level, self.zoom_level)
        painter.drawPixmap(0, 0, self.screenshot)
        painter.restore()
        
        # Draw virtual cursor and color indicator
        if self.virtual_cursor_pos:
            cursor_x = self.virtual_cursor_pos.x()
            cursor_y = self.virtual_cursor_pos.y()
            
            # Draw crosshair cursor
            painter.setPen(Qt.GlobalColor.white)
            line_length = 15
            painter.drawLine(int(cursor_x - line_length), int(cursor_y), int(cursor_x + line_length), int(cursor_y))
            painter.drawLine(int(cursor_x), int(cursor_y - line_length), int(cursor_x), int(cursor_y + line_length))
            
            # Draw color indicator circle near cursor
            painter.setPen(Qt.GlobalColor.white)
            painter.setBrush(self.current_color)
            circle_size = 40
            offset = 20
            circle_x = cursor_x + offset
            circle_y = cursor_y - offset
            painter.drawEllipse(int(circle_x), int(circle_y), circle_size, circle_size)
            
            # Draw black outline
            painter.setPen(Qt.GlobalColor.black)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(int(circle_x), int(circle_y), circle_size, circle_size)
    
    def mouseMoveEvent(self, event):
        # Update virtual cursor position based on mouse movement
        if self.virtual_cursor_pos is None:
            self.virtual_cursor_pos = QPointF(event.pos())
        self.update()
    
    def check_mouse_movement(self):
        """Check actual global mouse position for continuous movement tracking"""
        current_global = QCursor.pos()
        
        if self.last_global_pos is not None:
            # Calculate delta in global coordinates (raw mouse movement)
            delta_x = current_global.x() - self.last_global_pos.x()
            delta_y = current_global.y() - self.last_global_pos.y()
            
            if delta_x != 0 or delta_y != 0:
                # Update virtual cursor position
                self.virtual_cursor_pos.setX(self.virtual_cursor_pos.x() + delta_x)
                self.virtual_cursor_pos.setY(self.virtual_cursor_pos.y() + delta_y)
                
                # Clamp virtual cursor to screen bounds
                screen_geo = self.screen().geometry()
                self.virtual_cursor_pos.setX(max(0, min(screen_geo.width(), self.virtual_cursor_pos.x())))
                self.virtual_cursor_pos.setY(max(0, min(screen_geo.height(), self.virtual_cursor_pos.y())))
                
                # Pan the image if zoomed (opposite direction)
                if self.is_zoomed:
                    self.offset_x -= delta_x
                    self.offset_y -= delta_y
                
                # Recenter real cursor if it's near screen edges
                edge_margin = 100
                needs_recenter = (
                    current_global.x() < edge_margin or 
                    current_global.x() > screen_geo.width() - edge_margin or
                    current_global.y() < edge_margin or 
                    current_global.y() > screen_geo.height() - edge_margin
                )
                
                if needs_recenter:
                    # Move cursor away from edge but not to center
                    new_x = current_global.x()
                    new_y = current_global.y()
                    
                    if current_global.x() < edge_margin:
                        new_x = edge_margin + 100
                    elif current_global.x() > screen_geo.width() - edge_margin:
                        new_x = screen_geo.width() - edge_margin - 100
                    
                    if current_global.y() < edge_margin:
                        new_y = edge_margin + 100
                    elif current_global.y() > screen_geo.height() - edge_margin:
                        new_y = screen_geo.height() - edge_margin - 100
                    
                    QCursor.setPos(new_x, new_y)
                    self.last_global_pos = QCursor.pos()
                else:
                    self.last_global_pos = current_global
                
                # Get color at virtual cursor position
                screen_x = (self.virtual_cursor_pos.x() - self.offset_x) / self.zoom_level
                screen_y = (self.virtual_cursor_pos.y() - self.offset_y) / self.zoom_level
                
                image = self.screenshot.toImage()
                ratio = self.screenshot.devicePixelRatio()
                x = int(screen_x * ratio)
                y = int(screen_y * ratio)
                
                if 0 <= x < image.width() and 0 <= y < image.height():
                    self.current_color = QColor(image.pixel(x, y))
                
                self.update()
        else:
            self.last_global_pos = current_global
        
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming at virtual cursor position"""
        if not self.virtual_cursor_pos:
            return
            
        # Get the point under the virtual cursor in image space before zoom
        old_zoom = self.zoom_level
        screen_x = (self.virtual_cursor_pos.x() - self.offset_x) / old_zoom
        screen_y = (self.virtual_cursor_pos.y() - self.offset_y) / old_zoom
        
        # Update zoom level
        delta = event.angleDelta().y()
        zoom_factor = 1.15 if delta > 0 else 1.0 / 1.15
        self.zoom_level *= zoom_factor
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, self.zoom_level))
        
        # Mark as zoomed if not at base level
        self.is_zoomed = self.zoom_level > 1.01
        
        # Adjust offset so the point under virtual cursor stays under cursor
        self.offset_x = self.virtual_cursor_pos.x() - screen_x * self.zoom_level
        self.offset_y = self.virtual_cursor_pos.y() - screen_y * self.zoom_level
        
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Transform virtual cursor position to image coordinates
            screen_x = (self.virtual_cursor_pos.x() - self.offset_x) / self.zoom_level
            screen_y = (self.virtual_cursor_pos.y() - self.offset_y) / self.zoom_level
            
            image = self.screenshot.toImage()
            
            # Get device pixel ratio for high DPI screens
            ratio = self.screenshot.devicePixelRatio()
            x = int(screen_x * ratio)
            y = int(screen_y * ratio)
            
            if 0 <= x < image.width() and 0 <= y < image.height():
                color = QColor(image.pixel(x, y))
                self.paretn_callback(color)
                set_cursor("cursor")  # Restore cursor before closing
                self.close()
        elif event.button() == Qt.MouseButton.RightButton:
            set_cursor("cursor")  # Restore cursor before closing
            self.close()
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.mouse_timer.stop()
            set_cursor("cursor")  # Restore cursor visibility
            self.close()
    
    def closeEvent(self, event):
        """Ensure timer is stopped and cursor is restored when window closes"""
        self.mouse_timer.stop()
        set_cursor("cursor")  # Restore cursor visibility
        super().closeEvent(event)
