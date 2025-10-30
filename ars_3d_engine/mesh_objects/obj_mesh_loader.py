import numpy as np
from vispy import scene
from vispy.io import read_mesh
from vispy.geometry import MeshData  
from ars_3d_engine.mesh_objects.scene_objects import CGeometry
 

class CMesh(CGeometry):

    @classmethod
    def create(cls, file_path: str, color=(102/255, 108/255, 120/255, 1.0), translate=(0.0, 0.0, 0.0), name="Mesh"):
        vertices, faces, normals, texcoords = read_mesh(file_path)  # Changed _ to texcoords
        md = MeshData(vertices=vertices, faces=faces)
        if normals is not None:
            md._vertex_normals = normals.astype(np.float32)
        if texcoords is not None:
            md._vertex_tex_coords = texcoords.astype(np.float32)  # Add this to set texcoords
        v = scene.visuals.Mesh(meshdata=md, color=color, shading=None)
        obj = cls(v, name=name)
        obj.set_position(translate[0], translate[1], translate[2])
        return obj
