from vispy import scene, app, gloo
from vispy.visuals import Visual
import numpy as np
import time
from .shaders import FRAGMENT_SHADER, VERTEX_SHADER


class GridVisual(Visual):
    """Shader-based grid visual."""
    def __init__(self, minor_step, major_step, visible_distance, fade_exponent, colors):
        super().__init__(vcode=VERTEX_SHADER, fcode=FRAGMENT_SHADER)

        # Initial positions (unit quad)
        self.positions = np.array([
            [-1, 0, -1], [-1, 0, 1], [1, 0, 1],
            [-1, 0, -1], [1, 0, 1], [1, 0, -1]
        ], dtype=np.float32)

        self._vertex_buffer = gloo.VertexBuffer(self.positions)
        
        self.shared_program['a_position'] = self._vertex_buffer
        
        self.shared_program['u_minor_step'] = minor_step
        self.shared_program['u_major_step'] = major_step
        self.shared_program['u_visible_distance'] = visible_distance
        self.shared_program['u_fade_exponent'] = fade_exponent
        
        self.shared_program['u_minor_color'] = colors['minor']
        self.shared_program['u_major_color'] = colors['major']
        self.shared_program['u_axis_x_color'] = colors['x']
        self.shared_program['u_axis_z_color'] = colors['z']
        
        self.shared_program['u_show_grid'] = True
        self.shared_program['u_show_x_axis'] = True
        self.shared_program['u_show_z_axis'] = True
        
        self.set_gl_state('translucent', blend=True, depth_test=True, cull_face=False)
        self._draw_mode = 'triangles'

    def _prepare_transforms(self, view):
        self.shared_program.vert['transform'] = view.get_transform()

    def _prepare_draw(self, view):
        if not hasattr(view, 'camera'):
            scale = 1000.0
        else:
            far_clip = view.camera.far or 1000.0
            scale = far_clip * 1.5
        scaled_positions = self.positions * np.array([scale, 1, scale], dtype=np.float32)
        self._vertex_buffer.set_data(scaled_positions)

# CRITICAL: Wrap for scene integration
GridVisual = scene.visuals.create_visual_node(GridVisual)

