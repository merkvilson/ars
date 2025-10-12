from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QPen
from PyQt6.QtCore import Qt
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic

# water_widget.py
# Requirements: pip install PyQt6 numpy
import sys
import numpy as np
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPainter, QImage
from PyQt6.QtWidgets import QWidget, QApplication, QMainWindow




import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPainterPath, QLinearGradient, QPen
from PyQt6.QtCore import QTimer, Qt

class WaterWidget(QWidget):
    """
    A 2D water fluid simulation widget for PyQt6.
    Simulates a calm water surface in a tank that reacts subtly to mouse cursor interaction.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Simulation parameters tuned for calm, smooth waves that settle quickly
        self.num_columns = 40  # Higher resolution for smoother appearance
        self.tension = 0.025    # Restoring force strength
        self.damping = 0.08     # Damping to make waves fade out reasonably fast
        self.spread = 0.32      # Propagation speed between columns
        self.splash_strength = 18.0  # Mouse disturbance strength, tuned for visible but not exaggerated reaction
        
        # Water level (y-position from top, y increases downward)
        self.target_height_ratio = 0.55
        self.target_height = 0
        self.heights = []
        self.velocities = []
        
        self.setMouseTracking(True)
        
        # Update timer for ~60 FPS
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(16)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.target_height = self.height() * self.target_height_ratio
        self.heights = [self.target_height] * self.num_columns
        self.velocities = [0.0] * self.num_columns

    def update_simulation(self):
        """Update the physics simulation."""
        # Compute accelerations from restoring forces and damping
        for i in range(self.num_columns):
            force = self.tension * (self.target_height - self.heights[i])
            self.velocities[i] += force
            self.velocities[i] *= (1 - self.damping)
        
        # Compute spreads to neighbors (using current heights)
        spreads = [0.0] * self.num_columns
        for i in range(self.num_columns):
            if i > 0:
                spreads[i-1] += self.spread * (self.heights[i] - self.heights[i-1])
            if i < self.num_columns - 1:
                spreads[i+1] += self.spread * (self.heights[i] - self.heights[i+1])
        
        # Apply spreads and update positions
        for i in range(self.num_columns):
            self.velocities[i] += spreads[i]
            self.heights[i] += self.velocities[i]
            # Clamp to prevent wild oscillations
            if abs(self.velocities[i]) > 3.0:
                self.velocities[i] = 3.0 * (1 if self.velocities[i] > 0 else -1)
        
        self.update()  # Repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        if self.num_columns == 0 or self.width() == 0:
            return
        
        column_width = self.width() / (self.num_columns - 1)
        
        # Water body fill with gradient
        gradient = QLinearGradient(0, self.target_height, 0, self.height())
        gradient.setColorAt(0, QColor(102, 204, 255))  # Light blue
        gradient.setColorAt(0.5, QColor(51, 153, 255))  # Mid blue
        gradient.setColorAt(1, QColor(0, 102, 204))     # Dark blue
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        
        path = QPainterPath()
        path.moveTo(0, self.height())
        for i in range(self.num_columns):
            x = i * column_width
            y = self.heights[i]
            path.lineTo(x, y)
        path.lineTo(self.width(), self.height())
        path.closeSubpath()
        painter.drawPath(path)
        
        # Surface highlight line
        path = QPainterPath()
        path.moveTo(0, self.heights[0])
        for i in range(1, self.num_columns):
            x = i * column_width
            y = self.heights[i]
            path.lineTo(x, y)
        pen = QPen(QColor(255, 255, 255, 128), 2.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
        # Simple reflection overlay
        if self.height() > self.target_height:
            ref_gradient = QLinearGradient(0, self.target_height, 0, self.target_height + 30)
            ref_gradient.setColorAt(0, QColor(255, 255, 255, 40))
            ref_gradient.setColorAt(1, QColor(255, 255, 255, 0))
            
            ref_path = QPainterPath()
            ref_path.moveTo(0, self.heights[0])
            for i in range(self.num_columns):
                x = i * column_width
                y = self.heights[i]
                ref_path.lineTo(x, y)
            ref_path.lineTo(self.width(), self.target_height + 30)
            ref_path.lineTo(0, self.target_height + 30)
            ref_path.closeSubpath()
            
            painter.setBrush(QBrush(ref_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(ref_path)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        if self.width() == 0 or self.num_columns == 0:
            return
        
        column_width = self.width() / (self.num_columns - 1)
        col = min(max(int(pos.x() / column_width), 0), self.num_columns - 1)
        
        surface_y = self.heights[col]
        penetration = pos.y() - surface_y
        
        if penetration > 0:  # Cursor below surface
            # Subtle downward push proportional to penetration (max at 15px)
            max_pen = 15.0
            if penetration < max_pen:
                force = self.splash_strength * (penetration / max_pen)
                # Apply to column and neighbors for smoothness
                for d in [-1, 0, 1]:
                    n = col + d
                    if 0 <= n < self.num_columns:
                        self.velocities[n] += force * (0.5 if abs(d) == 1 else 1.0)




class WaterWidget2(QWidget):
    """
    A reusable QWidget that simulates ripples on a water surface.
    - Mouse movement injects disturbances into the surface.
    - No texts or buttons; purely visual.
    - Can be embedded into any PyQt6 layout.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        # Simulation parameters
        self._c2 = 0.10      # Wave propagation coefficient (stable ~<= 0.25)
        self._damping = 0.996  # Velocity damping (0..1), higher = longer lasting
        self._foam_scale = 0.03  # Tweak foam intensity

        # Light direction for shading (normalized)
        self._light_dir = np.array([0.3, 0.9, 0.25], dtype=np.float32)
        self._light_dir /= np.linalg.norm(self._light_dir) + 1e-8

        # Simulation state
        self._w = 0
        self._h = 0
        self._h_curr = None
        self._h_prev = None
        self._h_next = None
        self._frame_rgb = None
        self._last_pos = None

        self._init_sim()

        # Update timer (~60 FPS)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def sizeHint(self) -> QSize:
        return QSize(640, 400)

    # ---- Simulation setup ----
    def _init_sim(self):
        w = max(4, self.width() or 640)
        h = max(4, self.height() or 400)
        self._w, self._h = w, h

        self._h_curr = np.zeros((h, w), dtype=np.float32)
        self._h_prev = np.zeros_like(self._h_curr)
        self._h_next = np.zeros_like(self._h_curr)
        self._frame_rgb = np.zeros((h, w, 3), dtype=np.uint8)

    def resizeEvent(self, event):
        self._init_sim()
        super().resizeEvent(event)

    # ---- Simulation step ----
    def _tick(self):
        if self._w < 3 or self._h < 3:
            return

        h = self._h_curr
        hp = self._h_prev
        hn = self._h_next

        # Interior update (discrete wave equation with damping)
        hi = h[1:-1, 1:-1]
        hip = hp[1:-1, 1:-1]
        lap = (h[:-2, 1:-1] + h[2:, 1:-1] + h[1:-1, :-2] + h[1:-1, 2:] - 4.0 * hi)

        v = (hi - hip) * self._damping
        hn[1:-1, 1:-1] = hi + v + self._c2 * lap

        # Zero boundary (absorbing-ish)
        hn[0, :] = 0.0
        hn[-1, :] = 0.0
        hn[:, 0] = 0.0
        hn[:, -1] = 0.0

        # Rotate buffers: prev <- curr, curr <- next
        self._h_prev, self._h_curr, self._h_next = self._h_curr, self._h_next, self._h_prev

        # Trigger repaint
        self.update()

    # ---- Rendering ----
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.SmoothPixmapTransform, False)

        rgb = self._render_rgb()
        # Keep reference so QImage uses valid memory
        self._frame_rgb = rgb
        img = QImage(self._frame_rgb.data, self._w, self._h, self._w * 3, QImage.Format.Format_RGB888)
        painter.drawImage(0, 0, img)

    def _render_rgb(self) -> np.ndarray:
        h = self._h_curr
        H, W = h.shape

        # Central differences for surface gradient (normals)
        dx = np.zeros_like(h)
        dy = np.zeros_like(h)
        dx[:, 1:-1] = 0.5 * (h[:, 2:] - h[:, :-2])
        dy[1:-1, :] = 0.5 * (h[2:, :] - h[:-2, :])

        nx = -dx
        ny = np.ones_like(h) * 2.0
        nz = -dy
        inv_len = 1.0 / np.sqrt(nx * nx + ny * ny + nz * nz + 1e-6)
        nx *= inv_len
        ny *= inv_len
        nz *= inv_len

        Lx, Ly, Lz = self._light_dir
        diff = np.clip(nx * Lx + ny * Ly + nz * Lz, 0.0, 1.0)  # diffuse term

        # Specular glints (cheap)
        spec = np.power(diff, 30.0)

        # Foam from curvature magnitude
        lap = np.zeros_like(h)
        lap[1:-1, 1:-1] = (h[:-2, 1:-1] + h[2:, 1:-1] + h[1:-1, :-2] + h[1:-1, 2:] - 4.0 * h[1:-1, 1:-1])
        foam = np.clip(np.abs(lap) / (self._foam_scale + 1e-6), 0.0, 1.0)

        # Base water tint
        base = np.zeros((H, W, 3), dtype=np.float32)
        base[..., 0] = 20   # R
        base[..., 1] = 100  # G
        base[..., 2] = 200  # B

        brightness = 0.35 + 0.65 * diff  # 0.35 .. 1.0
        img = base * brightness[..., None]
        img += (255.0 * (spec * 0.35))[..., None]  # subtle white highlights
        img = img * (1.0 - foam[..., None] * 0.3) + 255.0 * (foam * 0.3)[..., None]

        np.clip(img, 0, 255, out=img)
        return img.astype(np.uint8)

    # ---- Interaction ----
    def add_impulse(self, x: int, y: int, radius=8, strength=1.5):
        # Add a smooth bump at (x, y)
        if self._w <= 2 or self._h <= 2:
            return
        r = int(radius)
        x0 = max(1, x - r)
        x1 = min(self._w - 1, x + r + 1)
        y0 = max(1, y - r)
        y1 = min(self._h - 1, y + r + 1)
        if x0 >= x1 or y0 >= y1:
            return

        yy, xx = np.ogrid[y0:y1, x0:x1]
        dist2 = (xx - x) ** 2 + (yy - y) ** 2
        mask = dist2 <= r * r
        g = np.exp(-dist2 / (0.5 * r * r + 1e-6)).astype(np.float32)
        patch = self._h_curr[y0:y1, x0:x1]
        patch[mask] += strength * g[mask]

    def mouseMoveEvent(self, event):
        pos = event.position()
        x, y = int(pos.x()), int(pos.y())
        if 0 <= x < self._w and 0 <= y < self._h:
            speed = 0.0
            if self._last_pos is not None:
                dx = x - self._last_pos[0]
                dy = y - self._last_pos[1]
                speed = float(np.hypot(dx, dy))
            # Always react to movement; stronger with speed
            self.add_impulse(x, y, radius=6 + min(16, speed * 0.5), strength=0.5 + 0.15 * speed)

        self._last_pos = (x, y)

    def leaveEvent(self, event):
        self._last_pos = None
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        pos = event.position()
        x, y = int(pos.x()), int(pos.y())
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.add_impulse(x, y, radius=12, strength=4.0)
        elif event.buttons() & Qt.MouseButton.RightButton:
            self.add_impulse(x, y, radius=12, strength=-4.0)



def BBL_Y(self, position):

    # Create the gradient widget
    custom_widget = WaterWidget()
    water_2d = WaterWidget2()
    #custom_widget.position = 30 / 100.0  # Set initial position based on slider default
    #custom_widget.setFixedSize(100, 500)  # Fixed size for the custom widget
    config = ContextMenuConfig()
    config.auto_close = False
    options_list = ["X", "Y", "Z", "A", "B", "C",]

    config.inner_widgets = {"X": custom_widget, "B": water_2d}
    config.slider_values = {"Y": (0,100,30), "Z": (0,100,30), "A": (0,100,30)}
    config.editable_items = {"X": False}

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
    
    return ctx  # Return the context menu if you need to handle its result