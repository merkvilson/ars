import numpy as np
from vispy import scene

from vispy.geometry import MeshData  

from PIL import Image


from ars_3d_engine.mesh_objects.scene_objects import CGeometry


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
    
    def get_params(self):
        """Provide CSprite-specific parameters for cloning."""
        return {'cfg': self.cfg}

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

