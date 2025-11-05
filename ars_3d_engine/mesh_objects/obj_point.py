import numpy as np
from vispy import scene
from ars_3d_engine.mesh_objects.scene_objects import CGeometry
 

class CPoint(CGeometry):

    @classmethod
    def create(cls, position=(0.0, 0.0, 0.0), color=(1.0, 1.0, 1.0, .5), size=50.0, name="Point"):
        """
        Create a single point in 3D space.
        
        Args:
            position: Tuple (x, y, z) for the point position
            color: Tuple (r, g, b, a) with values 0-1
            size: Size of the point in pixels
            name: Name of the point object
        """
        # Ensure color is a tuple with 4 components
        if len(color) == 3:
            color = (*color, 1.0)
        
        # Create a Markers visual with a single point
        v = scene.visuals.Markers()
        v.set_data(
            pos=np.array([position], dtype=np.float32),
            face_color=np.array([color], dtype=np.float32),
            size=size,
            edge_width=0
        )
        
        obj = cls(v, name=name)
        obj._point_size = size
        obj._point_color = tuple(color)  # Ensure it's a tuple, not a VisPy Color object
        obj.set_position(position[0], position[1], position[2])
        return obj
    
    def get_color(self) -> tuple:
        """Get the current color of the point. Returns a tuple (r, g, b, a) with values 0-1."""
        color = getattr(self, '_point_color', (1.0, 1.0, 1.0, 1.0))
        # Ensure we always return a tuple, not a VisPy Color object
        if not isinstance(color, tuple):
            if hasattr(color, 'rgba'):
                return tuple(color.rgba)
            elif hasattr(color, '__iter__'):
                return tuple(color)
        return color
    
    def set_color(self, color: tuple) -> None:
        """Set the color of the point. Color should be a tuple (r, g, b) or (r, g, b, a) with values 0-1."""
        # Convert VisPy Color objects to tuples
        if hasattr(color, 'rgba'):
            color = tuple(color.rgba)
        elif not isinstance(color, tuple):
            color = tuple(color)
        
        # Ensure color has 4 components (rgba)
        if len(color) == 3:
            color = (*color, 1.0)
        
        self._point_color = color
        
        if hasattr(self._visual, 'set_data'):
            current_pos = self._visual._data['a_position']
            self._visual.set_data(
                pos=current_pos,
                face_color=np.array([color], dtype=np.float32),
                size=self._point_size,
                edge_width=0
            )
        self._update_gl_state()
    
    def set_point_size(self, size: float) -> None:
        """Set the size of the point in pixels."""
        self._point_size = size
        if hasattr(self._visual, 'set_data'):
            current_pos = self._visual._data['a_position']
            self._visual.set_data(
                pos=current_pos,
                face_color=np.array([self._point_color], dtype=np.float32),
                size=size,
                edge_width=0
            )
    
    def get_point_size(self) -> float:
        """Get the current size of the point."""
        return getattr(self, '_point_size', 10.0)
    