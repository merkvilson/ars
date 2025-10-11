from abc import ABC, abstractmethod
import inspect
import numpy as np
from vispy import scene
from vispy.scene import transforms
from vispy.visuals.transforms import NullTransform
from vispy.io import read_mesh
from vispy.visuals.filters import ShadingFilter

DEFAULT_OBJ_COLOR = (102/255, 108/255, 120/255, 1.0)

class IObject3D(ABC):

    def __init__(self, visual, name="Object"):

        self._visual = visual
        
        # If the visual has the default NullTransform, replace it with a MatrixTransform.
        if isinstance(self._visual.transform, NullTransform):
            self._visual.transform = transforms.MatrixTransform()

        # A parent node that will only handle translation
        self._node = scene.Node()
        self._node.transform = transforms.MatrixTransform()
        self._visual.parent = self._node

        self._name = name
        self._parent = None
        self._children = []

        # Attach shading filter for directional light
        self.shading_filter = None
        if hasattr(self._visual, 'mesh_data') and self._visual.mesh_data is not None:
            self.shading_filter = ShadingFilter(shading='smooth', shininess=50, light_dir=(0, -1, -1))
            #self.shading_filter.ambient_light = (0.2, 0.2, 0.2)
            self._visual.attach(self.shading_filter)
            self._visual.update()

        self._update_gl_state()

    def update_light_dir(self, light_dir):
        """Update the light direction for the shading filter (in view space)."""
        if self.shading_filter is not None:
            self.shading_filter.light_dir = np.array(light_dir, dtype=float)

    def set_shading(self, shading_type: str) -> None:
        """Set the shading type for the visual. Valid options: None, 'flat', 'smooth'."""
        if self.shading_filter is None:
            if shading_type is None:
                return  # No shading filter exists, and None requested
            else:
                # Create and attach shading filter if it doesn't exist and shading is requested
                if hasattr(self._visual, 'mesh_data') and self._visual.mesh_data is not None:
                    self.shading_filter = ShadingFilter(shading=shading_type, shininess=50, light_dir=(0, -1, -1))
                    self._visual.attach(self.shading_filter)
                    self._visual.update()
                else:
                    return  # Cannot apply shading without mesh_data
        self.shading_filter.shading = shading_type
        self._visual.update()

    def get_shading(self) -> str:
        """Get the current shading type. Returns None if no shading filter is attached."""
        if self.shading_filter is None:
            return None
        return self.shading_filter.shading

    @property
    def visual(self):
        """The top-level node for the object (handles translation)."""
        return self._node

    @property
    def rotation_visual(self):
        """The visual that holds the rotation and scale transform."""
        return self._visual

    def position(self) -> np.ndarray:
        # Map the local origin [0,0,0] into world coordinates
        return self._node.transform.map([0, 0, 0])[:3]
    """
    # homogeneous version (handles 4D coords / perspective parents)
    def position(self) -> np.ndarray:
        p = self._node.transform.map([0.0, 0.0, 0.0, 1.0])
        p = np.asarray(p, dtype=float)
        if p.size == 4 and abs(p[3]) > 1e-12:
            return (p[:3] / p[3]).copy()
        return p[:3].copy()
    """

    def set_position(self, x: float, y: float, z: float) -> None:
        tr = transforms.MatrixTransform()
        tr.translate((float(x), float(y), float(z)))
        self._node.transform = tr

    def set_color(self, color: tuple) -> None:
        """Set the color of the visual. Color should be a tuple (r, g, b) or (r, g, b, a) with values 0-1."""
        if hasattr(self._visual, 'color'):
            self._visual.color = color
        self._update_gl_state()

    def set_scale(self, scale: tuple) -> None:
        """Set the scale of the object. Scale can be a single float or tuple (sx, sy, sz)."""
        if isinstance(scale, (int, float)):
            scale = (scale, scale, scale)
        
        current_matrix = self._visual.transform.matrix.copy()
        
        # Get the current rotation by normalizing the basis vectors
        sx_old = np.linalg.norm(current_matrix[0, :3])
        sy_old = np.linalg.norm(current_matrix[1, :3])
        sz_old = np.linalg.norm(current_matrix[2, :3])
        
        if sx_old < 1e-8: sx_old = 1e-8
        if sy_old < 1e-8: sy_old = 1e-8
        if sz_old < 1e-8: sz_old = 1e-8
        
        # Extract pure rotation
        rot_matrix = current_matrix[:3, :3].copy()
        rot_matrix[0, :] /= sx_old
        rot_matrix[1, :] /= sy_old
        rot_matrix[2, :] /= sz_old
        
        # Apply new scale
        S = np.eye(4, dtype=float)
        S[0, 0] = scale[0]
        S[1, 1] = scale[1]
        S[2, 2] = scale[2]
        
        R = np.eye(4, dtype=float)
        R[:3, :3] = rot_matrix
        
        new_matrix = (S @ R).astype(np.float32)
        self._visual.transform.matrix = new_matrix

    def set_alpha(self, alpha: float) -> None:
        """Set the alpha (transparency) value. Alpha should be a value 0-1."""
        current_color = self.get_color()
        new_color = (current_color[0], current_color[1], current_color[2], alpha)
        self.set_color(new_color)

    def get_color(self) -> tuple:
        """Get the current color of the visual. Returns a tuple (r, g, b, a) with values 0-1."""
        color = self._visual.color
        return tuple(color.rgba)

    def get_alpha(self) -> float:
        """Get the current alpha (transparency) value. Returns a value 0-1."""
        return self.get_color()[3]

    def _update_gl_state(self):
        alpha = self.get_alpha()
        if alpha < 1.0:
            self._visual.set_gl_state(preset='translucent', cull_face=True)
        else:
            self._visual.set_gl_state(preset='opaque')

    #Don't remove
    #Don't remove
    #Don't remove
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    def set_parent(self, parent):
        if self._parent == parent:
            return
        if self._parent:
            self._parent._children.remove(self)
        self._parent = parent
        if parent:
            parent._children.append(self)

class CMesh(IObject3D):

    @classmethod
    def create(cls,file_path: str,color=DEFAULT_OBJ_COLOR,translate=(0.0, 0.0, 0.0),name="Mesh"):
        vertices, faces, normals, _ = read_mesh(file_path)
        v = scene.visuals.Mesh(vertices=vertices, faces=faces, color=color, shading=None)
        obj = cls(v, name=name)
        obj.set_position(translate[0], translate[1], translate[2])
        return obj