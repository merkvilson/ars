"""
Demo application for Gaussian Splatting Viewer.

For integration into your app, use:
    from gs_viewer import GaussianSplattingWidget

To run this demo:
    python -m gs_viewer.demo
    OR run demo.py directly
"""
import sys
import os

# Allow running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtGui import QSurfaceFormat

from gs_viewer.gs_widget import GaussianSplattingWidget


class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gaussian Splatting Viewer")
        self.resize(1280, 720)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Gaussian Splatting viewport
        self.gs_viewport = GaussianSplattingWidget(self)
        layout.addWidget(self.gs_viewport)
        
        # Open button
        open_btn = QPushButton("Open PLY", self)
        open_btn.clicked.connect(self.open_ply)
        open_btn.setFixedSize(100, 30)
        open_btn.move(10, 10)
        open_btn.raise_()

    def open_ply(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PLY", "", "PLY Files (*.ply)")
        if file_path:
            count = self.gs_viewport.load_ply(file_path)
            if count:
                print(f"Loaded {count} gaussians")


def main():
    fmt = QSurfaceFormat()
    fmt.setVersion(4, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    fmt.setSwapInterval(0)
    QSurfaceFormat.setDefaultFormat(fmt)
    
    app = QApplication(sys.argv)
    window = DemoWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
