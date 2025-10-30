from abc import ABC
import numpy as np
from vispy import scene
from vispy.scene import transforms
from vispy.visuals.transforms import NullTransform
from vispy.io import read_mesh
from vispy.visuals.filters import ShadingFilter
from vispy.geometry import MeshData  

from vispy.io import imread 
from vispy.visuals.filters import TextureFilter 
from PIL import Image # <-- Added this import

import pyvista as pv

class CGeometry(ABC):

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

        self.prompt = ""
        self.seed = 12345
        self.steps = 20
        self.cfg = 7.0
        self.denoise = 1.0
        self.workflow = None
        self.resolution = (512, 512)
        self.texture_path = None

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

    def get_position(self) -> np.ndarray:
        # Map the local origin [0,0,0] into world coordinates
        return self._node.transform.map([0, 0, 0])[:3]

    # homogeneous version (handles 4D coords / perspective parents) (Not used currently but kept for reference)
    def homogeneous_position(self) -> np.ndarray:
        p = self._node.transform.map([0.0, 0.0, 0.0, 1.0])
        p = np.asarray(p, dtype=float)
        if p.size == 4 and abs(p[3]) > 1e-12:
            return (p[:3] / p[3]).copy()
        return p[:3].copy()


    def set_position(self, x: float, y: float, z: float) -> None:
        tr = transforms.MatrixTransform()
        tr.translate((float(x), float(y), float(z)))
        self._node.transform = tr

    def set_prompt(self, prompt: str) -> None:
        """Set the text prompt associated with this object."""
        self._prompt = prompt

    def get_prompt(self) -> str:
        """Get the text prompt associated with this object."""
        return self._prompt

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


    def get_scale(self) -> tuple:
        """Get the current scale of the object. Returns a tuple (sx, sy, sz)."""
        current_matrix = self._visual.transform.matrix
        sx = np.linalg.norm(current_matrix[0, :3])
        sy = np.linalg.norm(current_matrix[1, :3])
        sz = np.linalg.norm(current_matrix[2, :3])
        return (sx, sy, sz)

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



    def set_texture(self, image_path: str) -> None:
        """Apply a texture to the mesh from an image file path. Requires the mesh to have texture coordinates."""
        # Use the *new* mesh_data attached to the visual
        current_mesh_data = self._visual.mesh_data
        texcoords = getattr(current_mesh_data, '_vertex_tex_coords', None)
        
        if texcoords is None:
            print("Mesh does not have texture coordinates. Cannot apply texture.")
            return
        if texcoords.ndim != 2 or texcoords.shape[-1] not in (2, 3):
            print("Texture coordinates must be a 2D array with last dimension 2 or 3.")
            return
        
        # Remove old texture filter if it exists
        if hasattr(self, 'texture_filter') and self.texture_filter is not None:
            self._visual.detach(self.texture_filter)
            self.texture_filter = None
        
        texcoords_to_use = texcoords[:, :2] if texcoords.shape[-1] == 3 else texcoords
        
        try:
            image = imread(image_path)
        except FileNotFoundError:
            print(f"Error: Texture file not found at {image_path}")
            return
        except Exception as e:
            print(f"Error reading texture file {image_path}: {e}")
            return

        image = np.flipud(image) 
        if image.ndim == 2:  image = image[..., np.newaxis]
        self.texture_filter = TextureFilter(image, texcoords_to_use)
        self._visual.attach(self.texture_filter)
        self._visual.update()

        self.texture_path = image_path  # Store the texture path

    def clone(self) -> 'CGeometry':
        # Copy mesh data
        md = self._visual.mesh_data
        verts = md.get_vertices().copy() if md.get_vertices() is not None else None
        faces = md.get_faces().copy() if md.get_faces() is not None else None
        normals = getattr(md, '_vertex_normals', None)
        if normals is not None:
            normals = normals.copy()
        texcoords = getattr(md, '_vertex_tex_coords', None)
        if texcoords is not None:
            texcoords = texcoords.copy()

        # Create new MeshData
        new_md = MeshData(vertices=verts, faces=faces)
        if normals is not None:
            new_md._vertex_normals = normals.astype(np.float32)
        if texcoords is not None:
            new_md._vertex_tex_coords = texcoords.astype(np.float32)

        # Create new visual with the new MeshData
        new_visual = scene.visuals.Mesh(
            meshdata=new_md,
            color=self.get_color(),
            shading=None  # Shading will be set later
        )

        # Create new object (moved up here so it's defined before setting attributes)
        new_obj = CMesh(new_visual, name=self.name + "_copy")

        # Copy texture if applied
        if hasattr(self, 'texture_filter') and self.texture_filter is not None and self.texture_path:
            # We can't just copy the filter, we need to re-apply the texture
            # using the new mesh's texcoords.
            new_obj.set_texture(self.texture_path)
        
        # Copy position (translation)
        new_obj.set_position(*self.get_position())

        # Copy rotation and scale (full transform matrix)
        new_obj._visual.transform.matrix = self._visual.transform.matrix.copy()

        # Copy shading
        new_obj.set_shading(self.get_shading())

        # Copy alpha and GL state
        new_obj.set_alpha(self.get_alpha())
        new_obj._update_gl_state()

        return new_obj

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

