import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont, QColor

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        # Ensure it shows up immediately and stays on top
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self.setFixedSize(500, 300)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QWidget()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QWidget#container {
                background-color: #121212;
                border: 1px solid #333333;
                border-radius: 15px;
            }
            QLabel {
                color: #E0E0E0;
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setSpacing(20)
        
        # Logo
        self.logo_label = QLabel()
        logo_path = os.path.join("res", "icon.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self.logo_label.setPixmap(pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        container_layout.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Title
        self.title_label = QLabel("AIREN STUDIO")
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        container_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status
        self.status_label = QLabel("Initializing...")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet("color: #888888;")
        container_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.container)
        
        # Center on screen
        self.center()

    def center(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def show_message(self, message):
        self.status_label.setText(message)
        self.status_label.repaint() # Force repaint
        QApplication.processEvents()
