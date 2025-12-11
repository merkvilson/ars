import vispy
import numpy as np
import time
from vispy.util.quaternion import Quaternion
from vispy.app import Timer

class ArsFlyCamera(vispy.scene.cameras.FlyCamera):
    def __init__(self, *args, fly_bounds=None, **kwargs):
        self.update_callback = None
        self.fly_bounds = fly_bounds

        self._locked = False
        self._prev_interactive = True
        super().__init__(*args, **kwargs)

        for k in "Down,Up,Left,Right,Space,I,J,K,L,F,C,Q,E,Backspace".split(","):
            if k in self._keymap:
                del self._keymap[k]

        self._keymap['Space'] = (+1, 3)
        self._keymap['F'] = (-1, 3)

        # Custom Backspace reset
        self._reset_center = (6, 3, 6)
        self._reset_rotation1 = Quaternion.create_from_axis_angle(np.deg2rad(-45), 0, 1, 0)
        self._reset_rotation2 = Quaternion.create_from_axis_angle(np.deg2rad(20), 1, 0, 0)


    def _slerp(self, q1, q2, t):
        v1 = np.array([q1.w, q1.x, q1.y, q1.z])
        v2 = np.array([q2.w, q2.x, q2.y, q2.z])
        
        dot = np.dot(v1, v2)
        
        if dot < 0.0:
            v2 = -v2
            dot = -dot
            
        dot = np.clip(dot, -1.0, 1.0)
        
        theta_0 = np.arccos(dot)
        sin_theta_0 = np.sin(theta_0)
        
        if sin_theta_0 < 1e-6:
            v = (1.0 - t) * v1 + t * v2
            v /= np.linalg.norm(v)
        else:
            theta = theta_0 * t
            sin_theta = np.sin(theta)
            
            s0 = np.cos(theta) - dot * sin_theta / sin_theta_0
            s1 = sin_theta / sin_theta_0
            
            v = s0 * v1 + s1 * v2
            
        return Quaternion(v[0], v[1], v[2], v[3])

    def move_to(self, center = None, offset=1.0, animate=False, rotation=None):
        if not center:
            center = self.center

        if rotation is None:
            target_rotation = (self.rotation1, self.rotation2)
            calc_rotation = self.rotation
        else:
            target_rotation = rotation
            # Combine rotations: rotation2 * rotation1
            calc_rotation = target_rotation[1] * target_rotation[0]

        # Get the inverse rotation (Camera -> World)
        # FlyCamera.rotation stores World->Camera transform (View Matrix rotation)
        # So we need inverse to transform local Camera vectors to World vectors.
        inv_rot = calc_rotation.inverse()
        
        # In Camera space, Back is +Z (0, 0, 1) because Camera looks down -Z
        back_vector = inv_rot.rotate_point([0, 0, 1])
        back_vector = np.array(back_vector)
        
        # Normalize
        norm = np.linalg.norm(back_vector)
        if norm > 0:
            back_vector /= norm
            
        # Calculate target center
        # If center (object position) is provided, we move relative to it.
        # If not, we move relative to current camera position.
        base_point = np.array(center)
        target_center = base_point + back_vector * offset

        if not animate:
            self.center = tuple(target_center)
            self.rotation1 = target_rotation[0]
            self.rotation2 = target_rotation[1]
            self.view_changed()
        else:
            # Animate from CURRENT camera position to the target position
            self._anim_start_center = np.array(self.center)
            self._anim_target_center = target_center
            
            self._anim_start_rotation = (self.rotation1, self.rotation2)
            self._anim_target_rotation = target_rotation

            self._anim_duration = 0.5
            self._anim_start_time = time.time()
            
            if hasattr(self, '_anim_timer'):
                self._anim_timer.stop()
            
            self._anim_timer = Timer(interval=0.016, connect=self._on_anim_update, start=True)

    def _on_anim_update(self, event):
        elapsed = time.time() - self._anim_start_time
        t = elapsed / self._anim_duration
        
        if t >= 1.0:
            t = 1.0
            self._anim_timer.stop()
            
        # Ease out cubic for smoother movement
        t_ease = 1 - (1 - t) ** 3
        
        # Interpolate Center
        self.center = (1 - t_ease) * self._anim_start_center + t_ease * self._anim_target_center
        
        # Interpolate Rotation
        if hasattr(self, '_anim_start_rotation') and hasattr(self, '_anim_target_rotation'):
             r1_start, r2_start = self._anim_start_rotation
             r1_target, r2_target = self._anim_target_rotation
             
             self.rotation1 = self._slerp(r1_start, r1_target, t_ease)
             self.rotation2 = self._slerp(r2_start, r2_target, t_ease)
        
        self.view_changed()


    def reset(self):
        self.center = self._reset_center
        self.rotation1 = self._reset_rotation1
        self.rotation2 = self._reset_rotation2
        self.view_changed()


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


    def on_timer(self, event):
        # Call the parent's on_timer to handle standard updates
        super().on_timer(event)
        
        # Override the damping logic with stronger reduction (less inertia)
        reduce = np.array([0.1, 0.1, 0.1, 0.2, 0.2, 0.2])  # Increased values for faster slowdown
        reduce[self._brake > 0] = 0.4  # Even stronger when braking
        
        self._speed -= self._speed * reduce
        if np.abs(self._speed).max() < 0.05:
            self._speed *= 0.0
        
        self.view_changed()


    def viewbox_key_event(self, event):
        if self._locked:
            event.handled = True
            return
        
        if event.key is not None and event.key.name == 'Backspace':
            if event.type == 'key_press':
                self.reset()
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