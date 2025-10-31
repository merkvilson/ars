import numpy as np
from vispy import scene

from ars_3d_engine.mesh_objects.scene_objects import CGeometry
import pyvista as pv
from vispy.geometry import MeshData


class CPrimitive(CGeometry):
    def __init__(self, visual, **params):
        super().__init__(visual)
        
        # Store primitive parameters
        self.name = params.get('primitive_type', 'Object').capitalize()
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
            primitive_type: Type of primitive ('sphere', 'cube', 'plane', 'cylinder', 'cone', 'disc', 'pyramid', 'torus')
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
            primitive_type: New primitive type ('sphere', 'cube', 'plane', 'cylinder', 'cone', 'disc', 'pyramid', 'torus')
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

    def get_params(self):
        """Provide CPrimitive-specific parameters for cloning."""
        return {
            'primitive_type': self.primitive_type,
            'radius': self.radius,
            'width': self.width,
            'height': self.height,
            'depth': self.depth,
            'resolution': self.resolution,
            'direction': self.direction
        }

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
            pv_mesh = pv.Sphere(
            radius = radius,
            center = (0.0, 0.0, 0.0),
            direction = (0.0, 0.0, 1.0),
            theta_resolution = resolution,
            phi_resolution = resolution,
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
        elif primitive_type == 'torus':
            pv_mesh = pv.ParametricTorus(ringradius=radius, crosssectionradius=radius/2,)
            pv_mesh.rotate_x(90, inplace=True)
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
        
        # Generate texture coordinates
        texcoords = CPrimitive._generate_texture_coords(pv_mesh, primitive_type)
        
        vertices = pv_mesh.points.astype(np.float32)
        
        # After triangulation, all faces should be triangles (4 values: [3, v0, v1, v2])
        faces = pv_mesh.faces.reshape(-1, 4)[:, 1:].astype(np.uint32)
        normals = pv_mesh.point_normals.astype(np.float32)

        md = MeshData(vertices=vertices, faces=faces)
        if normals.shape[0] > 0:
            md._vertex_normals = normals
        if texcoords is not None and texcoords.shape[0] > 0:
            md._vertex_tex_coords = texcoords
            
        return md

    @staticmethod
    def _generate_texture_coords(pv_mesh, primitive_type):
        """
        Generate UV texture coordinates for the mesh based on primitive type.
        """
        vertices = pv_mesh.points
        n_points = vertices.shape[0]
        
        if primitive_type == 'sphere':
            # Spherical UV mapping
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            # Convert to spherical coordinates
            r = np.sqrt(x**2 + y**2 + z**2)
            r = np.maximum(r, 1e-8)  # Avoid division by zero
            
            # U: longitude (0 to 1)
            u = 0.5 + np.arctan2(x, z) / (2 * np.pi)
            # V: latitude (0 to 1)
            v = 0.5 - np.arcsin(np.clip(y / r, -1, 1)) / np.pi
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
        elif primitive_type == 'cube':
            # Box/cubic UV mapping - project to dominant face
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            abs_x, abs_y, abs_z = np.abs(x), np.abs(y), np.abs(z)
            
            u = np.zeros(n_points)
            v = np.zeros(n_points)
            
            # Determine dominant axis for each vertex
            # +X face
            mask = (abs_x >= abs_y) & (abs_x >= abs_z) & (x > 0)
            u[mask] = -z[mask] / abs_x[mask] * 0.5 + 0.5
            v[mask] = y[mask] / abs_x[mask] * 0.5 + 0.5
            
            # -X face
            mask = (abs_x >= abs_y) & (abs_x >= abs_z) & (x < 0)
            u[mask] = z[mask] / abs_x[mask] * 0.5 + 0.5
            v[mask] = y[mask] / abs_x[mask] * 0.5 + 0.5
            
            # +Y face
            mask = (abs_y >= abs_x) & (abs_y >= abs_z) & (y > 0)
            u[mask] = x[mask] / abs_y[mask] * 0.5 + 0.5
            v[mask] = -z[mask] / abs_y[mask] * 0.5 + 0.5
            
            # -Y face
            mask = (abs_y >= abs_x) & (abs_y >= abs_z) & (y < 0)
            u[mask] = x[mask] / abs_y[mask] * 0.5 + 0.5
            v[mask] = z[mask] / abs_y[mask] * 0.5 + 0.5
            
            # +Z face
            mask = (abs_z >= abs_x) & (abs_z >= abs_y) & (z > 0)
            u[mask] = x[mask] / abs_z[mask] * 0.5 + 0.5
            v[mask] = y[mask] / abs_z[mask] * 0.5 + 0.5
            
            # -Z face
            mask = (abs_z >= abs_x) & (abs_z >= abs_y) & (z < 0)
            u[mask] = -x[mask] / abs_z[mask] * 0.5 + 0.5
            v[mask] = y[mask] / abs_z[mask] * 0.5 + 0.5
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
        elif primitive_type == 'plane':
            # Simple planar UV mapping
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            
            # Normalize to 0-1 range
            x_min, x_max = x.min(), x.max()
            y_min, y_max = y.min(), y.max()
            
            if x_max - x_min > 1e-8:
                u = (x - x_min) / (x_max - x_min)
            else:
                u = np.zeros(n_points)
                
            if y_max - y_min > 1e-8:
                v = (y - y_min) / (y_max - y_min)
            else:
                v = np.zeros(n_points)
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
        elif primitive_type in ['cylinder', 'cone', 'pyramid']:
            # Cylindrical UV mapping
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            
            # U: angle around the axis (0 to 1)
            u = 0.5 + np.arctan2(x, z) / (2 * np.pi)
            
            # V: height along the axis (0 to 1)
            y_min, y_max = y.min(), y.max()
            if y_max - y_min > 1e-8:
                v = (y - y_min) / (y_max - y_min)
            else:
                v = np.full(n_points, 0.5)
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
        elif primitive_type == 'disc':
            # Radial UV mapping for disc
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            
            # Normalize position to 0-1 range from center
            r = np.sqrt(x**2 + y**2)
            r_max = r.max()
            if r_max > 1e-8:
                r_normalized = r / r_max
            else:
                r_normalized = np.zeros(n_points)
            
            # U and V from -1 to 1, then to 0 to 1
            u = x / (r_max + 1e-8) * 0.5 + 0.5
            v = y / (r_max + 1e-8) * 0.5 + 0.5
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
        elif primitive_type == 'torus':
            # Toroidal UV mapping
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            
            # U: angle around major radius
            u = 0.5 + np.arctan2(y, x) / (2 * np.pi)
            
            # V: angle around minor radius (tube)
            # Calculate distance from center axis
            r_major = np.sqrt(x**2 + y**2)
            v = 0.5 + np.arctan2(z, r_major - r_major.mean()) / (2 * np.pi)
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
        else:
            # Fallback: simple planar projection
            x, y = vertices[:, 0], vertices[:, 1]
            x_min, x_max = x.min(), x.max()
            y_min, y_max = y.min(), y.max()
            
            u = (x - x_min) / (x_max - x_min + 1e-8)
            v = (y - y_min) / (y_max - y_min + 1e-8)
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
        
        return texcoords

