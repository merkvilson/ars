import time
from PyQt6 import QtCore


class PickPulseAnimator(QtCore.QObject):
    def __init__(self, *, canvas, parent=None):
        super().__init__(parent)
        self._canvas = canvas

    def play(self, obj, *, duration_s: float = 0.5, scale_boost: float = 0.10, color_boost: float = 0.50) -> None:
        """Quickly pulse scale (+10%) and brighten color, then ease back."""

        def clamp01(v: float) -> float:
            return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)

        def ease_out_cubic(t: float) -> float:
            return 1.0 - (1.0 - t) ** 3

        # Stop any existing pulse on this object
        existing = getattr(obj, "_pick_pulse_timer", None)
        try:
            if existing is not None:
                existing.stop()
        except Exception:
            pass

        try:
            base_scale = obj.get_scale()
            base_color = obj.get_color()  # (r, g, b, a)
        except Exception:
            return

        duration_s = float(duration_s)
        start = time.perf_counter()

        grow_s = min(0.12, max(0.0, duration_s * 0.25))
        rest_s = max(1e-6, duration_s - grow_s)

        timer = QtCore.QTimer(self)
        timer.setInterval(16)
        obj._pick_pulse_timer = timer  # keep alive

        def tick():
            elapsed = time.perf_counter() - start
            if elapsed >= duration_s:
                timer.stop()
                try:
                    obj.set_scale(base_scale)
                    obj.set_color(base_color)
                except Exception:
                    pass
                try:
                    delattr(obj, "_pick_pulse_timer")
                except Exception:
                    pass
                self._canvas.update()
                return

            if elapsed <= grow_s and grow_s > 1e-9:
                u = elapsed / grow_s
                k = ease_out_cubic(u)
            else:
                u = (elapsed - grow_s) / rest_s
                u = 0.0 if u < 0.0 else (1.0 if u > 1.0 else u)
                k = 1.0 - ease_out_cubic(u)

            scale_factor = 1.0 + scale_boost * k
            bright_factor = 1.0 + color_boost * k

            try:
                obj.set_scale((base_scale[0] * scale_factor, base_scale[1] * scale_factor, base_scale[2] * scale_factor))
                r, g, b, a = base_color
                a2 = a if a >= 1.0 else clamp01(a * bright_factor)
                obj.set_color((clamp01(r * bright_factor), clamp01(g * bright_factor), clamp01(b * bright_factor), a2))
            except Exception:
                timer.stop()
                return

            self._canvas.update()

        timer.timeout.connect(tick)
        timer.start()