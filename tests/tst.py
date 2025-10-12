import sys
from time import perf_counter

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QLinearGradient, QPainterPath, QPen
from PyQt6.QtCore import QTimer, Qt, QPointF


class WaterWidget(QWidget):
    """
    Calm 2D water surface using a damped discrete wave equation.
    - Surface is 1D (columns) and filled downwards to form the water body.
    - Mouse "touch" creates a gentle, localized impulse that dissipates.
    - Numerically stable (CFL clamped), with damping + slight viscosity to avoid jitter.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Simulation params (feel free to tweak)
        self.num_cols = 180          # number of columns along the surface
        self.rest_ratio = 0.73       # baseline water height (0=top, 1=bottom)
        self.wave_speed = 340.0      # px/s; effective wave speed (CFL guarded)
        self.damping = 0.030         # velocity damping (0..~0.1)
        self.viscosity = 0.035       # small smoothing of high-freq ripples (0..~0.1)
        self.touch_radius = 24.0     # px "touch" depth window under the surface
        self.splash_strength = 10.0  # impulse magnitude in px
        self.max_cfl = 0.45          # safety clamp for stability

        # Fixed integration step for stable physics (sub-stepped)
        self.dt_fixed = 1.0 / 120.0
        self._accum = 0.0
        self._last_t = perf_counter()

        # State: displacement from rest line (not absolute y), double-buffer for wave eq
        self.y = [0.0] * self.num_cols
        self.y_prev = [0.0] * self.num_cols
        self.y_next = [0.0] * self.num_cols

        # Rendering helpers
        self.setMouseTracking(True)
        self._rest_y = 0.0  # computed on first paint/resize

        # Timer ~60Hz UI tick; physics runs on fixed dt with substeps
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(16)

    # ---------- Physics ----------

    def _on_tick(self):
        now = perf_counter()
        dt = now - self._last_t
        self._last_t = now
        self._accum += dt

        # Do a few fixed sub-steps to keep CFL stable even if UI hiccups
        max_steps = 5
        steps = 0
        while self._accum >= self.dt_fixed and steps < max_steps:
            self._step_physics(self.dt_fixed)
            self._accum -= self.dt_fixed
            steps += 1

        self.update()

    def _step_physics(self, dt):
        w = max(self.width(), 1)
        dx = w / max(self.num_cols - 1, 1)
        # CFL: (v*dt/dx)^2
        c = (self.wave_speed * dt / dx)
        c2 = c * c
        if c2 > self.max_cfl:
            c2 = self.max_cfl  # clamp for safety

        damp = self.damping
        visc = self.viscosity
        n = self.num_cols

        y = self.y
        yp = self.y_prev
        yn = self.y_next

        # Update interior via damped wave eq:
        # y_next = 2y - y_prev + c^2*(y[i-1] - 2y[i] + y[i+1]) - damping*(y - y_prev)
        for i in range(1, n - 1):
            lap = y[i - 1] - 2.0 * y[i] + y[i + 1]
            yn[i] = (2.0 * y[i] - yp[i]) + c2 * lap - damp * (y[i] - yp[i])

        # Fixed walls at edges (container sides)
        yn[0] = 0.0
        yn[n - 1] = 0.0

        # Light viscosity (numerical smoothing) to kill high-frequency chatter
        if visc > 0.0 and n > 2:
            left = yn[0]
            for i in range(1, n - 1):
                neighbor_avg = 0.5 * (yn[i - 1] + yn[i + 1])
                yn[i] = yn[i] * (1.0 - visc) + neighbor_avg * visc
            yn[n - 1] = 0.0

        # Swap buffers (yp <- y, y <- yn)
        self.y_prev, self.y, self.y_next = self.y, self.y_next, self.y_prev

        # Tiny cleanup of near-zero noise
        eps = 1e-4
        for i in range(n):
            if -eps < self.y[i] < eps and -eps < self.y_prev[i] < eps:
                self.y[i] = 0.0
                self.y_prev[i] = 0.0

    # ---------- Interaction ----------

    def mouseMoveEvent(self, event):
        if self.width() <= 1 or self.num_cols < 2:
            return
        pos = event.position()
        dx = self.width() / (self.num_cols - 1)
        idx = int(round(pos.x() / dx))
        idx = max(0, min(self.num_cols - 1, idx))

        surface_y = self._rest_line_at(idx)
        depth = pos.y() - surface_y  # >0 means cursor is inside water
        if 0.0 < depth < self.touch_radius:
            # Make an impulse proportional to penetration depth, spread with Gaussian-ish weights
            # Apply to y_prev to create velocity (so the wave moves downward/upward smoothly)
            base = self.splash_strength * (depth / self.touch_radius)

            weights = [0.08, 0.24, 0.36, 0.24, 0.08]  # symmetric, sums to 1.0
            k0 = -2
            for k, w in enumerate(weights):
                i = idx + k0 + k
                if 0 <= i < self.num_cols:
                    self.y_prev[i] -= base * w  # subtract to push surface down (positive velocity)

    def _rest_line_at(self, i):
        # Absolute y coordinate of the rest surface at column i
        return self._rest_y

    # ---------- Drawing ----------

    def paintEvent(self, event):
        if self.height() <= 0 or self.width() <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Update rest line each frame (so it follows resize smoothly)
        self._rest_y = self.height() * self.rest_ratio

        # Build surface points
        dx = self.width() / max(self.num_cols - 1, 1)
        pts = []
        for i in range(self.num_cols):
            x = i * dx
            y = self._rest_y + self.y[i]
            pts.append(QPointF(x, y))

        # Smooth surface via Catmull–Rom converted to Bezier
        surface_path = self._catmull_rom_path(pts)

        # Fill the water body with gradient
        water_path = QPainterPath(surface_path)
        water_path.lineTo(self.width(), self.height())
        water_path.lineTo(0, self.height())
        water_path.closeSubpath()

        gradient = QLinearGradient(0, self._rest_y - 40, 0, self.height())
        gradient.setColorAt(0.0, QColor("#69c7ff"))
        gradient.setColorAt(0.5, QColor("#3ea5ff"))
        gradient.setColorAt(1.0, QColor("#1170cc"))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawPath(water_path)

        # Subtle surface highlight
        pen = QPen(QColor(255, 255, 255, 140))
        pen.setWidthF(1.4)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(surface_path)

        # Optional container outline
        outline = QPen(QColor(0, 0, 0, 60))
        outline.setWidth(1)
        painter.setPen(outline)
        painter.drawRect(self.rect())

    def _catmull_rom_path(self, points):
        """Build a smooth path through points using Catmull–Rom (uniform) to cubic Bezier."""
        path = QPainterPath()
        if not points:
            return path
        if len(points) < 2:
            path.moveTo(points[0])
            return path

        path.moveTo(points[0])

        # Helper to clamp index
        def P(idx):
            if idx < 0:
                return points[0]
            if idx >= len(points):
                return points[-1]
            return points[idx]

        for i in range(len(points) - 1):
            p0 = P(i - 1)
            p1 = P(i)
            p2 = P(i + 1)
            p3 = P(i + 2)

            # Catmull-Rom to Bezier (alpha=0.5 uniform)
            c1x = p1.x() + (p2.x() - p0.x()) / 6.0
            c1y = p1.y() + (p2.y() - p0.y()) / 6.0
            c2x = p2.x() - (p3.x() - p1.x()) / 6.0
            c2y = p2.y() - (p3.y() - p1.y()) / 6.0
            path.cubicTo(c1x, c1y, c2x, c2y, p2.x(), p2.y())

        return path

    def resizeEvent(self, event):
        # Keep state, just adjust rest line implicitly via height
        super().resizeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("Calm 2D Water (PyQt6)")
    win.setGeometry(100, 100, 900, 420)

    widget = WaterWidget()
    win.setCentralWidget(widget)
    win.show()
    sys.exit(app.exec())