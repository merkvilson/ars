import os
import cv2
import numpy as np
from vispy.io import write_png
from vispy.gloo import gl
from prefs.pref_controller import get_path

def pre_proc(self):
    # Disable picking filters to ensure normal rendering
    self._objectManager.picking()._set_enabled(False)

    # Temporarily hide for clean render
    original_grid_visible = self.grid.visible
    original_gizmo_visible = self.gizmo_node.visible
    self.grid.visible = False
    self.gizmo_node.visible = False

    # Force a full render (without crop)
    self._canvas.render()

    # Restore visibility
    self.grid.visible = original_grid_visible
    self.gizmo_node.visible = original_gizmo_visible

    # Force scene update if needed
    self._canvas.update()
    
    ps = float(self._canvas.pixel_scale or 1.0)
    w, h = int(self._canvas.size[0] * ps), int(self._canvas.size[1] * ps)

    return w, h

def post_proc(x, y, render_pass):
    # Resize and crop to target dimensions (x, y)
    scale_x = x / render_pass.shape[1]  # target_width / current_width
    scale_y = y / render_pass.shape[0]  # target_height / current_height
    scale = max(scale_x, scale_y)  # Use max to ensure we cover the target size (fit shortest axis)
    new_w = round(render_pass.shape[1] * scale)
    new_h = round(render_pass.shape[0] * scale)
    resized = cv2.resize(render_pass, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    start_y = (new_h - y) // 2
    start_x = (new_w - x) // 2
    cropped = resized[start_y:start_y + y, start_x:start_x + x]

    return cropped


def save_depth(self, filename: str = 'depth.png', x: int = 512, y: int = 512) -> None:

    w, h = pre_proc(self)

    # Read buffer
    raw_pass = gl.glReadPixels(0, 0, w, h, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT)
    render_pass = np.flipud(np.frombuffer(raw_pass, np.float32).reshape((h, w)))
    
    min_d, max_d = np.nanmin(render_pass), np.nanmax(render_pass) # Normalize to [0, 1]
    if max_d > min_d: render_pass = (render_pass - min_d) / (max_d - min_d)
    else: render_pass = np.zeros_like(render_pass)
    render_pass = 1 - render_pass #Invert for better visibility (closer = lighter)
    render_pass = (render_pass * 255).astype(np.uint8) # Map to uint8 grayscale

    cropped = post_proc(x, y, render_pass)
    cropped = np.repeat(cropped[..., np.newaxis], 3, axis=2) # Convert to RGB for PNG (repeat channels)
    write_png(os.path.join(os.path.join(get_path('input'), filename)), cropped)


def save_render(self, filename: str = 'render.png', x: int = 512, y: int = 512) -> None:

    w, h = pre_proc(self)

    # Read buffer
    raw_pass = gl.glReadPixels(0, 0, w, h, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
    render_pass = np.flipud(np.frombuffer(raw_pass, np.uint8).reshape((h, w, 4)))[:, :, :3]
        
    cropped = post_proc(x, y, render_pass)

    write_png(os.path.join(os.path.join(get_path('input'), filename)), cropped)