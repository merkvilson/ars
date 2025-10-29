from vispy import scene

class ArsOrbitCamera(scene.cameras.TurntableCamera):
    def __init__(self, *args, fly_bounds=None, **kwargs):
        self.update_callback = None
        self.fly_bounds = fly_bounds

        self._locked = False
        self._prev_interactive = True
        super().__init__(*args, **kwargs)

    def view_changed(self):
        # Wrap the camera center for x and z, clamp for y if fly_bounds are defined
        if hasattr(self, "fly_bounds") and self.fly_bounds is not None and self.center is not None:
            x_min, x_max = self.fly_bounds[0]
            y_min, y_max = self.fly_bounds[1]
            z_min, z_max = self.fly_bounds[2]

            cx, cy, cz = self.center

            x_width = x_max - x_min
            cx = x_min + ((cx - x_min) % x_width) # Wrap x

            z_width = z_max - z_min
            cz = z_min + ((cz - z_min) % z_width) # Wrap z

            cy = max(y_min, min(cy, y_max)) # Clamp y

            self._center = (cx, cy, cz)

        super().view_changed()

        if self.update_callback is not None:
            self.update_callback()

    def set_locked(self, locked: bool):
        if locked == self._locked: return
        self._locked = locked
        if locked:
            self._prev_interactive = self.interactive
            self.interactive = False
        else: self.interactive = self._prev_interactive

    def is_locked(self) -> bool:
        return self._locked

    def viewbox_key_event(self, event):
        if self._locked:
            event.handled = True
            return
        super().viewbox_key_event(event)

    def viewbox_mouse_event(self, event):
        if self._locked:
            event.handled = True
            return

        if event.type == 'mouse_wheel':
            event.handled = True
            return

        super().viewbox_mouse_event(event)
