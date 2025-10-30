import numpy as np
from vispy import scene

from ars_3d_engine.mesh_objects.scene_objects import CGeometry
import pyvista as pv
from vispy.geometry import MeshData


class CPrimitive(CGeometry):
    def __init__(self, visual, name="CPrimitive", **params):
        super().__init__(visual, name)
        
        # Store primitive parameters
        self.primitive_type = params.get('primitive_type', 'sphere')
        self.radius = params.get('radius', 1.0)
        self.width = params.get('width', 2.0)
        self.height = params.get('height', 2.0)
        self.depth = params.get('depth', 2.0)
        self.resolution = params.get('resolution', 30)
        self.direction = params.get('direction', (0, 1, 0))


    @classmethod
    def create(cls, primitive_type='sphere', color=(102/255, 108/255, 120/255, 1.0), 
               translate=(0.0, 0.0, 0.0), **params):
        """
        Create a parametric primitive mesh.
        
        Args:
            primitive_type: Type of primitive ('sphere', 'cube', 'plane', 'cylinder', 'cone', 'disc', 'pyramid')
            color: RGBA color tuple
            translate: Position tuple (x, y, z)
            **params: Additional parameters like radius, width, height, depth, resolution, direction
        """
        md = cls._generate_mesh(primitive_type, **params)
        v = scene.visuals.Mesh(meshdata=md, color=color, shading=None)
        
        obj = cls(v, primitive_type=primitive_type, **params)
        obj.set_position(*translate)
        return obj

    def set_primitive_type(self, primitive_type, **params):
        """
        Dynamically switch the primitive type and regenerate the mesh.
        
        Args:
            primitive_type: New primitive type ('sphere', 'cube', 'plane', 'cylinder', 'cone', 'disc', 'pyramid')
            **params: Optional new parameters (radius, width, height, depth, resolution, direction)
                     If not provided, will use existing stored parameters
        """
        # Update primitive type
        self.primitive_type = primitive_type
        
        # Update parameters if provided, otherwise keep existing ones
        if 'radius' in params:
            self.radius = params['radius']
        if 'width' in params:
            self.width = params['width']
        if 'height' in params:
            self.height = params['height']
        if 'depth' in params:
            self.depth = params['depth']
        if 'resolution' in params:
            self.resolution = params['resolution']
        if 'direction' in params:
            self.direction = params['direction']
        
        # Prepare parameters dict for mesh generation
        mesh_params = {
            'radius': self.radius,
            'width': self.width,
            'height': self.height,
            'depth': self.depth,
            'resolution': self.resolution,
            'direction': self.direction
        }
        
        # Regenerate mesh with new type
        md = self._generate_mesh(primitive_type, **mesh_params)
        
        # Update the visual's mesh data using set_data method
        # Note: self._visual is the actual Mesh object, self.visual is the Node wrapper
        self._visual.set_data(meshdata=md)
        
        print(f"Switched primitive to {primitive_type}")

    @staticmethod
    def _generate_mesh(primitive_type='sphere', **params):
        """
        Generate mesh data based on primitive type and parameters.
        
        Args:
            primitive_type: Type of primitive to generate
            **params: radius, width, height, depth, resolution, etc.
        """
        # Extract common parameters with defaults
        radius = params.get('radius', 1.0)
        width = params.get('width', 2.0)
        height = params.get('height', 2.0)
        depth = params.get('depth', 2.0)
        resolution = params.get('resolution', 30)
        direction = params.get('direction', (0, 1, 0))
        
        # Generate PyVista mesh based on type
        if primitive_type == 'sphere':
            pv_mesh = pv.Sphere(radius=radius, theta_resolution=resolution, phi_resolution=resolution)
            pv_mesh = pv.Sphere(
                
            radius = 1,
            center = (0.0, 0.0, 0.0),
            direction = (0.0, 0.0, 1.0),
            theta_resolution = 30,
            phi_resolution = 30,
            start_theta = 0.0,
            end_theta = 360.0,
            start_phi = 0.0,
            end_phi = 180.0,

            )


        elif primitive_type == 'cube':
            pv_mesh = pv.Cube(center=(0, 0, 0), x_length=width, y_length=height, z_length=depth)
        elif primitive_type == 'plane':
            pv_mesh = pv.Plane(center=(0, 0, 0), i_size=width, j_size=height, direction=direction)
        elif primitive_type == 'cylinder':
            pv_mesh = pv.Cylinder(radius=radius, height=height, resolution=resolution, direction=direction)
        elif primitive_type == 'cone':
            pv_mesh = pv.Cone(radius=radius, height=height, resolution=100, direction=direction)
        elif primitive_type == 'pyramid':
            pv_mesh = pv.Cone(radius=radius, height=height, resolution=4, direction=direction)
            pv_mesh.rotate_y(45, inplace=True)
        elif primitive_type == 'disc':
            pv_mesh = pv.Disc(center=(0, 0, 0), inner=0, outer=radius, normal=direction, r_res=resolution, c_res=resolution)
        else:
            raise ValueError(f"Unknown primitive type: {primitive_type}")
        
        # Always triangulate to ensure consistent face format
        pv_mesh = pv_mesh.triangulate()

        # Compute normals
        pv_mesh.compute_normals(
            cell_normals=False,
            point_normals=True,
            split_vertices=True,
            feature_angle=30,
            inplace=True,
        )
        vertices = pv_mesh.points.astype(np.float32)
        
        # After triangulation, all faces should be triangles (4 values: [3, v0, v1, v2])
        faces = pv_mesh.faces.reshape(-1, 4)[:, 1:].astype(np.uint32)
        normals = pv_mesh.point_normals.astype(np.float32)

        md = MeshData(vertices=vertices, faces=faces)
        if normals.shape[0] > 0:
            md._vertex_normals = normals
            
        return md

