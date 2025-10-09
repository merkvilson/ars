# bg.py
from vispy import scene
from vispy.io import imread
from vispy.gloo import clear as gloo_clear, Texture2D
from vispy.scene import Widget, Node
import numpy as np

from common.ars_debug import DEBUG_MODE as DBG


class Background(Widget):
    ClearDepth = type("ClearDepthBuffer", (Node,), {'draw': lambda self: gloo_clear(color=False, depth=True)})
    
    def __init__(self, image_path=None, *args, **kwargs):
        self._last = None
        self.bg_view = None
        self.bg_image = None
        super().__init__(*args, **kwargs)
        self.order = float("-inf")
        self._last = self.ClearDepth(parent=self)
        self._last.order = float("inf")
        assert self._children.pop() == self._last
        
        # Background view and camera
        self.bg_view = self.add_view(camera=scene.cameras.PanZoomCamera())
        
        # Load image only if image_path is provided
        if image_path:
            image_data = imread(image_path)[::-1, :, :]  # Flip vertically to correct orientation
            texture_format = 'rgba' if image_data.shape[-1] == 4 else 'rgb'
            texture = Texture2D(image_data, format=texture_format, wrapping='clamp_to_edge', interpolation='linear')
            texture.min_filter = 'linear_mipmap_linear'
            texture.mag_filter = 'linear'
            self.bg_image = scene.visuals.Image(data=image_data, texture=texture, parent=self.bg_view.scene)
            self._adjust_camera(image_data)
    
    @property
    def children(self):
        return super().children + [self._last] if self._last is not None else super().children
    
    def set_image(self, image_path):
        # Load new image data
        try:
            image_data = imread(image_path)[::-1, :, :]  # Flip vertically to correct orientation
        except Exception as e:
            if DBG: print(f"Error loading image {image_path}: {e}")
            return
        
        # Determine texture format based on number of channels
        texture_format = 'rgba' if image_data.shape[-1] == 4 else 'rgb'
        # Create a new texture
        texture = Texture2D(image_data, format=texture_format, wrapping='clamp_to_edge', interpolation='linear')
        texture.min_filter = 'linear_mipmap_linear'
        texture.mag_filter = 'linear'
        # Remove the old image visual if it exists
        if self.bg_image is not None:
            self.bg_image.parent = None  # Detach from scene
        # Create a new Image visual
        self.bg_image = scene.visuals.Image(data=image_data, texture=texture, parent=self.bg_view.scene)
        self._adjust_camera(image_data)
    
    def clear_image(self):
        # Remove the current image visual if it exists
        if self.bg_image is not None:
            self.bg_image.parent = None  # Detach from scene
            self.bg_image = None
    
    def _adjust_camera(self, image_data):
        # Get image dimensions
        height, width = image_data.shape[:2]
        
        # Center the camera on the image
        self.bg_view.camera.center = (width / 2, height / 2)
        
        # Calculate the aspect ratio of the image and the viewport
        viewport_size = self.canvas.size if hasattr(self, 'canvas') and self.canvas is not None else (800, 600)
        viewport_aspect = viewport_size[0] / viewport_size[1]
        image_aspect = width / height
        
        # Adjust the camera zoom to fit the image to the viewport
        if image_aspect > viewport_aspect:
            # Image is wider than viewport: fit to width
            zoom = width / viewport_size[0]
        else:
            # Image is taller than viewport: fit to height
            zoom = height / viewport_size[1]
        
        # Set the camera range to fit the image
        self.bg_view.camera.set_range(
            x=(0, width),
            y=(0, height),
            margin=0
        )
        
        # Adjust zoom to ensure the image fills the viewport while preserving aspect ratio
        self.bg_view.camera.zoom = 1.0 / zoom
        self.bg_view.camera.update()