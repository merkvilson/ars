import numpy as np
from vispy import scene

from ars_3d_engine.mesh_objects.scene_objects import CGeometry
import pyvista as pv
from vispy.geometry import MeshData


class CText3D(CGeometry):
    def __init__(self, visual, name="Text3D", text="text", depth=0.5, angle=30.0):
        super().__init__(visual, name)
        self._text = text
        self._depth = depth
        self._angle = angle

    @classmethod
    def create(cls, text="text", depth=0.5, color=(102/255, 108/255, 120/255, 1.0), translate=(0.0, 0.0, 0.0), name="Text3D", angle=30.0):
        md = CText3D._generate_mesh_data_with_breaking_angle(text, depth, angle)
        v = scene.visuals.Mesh(meshdata=md, color=color, shading=None)
        
        obj = cls(v, name=name, text=text, depth=depth, angle=angle)
        obj.set_position(*translate)
        return obj

    @staticmethod
    def _generate_mesh_data_with_breaking_angle(text, depth, angle):
        if not text:
            return MeshData()

        # 1. Generate base mesh
        pv_mesh = pv.Text3D(text, depth=depth).triangulate()

        # 2. Compute normals, splitting vertices at sharp edges
        pv_mesh.compute_normals(
            cell_normals=False,
            point_normals=True,
            split_vertices=True,
            feature_angle=angle,
            inplace=True,
        )

        # 4. Extract data for VisPy
        vertices = pv_mesh.points.astype(np.float32)
        faces = pv_mesh.faces.reshape(-1, 4)[:, 1:].astype(np.uint32)
        normals = pv_mesh.point_normals.astype(np.float32)

        # 5. Create final MeshData
        md = MeshData(vertices=vertices, faces=faces)
        if normals.shape[0] > 0:
            md._vertex_normals = normals
            
        return md

    def set_text(self, text: str) -> None:
        self._text = text
        md = CText3D._generate_mesh_data_with_breaking_angle(self._text, self._depth, self._angle)
        self._visual.set_data(meshdata=md)
        self._visual.update()

    def get_text(self) -> str:
        return self._text
    