class CSprite(CGeometry):
    
    def __init__(self, visual, name="Sprite", cfg=7.0):
        # Call parent constructor first to initialize all CGeometry attributes
        super().__init__(visual, name)
        
        # Add CSprite-specific attributes
        self.cfg = cfg
        self.sprite_size = (2.0, 2.0) # Default size

    @staticmethod
    def _create_quad_meshdata(size):
        """Helper staticmethod to generate simple quad MeshData."""
        width, height = size
        hw, hh = width / 2.0, height / 2.0
        
        vertices = np.array([
            [-hw, -hh, 0],  # Bottom-left
            [ hw, -hh, 0],  # Bottom-right
            [ hw,  hh, 0],  # Top-right
            [-hw,  hh, 0],  # Top-left
        ], dtype=np.float32)
        
        # Two triangles to form the plane
        faces = np.array([
            [0, 1, 2],  # First triangle
            [0, 2, 3],  # Second triangle
        ], dtype=np.uint32)
        
        # Normals pointing in +Z direction
        normals = np.array([
            [0, 0, 1],
            [0, 0, 1],
            [0, 0, 1],
            [0, 0, 1],
        ], dtype=np.float32)
        
        # UV texture coordinates
        texcoords = np.array([
            [0, 0],  # Bottom-left
            [1, 0],  # Bottom-right
            [1, 1],  # Top-right
            [0, 1],  # Top-left
        ], dtype=np.float32)
        
        # Create MeshData
        md = MeshData(vertices=vertices, faces=faces)
        md._vertex_normals = normals
        md._vertex_tex_coords = texcoords
        return md

    @classmethod
    def create(cls, size=(2.0, 2.0), color=(1.0, 1.0, 1.0, 1.0), translate=(0.0, 0.0, 0.0), name="Sprite", cfg=7.0):
        
        # Use the static helper method to get the geometry
        md = CSprite._create_quad_meshdata(size)
        
        # Create visual
        v = scene.visuals.Mesh(meshdata=md, color=color, shading=None)
        
        # Create sprite object with custom attributes
        obj = cls(v, name=name, cfg=cfg)
        obj.set_position(translate[0], translate[1], translate[2])
        obj.sprite_size = size # Store the intended size
        
        return obj 
    


    def _update_gl_state(self):

            self._visual.set_gl_state(cull_face=False)



    def revert_cutout(self):
        """
        Reverts the cutout operation, restoring the sprite to a simple
        rectangular quad.
        """
        # Get the standard quad geometry using the helper
        new_md = CSprite._create_quad_meshdata(self.sprite_size)
        
        # Update the visual with the new (simple) geometry
        self._visual.set_data(meshdata=new_md)
        
        # Re-apply the texture if it exists
        if self.texture_path:
            self.set_texture(self.texture_path)
        
        self._visual.update()
        print("Sprite geometry reverted to standard quad.")

    def cutout(self):
        """
        Modifies the sprite's geometry based on the alpha channel of its texture.
        This will replace the existing quad with a mesh matching the
        opaque pixels of the texture.
        """
        if self.texture_path is None:
            print("Error: No texture_path set. Call set_texture() first.")
            return

        try:
            img = Image.open(self.texture_path)
        except Exception as e:
            print(f"Error opening image {self.texture_path}: {e}")
            return
        
        # Get image pixels
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        pixels = np.asarray(img)
        height_px, width_px = pixels.shape[:2]
        if width_px == 0 or height_px == 0:
             print("Error: Texture image has zero dimensions.")
             return
             
        mask = pixels[:, :, 3] > 0
        
        if not mask.any():
            print("Warning: Texture is fully transparent. Clearing geometry.")
            self._visual.set_data(meshdata=MeshData())
            self._visual.update()
            return
            
        # Get target mesh size from sprite
        width_units, height_units = self.sprite_size
        scale_x = width_units / width_px
        scale_y = height_units / height_px
        
        # Build index mapping for valid pixels
        indices = np.zeros((height_px, width_px), dtype=np.int32)
        num_vertices = mask.sum()
        indices[mask] = np.arange(num_vertices)  # 0-indexed
        
        # Get coordinates of valid pixels
        ys, xs = np.nonzero(mask)
        
        # Compute vertices
        vx = (xs - width_px * 0.5) * scale_x
        vy = -(ys - height_px * 0.5) * scale_y # Flipped Y to match vispy coords
        vz = np.zeros(num_vertices, dtype=np.float32)
        vertices = np.stack([vx, vy, vz], axis=-1).astype(np.float32)
        
        # Compute UVs
        u = xs / (width_px - 1.0)
        v = 1.0 - ys / (height_px - 1.0) # Flipped Y for texture mapping
        texcoords = np.stack([u, v], axis=-1).astype(np.float32)
        
        # Compute normals
        normals = np.zeros_like(vertices, dtype=np.float32)
        normals[:, 2] = 1.0  # Pointing +Z
        
        # Find valid quads (cells where all 4 corners are opaque)
        mask_down = mask[1:, :]
        mask_right = mask[:, 1:]
        mask_diag = mask[1:, 1:]
        mask_tl = mask[:-1, :-1]
        
        valid_quads = mask_tl & mask_right[:-1, :] & mask_down[:, :-1] & mask_diag
        qy, qx = np.nonzero(valid_quads)

        if qy.size == 0:
            print("Warning: No valid quads found. Result will be a point cloud (no faces).")
            faces = np.empty((0, 3), dtype=np.uint32)
        else:
            # Get vertex indices for the top-left corner of each quad
            idx = indices
            v1 = idx[qy, qx]          # Top-left
            v2 = idx[qy, qx + 1]      # Top-right
            v3 = idx[qy + 1, qx + 1]  # Bottom-right
            v4 = idx[qy + 1, qx]      # Bottom-left
            
            # Create two triangles per quad
            tri1 = np.stack([v1, v2, v3], axis=-1)
            tri2 = np.stack([v1, v3, v4], axis=-1)
            faces = np.concatenate([tri1, tri2], axis=0).astype(np.uint32)
        
        # Create new MeshData
        new_md = MeshData(vertices=vertices, faces=faces)
        new_md._vertex_normals = normals
        new_md._vertex_tex_coords = texcoords
        
        # Update the visual with the new geometry
        self._visual.set_data(meshdata=new_md)
        
        # Re-apply the texture. This is crucial!
        # It rebuilds the TextureFilter using the *new* texcoords.
        self.set_texture(self.texture_path)
        
        self._visual.update()
        print(f"Cutout complete. New mesh has {num_vertices} vertices and {faces.shape[0]} faces.")

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
    
#TODO: Examine and convert this code into a method of CText3D class
""" 
# convert test mesh into pyvista compitable code

import trimesh
import pyvista as pv

# Create 3D text mesh using a system font
mesh = trimesh.creation.text(
    text="Hello PyVista",
    font="Arial.ttf",
    height=1.0
)

# Convert trimesh to PyVista mesh
pv_mesh = pv.wrap(mesh)

plotter = pv.Plotter()
plotter.add_mesh(pv_mesh, color='gold')
plotter.show()

"""