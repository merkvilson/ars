import numpy as np
from vispy.io import write_png
from vispy.gloo import gl
import cv2  # For Canny edge detection and resizing
from prefs.pref_controller import get_path
import os

def save_depth(self, filename: str = 'depth.png', invert: bool = True, x: int = 512, y: int = 512) -> None:

    path = os.path.join(os.path.join(get_path('input'), filename))

    # Disable picking filters to ensure normal rendering
    picking = self._objectManager.picking()
    picking._set_enabled(False)
    
    # Temporarily hide the grid for clean render (restore after)
    original_grid_visible = self.grid.visible
    original_gizmo_visible = self.gizmo_node.visible
    self.grid.visible = False
    self.gizmo_node.visible = False
    
    # Force a full render to populate the depth buffer (without crop)
    self._canvas.render()
    
    # Restore grid visibility
    self.grid.visible = original_grid_visible
    self.gizmo_node.visible = original_gizmo_visible
    
    # Force scene update if needed
    self._canvas.update()
    
    ps = float(self._canvas.pixel_scale or 1.0)
    w, h = int(self._canvas.size[0] * ps), int(self._canvas.size[1] * ps)
    # Read raw depth buffer (bottom-up, flip later)
    raw_depth = gl.glReadPixels(0, 0, w, h, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT)
    depth = np.frombuffer(raw_depth, np.float32).reshape((h, w))
    depth = np.flipud(depth)  # Flip to top-down for image
    
    # Normalize to [0, 1] based on scene min/max (handles empty areas as NaN/inf)
    min_d, max_d = np.nanmin(depth), np.nanmax(depth)
    if max_d > min_d:
        norm_depth = (depth - min_d) / (max_d - min_d)
    else:
        norm_depth = np.zeros_like(depth)
    if invert:
        norm_depth = 1 - norm_depth
    # Map to uint8 grayscale
    norm_depth = (norm_depth * 255).astype(np.uint8)
    
    # Resize and crop to target dimensions (x, y)
    # Calculate scale factor based on minimum dimension ratio
    scale_x = x / norm_depth.shape[1]  # target_width / current_width
    scale_y = y / norm_depth.shape[0]  # target_height / current_height
    scale = max(scale_x, scale_y)  # Use max to ensure we cover the target size (fit shortest axis)
    
    # Calculate new dimensions after scaling
    new_w = round(norm_depth.shape[1] * scale)
    new_h = round(norm_depth.shape[0] * scale)
    
    # Resize the image
    resized = cv2.resize(norm_depth, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    # Center crop to exact target size
    start_y = (new_h - y) // 2
    start_x = (new_w - x) // 2
    cropped = resized[start_y:start_y + y, start_x:start_x + x]
    
    # Convert to RGB for PNG (repeat channels)
    img = np.repeat(cropped[..., np.newaxis], 3, axis=2)
    write_png(path, img)

def save_render(self, filename: str = 'render.png', x: int = 512, y: int = 512) -> None:

    path = os.path.join(os.path.join(get_path('input'), filename))

    # Disable picking filters to ensure normal rendering
    picking = self._objectManager.picking()
    picking._set_enabled(False)
    
    # Temporarily hide for clean render
    original_grid_visible = self.grid.visible
    original_gizmo_visible = self.gizmo_node.visible
    self.grid.visible = False
    self.gizmo_node.visible = False
    
    # Force a full render to populate the color buffer
    self._canvas.render()
    
    # Restore visibility
    self.grid.visible = original_grid_visible
    self.gizmo_node.visible = original_gizmo_visible

    
    # Force scene update if needed
    self._canvas.update()
    
    ps = float(self._canvas.pixel_scale or 1.0)
    w, h = int(self._canvas.size[0] * ps), int(self._canvas.size[1] * ps)
    
    # Read color buffer (RGBA)
    raw_rgba = gl.glReadPixels(0, 0, w, h, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
    rgba = np.frombuffer(raw_rgba, np.uint8).reshape((h, w, 4))
    rgba = np.flipud(rgba)  # Flip to top-down for image
    
    # Convert RGBA to RGB (drop alpha channel)
    rgb = rgba[:, :, :3]
    
    # Resize and crop to target dimensions (x, y)
    # Calculate scale factor based on minimum dimension ratio
    scale_x = x / rgb.shape[1]  # target_width / current_width
    scale_y = y / rgb.shape[0]  # target_height / current_height
    scale = max(scale_x, scale_y)  # Use max to ensure we cover the target size (fit shortest axis)
    
    # Calculate new dimensions after scaling
    new_w = round(rgb.shape[1] * scale)
    new_h = round(rgb.shape[0] * scale)
    
    # Resize the image
    resized = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    # Center crop to exact target size
    start_y = (new_h - y) // 2
    start_x = (new_w - x) // 2
    cropped = resized[start_y:start_y + y, start_x:start_x + x]
    
    write_png(path, cropped)