class InfiniteGrid(scene.visuals.Compound):
    def __init__(self, minor_step=10.0, subdivisions=5, visible_distance=200.0, fade_subdivisions=1, fade_exponent=1.0, show_y_axis=True, y_axis_length=100.0, parent=None):
        super().__init__([])
        self.unfreeze()

        self.max_visible_distance = visible_distance
        self.visible_distance = visible_distance
        self.fade_exponent = fade_exponent
        self.y_axis_length = y_axis_length

        colors = {
            'minor': (0.25, 0.25, 0.25, 0.9),
            'major': (0.4, 0.4, 0.4, 0.9),
            'x': (0.9, 0.3, 0.3, 1.0),
            'y': (0.3, 0.9, 0.3, 1.0),
            'z': (0.3, 0.5, 0.9, 1.0),
        }
        self.axis_y_color = np.array(colors['y'])
        
        self._grid_visual = GridVisual(
            minor_step=minor_step,
            major_step=minor_step * subdivisions,
            visible_distance=visible_distance,
            fade_exponent=fade_exponent,
            colors=colors
        )
        self.add_subvisual(self._grid_visual)

        self._y_axis_line = scene.visuals.Line(
            pos=np.array([[0.0, 0.0, 0.0], [0.0, self.y_axis_length, 0.0]]),
            color=self.axis_y_color,
            connect='segments',
            method='gl',
            width=2.2,
            antialias=False
        )

        if self._y_axis_line:
            self.add_subvisual(self._y_axis_line)

        self._cam_pos = None
        self._is_animating = False
        self._animation_start_time = None
        self._animation_duration = 2.0
        self._animation_timer = None
        
        self._grid_visible = True
        self._x_axis_visible = True
        self._y_axis_visible = True
        self._z_axis_visible = True
        
        self.freeze()

    def update_grid(self, cam_pos):
        now = time.time()
        
        if self._is_animating:
            elapsed = now - self._animation_start_time
            progress = min(elapsed / self._animation_duration, 1.0)
            self.visible_distance = (progress ** 2) * self.max_visible_distance
            if progress >= 1.0:
                self._is_animating = False
                if self._animation_timer:
                    self._animation_timer.stop()
                    self._animation_timer = None

        if self._is_animating or self._cam_pos is None or not np.allclose(cam_pos, self._cam_pos, rtol=1e-2, atol=1e-3):
            self._cam_pos = cam_pos
            
            program = self._grid_visual.shared_program
            program['u_cam_xz_pos'] = (cam_pos[0], cam_pos[2])
            program['u_visible_distance'] = self.visible_distance
            program['u_fade_exponent'] = self.fade_exponent
            
            if self._y_axis_line and self._y_axis_visible:
                cam_x, cam_y, cam_z = cam_pos
                half_dist = max(self.visible_distance, 0.1)
                origin_dist = np.sqrt(cam_x**2 + cam_y**2 + cam_z**2)
                top_dist = np.sqrt(cam_x**2 + (self.y_axis_length - cam_y)**2 + cam_z**2)
                
                alpha_origin = max(0.0, 1.0 - (origin_dist / half_dist) ** self.fade_exponent)
                alpha_top = max(0.0, 1.0 - (top_dist / half_dist) ** self.fade_exponent)
                
                colors_y = np.array([
                    list(self.axis_y_color[:3]) + [self.axis_y_color[3] * alpha_origin],
                    list(self.axis_y_color[:3]) + [self.axis_y_color[3] * alpha_top]
                ])
                self._y_axis_line.set_data(color=colors_y)
            elif self._y_axis_line:
                self._y_axis_line.visible = False
            
            if self.canvas:
                self.canvas.update()

    def start_animation(self, duration=2.0):
        self._animation_duration = duration
        self._animation_start_time = time.time()
        self.visible_distance = 0
        self._is_animating = True
        if self._animation_timer is None:
            self._animation_timer = app.Timer(1/60.0, connect=self._on_timer, start=True)

    def _on_timer(self, event):
        self.update_grid(self._cam_pos if self._cam_pos is not None else np.array([0, 10, 0]))

    def set_grid_visible(self, visible=None):
        self._grid_visible = not self._grid_visible if visible is None else bool(visible)
        self._grid_visual.shared_program['u_show_grid'] = self._grid_visible
        if self.canvas:
            self.canvas.update()

    def set_x_axis_visible(self, visible=None):
        self._x_axis_visible = not self._x_axis_visible if visible is None else bool(visible)
        self._grid_visual.shared_program['u_show_x_axis'] = self._x_axis_visible
        if self.canvas:
            self.canvas.update()

    def set_y_axis_visible(self, visible=None):
        self._y_axis_visible = not self._y_axis_visible if visible is None else bool(visible)
        if self._y_axis_line:
            self._y_axis_line.visible = self._y_axis_visible
        if self.canvas:
            self.canvas.update()

    def set_z_axis_visible(self, visible=None):
        self._z_axis_visible = not self._z_axis_visible if visible is None else bool(visible)
        self._grid_visual.shared_program['u_show_z_axis'] = self._z_axis_visible
        if self.canvas:
            self.canvas.update()

    def set_xyz_visible(self, visible=None):
        is_currently_visible = (self._x_axis_visible or
                                self._z_axis_visible or
                                (self._y_axis_line and self._y_axis_visible))
        target_visible = not is_currently_visible if visible is None else bool(visible)
        self.set_x_axis_visible(target_visible)
        self.set_y_axis_visible(target_visible)
        self.set_z_axis_visible(target_visible)

    def get_visibility_state(self):
        return {
            'grid': self._grid_visible,
            'x_axis': self._x_axis_visible,
            'y_axis': self._y_axis_visible,
            'z_axis': self._z_axis_visible
        }