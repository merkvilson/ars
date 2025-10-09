from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QTimer, Qt
import time

from common.ars_debug import DEBUG_MODE as DBG

class FPSCounter:
    def __init__(self, canvas, parent_widget):
        """
        Initialize an FPS counter overlay for a VisPy canvas.
        
        Args:
            canvas: VisPy SceneCanvas to track draw events.
            parent_widget: QWidget (usually canvas.native) to parent the QLabel.
        """
        # Create QLabel for FPS display
        self.fps_label = QLabel(parent_widget)
        self.fps_label.setText("0 FPS")
        self.fps_label.setStyleSheet("color: yellow; background: rgba(0, 0, 0, 0.5); font-size: 14px; padding: 2px;")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.fps_label.move(10, 10)
        self.fps_label.resize(100, 30)
        self.fps_label.setVisible(True)
        self.fps_label.raise_()

        self.frame_times = []
        self.canvas = canvas

        # Connect to canvas draw event
        def on_draw(ev):
            self.frame_times.append(time.time())
            if DBG: print(f"[DEBUG] Draw event triggered at {time.time()}")  # Debug draw events

        self.canvas.events.draw.connect(on_draw)
        if DBG: print("[DEBUG] Connected draw event handler")

        # Timer to update FPS every 500ms
        self.fps_timer = QTimer(parent_widget)
        self.fps_timer.timeout.connect(self._update_fps)
        self.fps_timer.start(500)
        if DBG: print("[DEBUG] FPS timer started")

    def _update_fps(self):
        """Update FPS display based on frame times in the last second."""
        current = time.time()
        while self.frame_times and self.frame_times[0] < current - 1.0:
            self.frame_times.pop(0)
        fps = len(self.frame_times)
        self.fps_label.setText(f"{fps} FPS")
        if DBG: print(f"[DEBUG] FPS updated: {fps} FPS, frame_times count: {len(self.frame_times)}")

    def toggle_visibility(self):
        """Toggle visibility of the FPS counter."""
        self.fps_label.setVisible(not self.fps_label.isVisible())
        if DBG: print("[DEBUG] FPS label toggled")