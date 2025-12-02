import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
import OpenGL.GL as gl

from . import gs_camera
from . import gs_util
from .renderer_ogl import OpenGLRenderer


class GaussianGLWidget(QOpenGLWidget):
    """Core OpenGL widget for Gaussian Splatting rendering."""
    
    def __init__(self, camera, parent=None):
        super().__init__(parent)
        self.camera = camera
        self.renderer = None
        self.gaussians = None
        self.scale_modifier = 1.0
        self.render_mode = 7
        self.auto_sort = False
        self.last_pos = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def initializeGL(self):
        gl.glClearColor(0, 0, 0, 1.0)
        self.renderer = OpenGLRenderer(self.camera.w, self.camera.h)
        
        self.renderer_list = [self.renderer]
        self.renderer_idx = 0
        
        self.gaussians = gs_util.naive_gaussian()
        self.update_renderer_state()

    def update_renderer_state(self):
        if self.renderer and self.gaussians:
            self.renderer.update_gaussian_data(self.gaussians)
            self.renderer.sort_and_update(self.camera)
            self.renderer.set_scale_modifier(self.scale_modifier)
            self.renderer.set_render_mod(self.render_mode - 3)
            self.renderer.update_camera_pose(self.camera)
            self.renderer.update_camera_intrin(self.camera)
            self.renderer.set_render_reso(self.camera.w, self.camera.h)

    def resizeGL(self, w, h):
        gl.glViewport(0, 0, w, h)
        self.camera.update_resolution(h, w)
        if self.renderer:
            self.renderer.set_render_reso(w, h)

    def paintGL(self):
        gl.glClearColor(0, 0, 0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        if self.camera.is_pose_dirty:
            self.renderer.update_camera_pose(self.camera)
            self.camera.is_pose_dirty = False
        
        if self.camera.is_intrin_dirty:
            self.renderer.update_camera_intrin(self.camera)
            self.camera.is_intrin_dirty = False
        
        if self.auto_sort:
            self.renderer.sort_and_update(self.camera)
        
        self.renderer.draw()

    def mousePressEvent(self, event):
        self.last_pos = event.position()
        if event.button() == Qt.MouseButton.LeftButton:
            self.camera.is_leftmouse_pressed = True
        elif event.button() == Qt.MouseButton.RightButton:
            self.camera.is_rightmouse_pressed = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.camera.is_leftmouse_pressed = False
        elif event.button() == Qt.MouseButton.RightButton:
            self.camera.is_rightmouse_pressed = False

    def mouseMoveEvent(self, event):
        pos = event.position()
        self.camera.process_mouse(pos.x(), pos.y())
        self.last_pos = pos
        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120
        self.camera.process_wheel(0, delta)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Q:
            self.camera.process_roll_key(1)
        elif event.key() == Qt.Key.Key_E:
            self.camera.process_roll_key(-1)
        self.update()

    def load_ply(self, file_path):
        """Load a Gaussian Splatting PLY file."""
        try:
            self.gaussians = gs_util.load_ply(file_path)
            self.renderer.update_gaussian_data(self.gaussians)
            self.renderer.sort_and_update(self.camera)
            self.update()
            return len(self.gaussians)
        except RuntimeError:
            return None

    def set_scale_modifier(self, val):
        self.scale_modifier = val
        if self.renderer:
            self.renderer.set_scale_modifier(val)
            self.update()

    def set_render_mode(self, mode):
        self.render_mode = mode
        if self.renderer:
            self.renderer.set_render_mod(mode - 4)
            self.update()

    def sort_gaussians(self):
        if self.renderer:
            self.renderer.sort_and_update(self.camera)
            self.update()


class GaussianSplattingWidget(QWidget):
    """
    Gaussian Splatting viewport widget.
    
    Use this as a drop-in widget in your PyQt6 application.
    Similar to ViewportWidget in ars_3d_engine.
    
    Example:
        from gs_viewer import GaussianSplattingWidget
        
        self.gs_viewport = GaussianSplattingWidget(parent=self)
        self.layout.addWidget(self.gs_viewport)
        
        # Load a PLY file
        self.gs_viewport.load_ply("path/to/file.ply")
    """
    
    def __init__(self, parent=None, width=1280, height=720):
        super().__init__(parent)
        
        # Camera
        self.camera = gs_camera.Camera(height, width)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # GL Widget
        self._gl_widget = GaussianGLWidget(self.camera, self)
        layout.addWidget(self._gl_widget)
        
        # Render timer for continuous updates
        self._render_timer = QTimer()
        self._render_timer.timeout.connect(self._gl_widget.update)
        self._render_timer.start(16)  # ~60fps
        
        # Settings
        self.auto_sort = False

    def load_ply(self, file_path: str) -> int | None:
        """
        Load a Gaussian Splatting PLY file.
        
        Args:
            file_path: Path to the .ply file
            
        Returns:
            Number of gaussians loaded, or None on failure
        """
        return self._gl_widget.load_ply(file_path)

    def set_scale(self, scale: float):
        """Set the gaussian scale modifier (0.1 to 10.0)."""
        self._gl_widget.set_scale_modifier(scale)

    def set_render_mode(self, mode: int):
        """
        Set render mode.
        
        Modes:
            0: Gaussian Ball
            1: Flat Ball
            2: Billboard
            3: Depth
            4: SH:0
            5: SH:0~1
            6: SH:0~2
            7: SH:0~3 (default)
        """
        self._gl_widget.set_render_mode(mode)

    def set_auto_sort(self, enabled: bool):
        """Enable/disable automatic gaussian sorting."""
        self._gl_widget.auto_sort = enabled
        self.auto_sort = enabled

    def sort_gaussians(self):
        """Manually sort gaussians by depth."""
        self._gl_widget.sort_gaussians()

    def set_fov(self, fov: float):
        """Set field of view in radians."""
        self.camera.fovy = fov
        self.camera.is_intrin_dirty = True

    def get_gaussian_count(self) -> int:
        """Get the number of loaded gaussians."""
        if self._gl_widget.gaussians:
            return len(self._gl_widget.gaussians)
        return 0
