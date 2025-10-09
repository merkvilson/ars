import sys
import math
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QSlider, QHBoxLayout, QGraphicsView, QGraphicsScene
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPainterPath, QPen
from .b_button import BButton, BButtonConfig

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

class TimelineWidget(QWidget):
    def __init__(self, frame_count=50, parent=None):
        super().__init__(parent)
        self.frame_count = frame_count

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Colors
        self.bg_color = QColor(70, 70, 70, 200)
        self.text_color = QColor(255, 255, 255, 200)

        # Tick height limits relative to the center circle diameter
        self.major_height_ratio = 2.00
        self.minor_height_ratio = 0.50

        # Pen width bounds
        self.pen_min = 3.0
        self.pen_max = 6.0

        # Setup QGraphicsView and Scene for BButton
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setStyleSheet("border: none; background: transparent;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Layout to position the QGraphicsView
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        # BButton configuration for slider
        button_config = BButtonConfig(
            symbol=str(self.frame_count),
            font=QFont("Arial", 14, QFont.Weight.Bold),
            slider_values=(0, 999, self.frame_count),
            incremental_value=25,
            show_value=False,
            callbackL=self.update_frame_count
        )
        self.button = BButton(button_config)
        self.scene.addItem(self.button)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Center the BButton in the scene
        width = float(self.width())
        height = float(self.height())
        radius = 22.0
        self.button.setPos(width / 2, height / 2)
        self.view.setSceneRect(0, 0, width, height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Geometry
        width = float(self.width())
        height = float(self.height())
        timeline_y = height / 2.0
        center_x = width / 2.0
        radius = 22.0
        diameter = 2.0 * radius

        # Draw arch ticks on both sides
        if self.frame_count > 0:
            side_count = self.frame_count // 2
            if side_count == 0:
                painter.end()
                return

            side_width = (width / 2.0) - radius
            side_width = max(0.0, side_width)

            radial_step = side_width / (side_count + 1)
            ideal_pen = 0.6 * radial_step
            pen_width = clamp(ideal_pen, self.pen_min, self.pen_max)

            pen = QPen(self.text_color)
            pen.setWidthF(pen_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            for i in range(side_count):
                t = (i / (side_count - 1)) if side_count > 1 else 0.0
                height_factor = 1.0 - 0.5 * t

                is_major = ((i + 1) % 10 == 0)
                max_base_px = (self.major_height_ratio if is_major else self.minor_height_ratio) * diameter
                desired_height = max_base_px * height_factor

                R = radius + (i + 1) * radial_step
                max_geom_height = max(0.0, 2.0 * R - 2.0)
                H = min(desired_height, max_geom_height)

                if H <= 0.0:
                    continue

                sin_arg = clamp(H / (2.0 * R), -1.0, 1.0)
                alpha_rad = math.asin(sin_arg)
                alpha_deg = math.degrees(alpha_rad)

                arc_rect = QRectF(center_x - R, timeline_y - R, 2.0 * R, 2.0 * R)

                path_left = QPainterPath()
                start_left = 180.0 - alpha_deg
                sweep_left = 2.0 * alpha_deg
                path_left.arcMoveTo(arc_rect, start_left)
                path_left.arcTo(arc_rect, start_left, sweep_left)
                painter.drawPath(path_left)

                path_right = QPainterPath()
                start_right = -alpha_deg
                sweep_right = 2.0 * alpha_deg
                path_right.arcMoveTo(arc_rect, start_right)
                path_right.arcTo(arc_rect, start_right, sweep_right)
                painter.drawPath(path_right)

        painter.end()

    def update_frame_count(self, count):
        self.frame_count = int(round(count))
        self.button.set_updated_config("symbol", str(self.frame_count))
        self.update()