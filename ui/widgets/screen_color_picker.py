import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter


class ScreenshotOverlay(QWidget):
    def __init__(self, screenshot,  paretn_callback):
        super().__init__()
        self.screenshot = screenshot
        self.current_color = QColor(0, 0, 0)
        self.mouse_pos = None
        self.paretn_callback = paretn_callback
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)
        self.showFullScreen()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.screenshot)
        
        # Draw color indicator circle near cursor
        if self.mouse_pos:
            # Draw circle
            painter.setPen(Qt.GlobalColor.white)
            painter.setBrush(self.current_color)
            circle_size = 40
            offset = 20
            circle_x = self.mouse_pos.x() + offset
            circle_y = self.mouse_pos.y() - offset
            painter.drawEllipse(circle_x, circle_y, circle_size, circle_size)
            
            # Draw black outline
            painter.setPen(Qt.GlobalColor.black)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(circle_x, circle_y, circle_size, circle_size)
    
    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        
        # Get color at cursor position
        image = self.screenshot.toImage()
        ratio = self.screenshot.devicePixelRatio()
        x = int(self.mouse_pos.x() * ratio)
        y = int(self.mouse_pos.y() * ratio)
        
        if 0 <= x < image.width() and 0 <= y < image.height():
            self.current_color = QColor(image.pixel(x, y))
        
        self.update()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            image = self.screenshot.toImage()
            
            # Get device pixel ratio for high DPI screens
            ratio = self.screenshot.devicePixelRatio()
            x = int(pos.x() * ratio)
            y = int(pos.y() * ratio)
            
            color = QColor(image.pixel(x, y))
            self.paretn_callback(color)
            self.close()
        elif event.button() == Qt.MouseButton.RightButton:
            self.close()
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
