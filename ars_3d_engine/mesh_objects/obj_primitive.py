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
        self.lod = params.get('lod', 30)
        self.direction = params.get('direction', (0, 1, 0))
        self.slice_start = params.get('slice_start', 0)
        self.radius_inner = params.get('radius_inner', 0.0)


    @classmethod
    def create(cls, primitive_type='sphere', color=(102/255, 108/255, 120/255, 1.0), 
               translate=(0.0, 0.0, 0.0), **params):
        """
        Create a parametric primitive mesh.
        
        Args:
            primitive_type: Type of primitive ('sphere', 'cube', 'plane', 'cylinder', 'cone', 'disc', 'pyramid', 'torus')
            color: RGBA color tuple
            translate: Position tuple (x, y, z)
            **params: Additional parameters like radius, width, height, depth, lod, direction, slice_start
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
            **params: Optional new parameters (radius, width, height, depth, lod, direction, slice_start)
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
        if 'lod' in params:
            self.lod = params['lod']
        if 'direction' in params:
            self.direction = params['direction']
        if 'slice_start' in params:
            self.slice_start = params['slice_start']
        if 'radius_inner' in params:
            self.radius_inner = params['radius_inner']
        
        # Prepare parameters dict for mesh generation
        mesh_params = {
            'radius': self.radius,
            'width': self.width,
            'height': self.height,
            'depth': self.depth,
            'lod': self.lod,
            'direction': self.direction,
            'slice_start': self.slice_start,
            'radius_inner': self.radius_inner
        }
        
        # Regenerate mesh with new type
        md = self._generate_mesh(primitive_type, **mesh_params)
        
        # Update the visual's mesh data using set_data method
        # Note: self._visual is the actual Mesh object, self.visual is the Node wrapper
        self._visual.set_data(meshdata=md)
        

    def get_params(self):
        """Provide CPrimitive-specific parameters for cloning."""
        return {
            'primitive_type': self.primitive_type,
            'radius': self.radius,
            'width': self.width,
            'height': self.height,
            'depth': self.depth,
            'lod': self.lod,
            'direction': self.direction,
            'slice_start': self.slice_start,
            'radius_inner': self.radius_inner
        }

    @staticmethod
    def _generate_mesh(primitive_type='sphere', **params):
        """
        Generate mesh data based on primitive type and parameters.
        
        Args:
            primitive_type: Type of primitive to generate
            **params: radius, width, height, depth, lod, etc.
        """
        # Extract common parameters with defaults
        radius = params.get('radius', 1.0)
        width = params.get('width', 2.0)
        height = params.get('height', 2.0)
        depth = params.get('depth', 2.0)
        lod = params.get('lod', 30)
        direction = params.get('direction', (0, 1, 0))
        slice_start = params.get('slice_start', 0)
        radius_inner = params.get('radius_inner', 0.0)
        
        # Generate PyVista mesh based on type
        if primitive_type == 'sphere':
            pv_mesh = pv.Sphere(
            radius = radius,
            center = (0.0, 0.0, 0.0),
            direction = direction,
            theta_resolution = lod,
            phi_resolution = lod,
            start_theta = slice_start,
            end_theta = 360.0,
            start_phi = 0.0,
            end_phi = 180.0,
            )


        elif primitive_type == 'cube':
            pv_mesh = pv.Cube(center=(0, 0, 0), x_length=width, y_length=height, z_length=depth)
        elif primitive_type == 'plane':
            pv_mesh = pv.Plane(center=(0, 0, 0), i_size=width, j_size=height, direction=direction)
        elif primitive_type == 'cylinder':
            pv_mesh = pv.Cylinder(radius=radius, height=height, resolution=lod, direction=direction)
        elif primitive_type == 'cone':
            pv_mesh = pv.Cone(radius=radius, height=height, resolution=lod, direction=direction, capping = True)
        elif primitive_type == 'pyramid':
            pv_mesh = pv.Cone(radius=radius, height=height, resolution=4, direction=direction)
            pv_mesh.rotate_y(45, inplace=True)
        elif primitive_type == 'disc':
            if radius_inner == radius: radius+=0.01  # Avoid zero-area disc
            pv_mesh = pv.Disc(center=(0, 0, 0), inner=radius_inner, outer=radius, normal=direction, r_res=lod, c_res=lod)
        elif primitive_type == 'torus':
            # If radius_inner is 0, use radius/2 as cross-section, otherwise use radius_inner
            cross_radius = radius_inner if radius_inner > 0 else 0.01
            pv_mesh = pv.ParametricTorus(ringradius=radius, crosssectionradius=cross_radius, v_res=lod, u_res=lod, w_res=lod)
            pv_mesh.rotate_x(90, inplace=True)
        else:
            raise ValueError(f"Unknown primitive type: {primitive_type}")
        
        # Always triangulate to ensure consistent face format
        pv_mesh = pv_mesh.triangulate()

        # Compute normals BEFORE generating texture coordinates
        # because compute_normals with split_vertices=True creates new vertices
        pv_mesh.compute_normals(
            cell_normals=False,
            point_normals=True,
            split_vertices=True,
            feature_angle=30,
            inplace=True,
        )
        
        # NOW generate texture coordinates after vertices are finalized
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
        Must be called AFTER compute_normals with split_vertices.
        """
        vertices = pv_mesh.points
        n_points = vertices.shape[0]
        
        # Try to use PyVista's built-in texture coordinates if available
        if hasattr(pv_mesh, 'texture_map_to_sphere') and primitive_type == 'sphere':
            try:
                pv_mesh.texture_map_to_sphere(inplace=True)
                if 'Texture Coordinates' in pv_mesh.point_data:
                    return pv_mesh.point_data['Texture Coordinates'][:, :2].astype(np.float32)
            except:
                pass
        
        if primitive_type == 'sphere':
            # Spherical UV mapping - Y is up (poles are at Y-axis extremes)
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            
            # U: longitude (0 to 1) - angle around Y-axis in XZ plane
            # Front (Z+) should be at U=0.5, right (X+) at U=0.25, back (Z-) at U=0.75, left (X-) at U=0 or 1
            u = 0.5 - np.arctan2(x, z) / (2 * np.pi)
            
            # V: latitude (0 to 1) - height along Y-axis
            # V=0 at bottom (south pole, Y=-radius), V=1 at top (north pole, Y=+radius)
            r = np.sqrt(x**2 + y**2 + z**2)
            r = np.maximum(r, 1e-8)  # Avoid division by zero
            v = 0.5 + np.arcsin(np.clip(y / r, -1, 1)) / np.pi
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
        elif primitive_type == 'cube':
            # Use normals to determine which face each vertex belongs to
            normals = pv_mesh.point_normals
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            nx, ny, nz = normals[:, 0], normals[:, 1], normals[:, 2]
            
            u = np.zeros(n_points)
            v = np.zeros(n_points)
            
            # Determine face based on normal direction (which component is largest)
            abs_nx, abs_ny, abs_nz = np.abs(nx), np.abs(ny), np.abs(nz)
            
            # Find bounding box for normalization
            x_range = x.max() - x.min()
            y_range = y.max() - y.min()
            z_range = z.max() - z.min()
            
            # X faces (left/right)
            mask_x = (abs_nx > abs_ny) & (abs_nx > abs_nz)
            u[mask_x] = (z[mask_x] - z.min()) / (z_range + 1e-8)
            v[mask_x] = (y[mask_x] - y.min()) / (y_range + 1e-8)
            
            # Y faces (top/bottom)
            mask_y = (abs_ny > abs_nx) & (abs_ny > abs_nz)
            u[mask_y] = (x[mask_y] - x.min()) / (x_range + 1e-8)
            v[mask_y] = (z[mask_y] - z.min()) / (z_range + 1e-8)
            
            # Z faces (front/back)
            mask_z = (abs_nz >= abs_nx) & (abs_nz >= abs_ny)
            u[mask_z] = (x[mask_z] - x.min()) / (x_range + 1e-8)
            v[mask_z] = (y[mask_z] - y.min()) / (y_range + 1e-8)
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
        elif primitive_type == 'plane':
            # Simple planar UV mapping - maintain aspect ratio
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            
            # Find ranges
            x_range = x.max() - x.min()
            y_range = y.max() - y.min()
            z_range = z.max() - z.min()
            
            # Determine which plane the mesh is in by finding the dimension with least variation
            if x_range <= y_range and x_range <= z_range:
                # Plane is perpendicular to X axis, use Y and Z
                u_coord, v_coord = y, z
                u_range, v_range = y_range, z_range
            elif y_range <= x_range and y_range <= z_range:
                # Plane is perpendicular to Y axis, use X and Z
                u_coord, v_coord = x, z
                u_range, v_range = x_range, z_range
            else:
                # Plane is perpendicular to Z axis, use X and Y
                u_coord, v_coord = x, y
                u_range, v_range = x_range, y_range
            
            # Normalize to 0-1 while maintaining aspect ratio
            max_range = max(u_range, v_range)
            if max_range > 1e-8:
                u = (u_coord - u_coord.min()) / max_range
                v = (v_coord - v_coord.min()) / max_range
            else:
                u = np.zeros(n_points)
                v = np.zeros(n_points)
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
        elif primitive_type in ['cylinder', 'cone', 'pyramid']:
            # Cylindrical UV mapping
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            
            # U: angle around the Y-axis (0 to 1)
            u = 0.5 + np.arctan2(z, x) / (2 * np.pi)
            
            # V: height along Y-axis (0 to 1)
            y_min, y_max = y.min(), y.max()
            if y_max - y_min > 1e-8:
                v = (y - y_min) / (y_max - y_min)
            else:
                v = np.full(n_points, 0.5)
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
        elif primitive_type == 'disc':
            # Polar/radial UV mapping for disc - proper circular mapping
            # Disc default: normal=(0,1,0) means disc is in XZ plane (Y is up)
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            normals = pv_mesh.point_normals
            
            # Use average normal to determine disc orientation
            avg_normal = np.mean(np.abs(normals), axis=0)
            
            # Determine which axis is the normal (perpendicular to disc)
            if avg_normal[0] > avg_normal[1] and avg_normal[0] > avg_normal[2]:
                # Normal is along X-axis, disc is in YZ plane
                u_coord, v_coord = y, z
            elif avg_normal[1] > avg_normal[0] and avg_normal[1] > avg_normal[2]:
                # Normal is along Y-axis, disc is in XZ plane
                u_coord, v_coord = x, z
            else:
                # Normal is along Z-axis, disc is in XY plane
                u_coord, v_coord = x, y
            
            # Center the coordinates
            u_center = (u_coord.max() + u_coord.min()) / 2
            v_center = (v_coord.max() + v_coord.min()) / 2
            
            # Get relative positions from center
            u_rel = u_coord - u_center
            v_rel = v_coord - v_center
            
            # Calculate radius for each point
            radius = np.sqrt(u_rel**2 + v_rel**2)
            max_radius = radius.max()
            
            # Normalize radius to 0-1
            if max_radius > 1e-8:
                normalized_radius = radius / max_radius
            else:
                normalized_radius = np.zeros(n_points)
            
            # Calculate angle (theta) for each point
            theta = np.arctan2(v_rel, u_rel)
            
            # Convert polar coordinates to UV
            # Map radius to distance from center (0.5, 0.5)
            # Points at center have UV = (0.5, 0.5)
            # Points at edge are at distance 0.5 from center
            u = 0.5 + 0.5 * normalized_radius * np.cos(theta)
            v = 0.5 + 0.5 * normalized_radius * np.sin(theta)
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
        elif primitive_type == 'torus':
            # Toroidal UV mapping
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            
            # U: angle around major radius (in XY plane after rotation)
            u = 0.5 + np.arctan2(x, y) / (2 * np.pi)
            
            # V: angle around minor radius (tube)
            # Calculate distance from center axis in XY plane
            r_xy = np.sqrt(x**2 + y**2)
            # Mean radius is the major radius
            r_major = np.median(r_xy)
            # V is based on the angle around the tube
            v = 0.5 + np.arctan2(z, r_xy - r_major) / (2 * np.pi)
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
        else:
            # Fallback: simple planar projection on XY
            x, y = vertices[:, 0], vertices[:, 1]
            x_range = x.max() - x.min()
            y_range = y.max() - y.min()
            
            u = (x - x.min()) / (x_range + 1e-8)
            v = (y - y.min()) / (y_range + 1e-8)
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
            
            texcoords = np.column_stack([u, v]).astype(np.float32)
        
        return texcoords

