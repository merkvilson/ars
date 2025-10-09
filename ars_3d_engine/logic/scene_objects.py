from abc import ABC, abstractmethod
import inspect
import numpy as np
from vispy import scene
from vispy.scene import transforms
from vispy.visuals.transforms import NullTransform
from vispy.io import read_mesh
from vispy.visuals.filters import ShadingFilter

DEFAULT_OBJ_COLOR = (75/255, 85/255, 95/255, 1.0)
DEFAULT_OBJ_COLOR = (102/255, 108/255, 120/255, 1.0)

class IObject3D(ABC):

    def __init__(self, visual, name="Object"):

        self._rotation_visual = visual
        
        # If the visual has the default NullTransform, replace it with a MatrixTransform.
        if isinstance(self._rotation_visual.transform, NullTransform):
            self._rotation_visual.transform = transforms.MatrixTransform()

        # A parent node that will only handle translation
        self._node = scene.Node()
        self._node.transform = transforms.MatrixTransform()
        self._rotation_visual.parent = self._node

        self._name = name
        self._parent = None
        self._children = []

        # Attach shading filter for directional light
        self.shading_filter = None
        if hasattr(self._rotation_visual, 'mesh_data') and self._rotation_visual.mesh_data is not None:
            self.shading_filter = ShadingFilter(shading='phong', shininess=50, light_dir=(0, -1, -1))
            #self.shading_filter.ambient_light = (0.2, 0.2, 0.2)
            self._rotation_visual.attach(self.shading_filter)


    def update_light_dir(self, light_dir):
        """Update the light direction for the shading filter (in view space)."""
        if self.shading_filter is not None:
            self.shading_filter.light_dir = np.array(light_dir, dtype=float)

    @property
    def visual(self):
        """The top-level node for the object (handles translation)."""
        return self._node

    @property
    def rotation_visual(self):
        """The visual that holds the rotation and scale transform."""
        return self._rotation_visual

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