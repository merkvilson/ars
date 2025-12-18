from abc import ABC
import numpy as np
import warnings
from vispy import scene
from vispy.scene import transforms
from vispy.visuals.transforms import NullTransform
from vispy.visuals.filters import ShadingFilter
from vispy.geometry import MeshData  
from vispy.io import imread 
from vispy.visuals.filters import TextureFilter 
from theme.fonts import font_icons as ic
import time
from vispy.app import Timer
from scipy.spatial.transform import Rotation as ScipyRotation

# Suppress gimbal lock warning - expected behavior with Euler angles
warnings.filterwarnings('ignore', message='Gimbal lock detected')

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

        # Track cumulative rotation angles (avoids Euler angle representation issues)
        self._rotation_angles = np.array([0.0, 0.0, 0.0], dtype=float)

        self.prompt = ""
        self.seed = 12345
        self.steps = 20
        self.cfg = 7.0
        self.denoise = 1.0
        self.workflow = None
        self.resolution = (512, 512)
        self.texture_path = None

        self.symbol = ic.ICON_OBJ_BBOX

        # Attach shading filter for directional light
        self.shading_filter = None
        if hasattr(self._visual, 'mesh_data') and self._visual.mesh_data is not None:
            self.shading_filter = ShadingFilter(shading='smooth', shininess=50, light_dir=(0, -1, -1))
            #self.shading_filter.ambient_light = (0.2, 0.2, 0.2)
            self._visual.attach(self.shading_filter)
            self._visual.update()

        self._update_gl_state()

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    def remove(self):
        """Completely remove the object from project"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.remove_object(self)

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

    def get_world_matrix(self):
        """Calculate the full world transformation matrix."""
        chain = []
        current = self._node
        # Traverse up the hierarchy
        while current is not None:
            chain.append(current)
            current = current.parent
            # Stop if we reach a node that isn't a standard scene node (like the ViewBox or SceneCanvas)
            if not isinstance(current, scene.Node):
                break
        
        # Calculate World = Local @ Parent @ ... @ Root (Row-Major)
        matrix = np.eye(4, dtype=np.float32)
        for n in chain:
            if hasattr(n, 'transform') and hasattr(n.transform, 'matrix'):
                matrix = matrix @ n.transform.matrix
        return matrix

    def get_position(self) -> np.ndarray:
        """Get the world position of the object."""
        # Extract translation from world matrix (Row 3 in Row-Major)
        return self.get_world_matrix()[3, :3]

    def get_local_position(self) -> np.ndarray:
        """Get the local position relative to the parent."""
        return self._node.transform.map([0, 0, 0])[:3]

    # homogeneous version (handles 4D coords / perspective parents) (Not used currently but kept for reference)
    def homogeneous_position(self) -> np.ndarray:
        p = self._node.transform.map([0.0, 0.0, 0.0, 1.0])
        p = np.asarray(p, dtype=float)
        if p.size == 4 and abs(p[3]) > 1e-12:
            return (p[:3] / p[3]).copy()
        return p[:3].copy()


    def get_parent_world_matrix(self):
        """Calculate the world transformation matrix of the parent node."""
        chain = []
        current = self._node.parent
        # Traverse up the hierarchy
        while current is not None:
            chain.append(current)
            current = current.parent
            if not isinstance(current, scene.Node):
                break
        
        matrix = np.eye(4, dtype=np.float32)
        for n in chain:
            if hasattr(n, 'transform') and hasattr(n.transform, 'matrix'):
                matrix = matrix @ n.transform.matrix
        return matrix

    def set_world_position(self, x: float, y: float, z: float) -> None:
        """Set the object's position in world coordinates."""
        parent_matrix = self.get_parent_world_matrix()
        
        try:
            inv_parent = np.linalg.inv(parent_matrix)
        except np.linalg.LinAlgError:
            inv_parent = np.eye(4)
            
        # Create world point (homogeneous)
        world_point = np.array([x, y, z, 1.0], dtype=np.float32)
        
        # Transform to local space: Local = World @ inv(Parent)
        local_point = world_point @ inv_parent
        
        # Normalize if w != 1 (though for affine transforms it usually is)
        if abs(local_point[3]) > 1e-12:
            local_point /= local_point[3]
            
        self.set_position(local_point[0], local_point[1], local_point[2])

    def set_position(self, x: float, y: float, z: float) -> None:
        """Set the object's local position relative to its parent."""
        x = float(x)
        y = float(y)
        z = float(z)

        if isinstance(self._node.transform, transforms.MatrixTransform):
            m = np.eye(4, dtype=np.float32)
            m[3, :3] = (x, y, z)
            self._node.transform.matrix = m
            return

        tr = transforms.MatrixTransform()
        tr.translate((x, y, z))
        self._node.transform = tr

    def move_to(self, center = None, offset=0.0, animate=False):
        current_pos = self.get_position() # World Position
        if center is None:
            center = current_pos
        
        target_center = np.array(center, dtype=float)
        target_center[1] += offset

        if not animate:
            self.set_world_position(*target_center)
        else:
            self._anim_start_center = current_pos
            self._anim_target_center = target_center
            
            self._anim_duration = float(animate)
            self._anim_start_time = time.time()
            
            if hasattr(self, '_anim_timer'):
                self._anim_timer.stop()
            
            self._anim_timer = Timer(interval=0.016, connect=self._on_anim_update, start=True)

    def _on_anim_update(self, event):
        elapsed = time.time() - self._anim_start_time
        t = elapsed / self._anim_duration
        
        if t >= 1.0:
            t = 1.0
            self._anim_timer.stop()
            
        # Ease out cubic
        t_ease = 1 - (1 - t) ** 3
        
        # Interpolate Center (World Space)
        current_center = (1 - t_ease) * self._anim_start_center + t_ease * self._anim_target_center
        self.set_world_position(*current_center)

    def set_prompt(self, prompt: str) -> None:
        """Set the text prompt associated with this object."""
        self._prompt = prompt

    def get_prompt(self) -> str:
        """Get the text prompt associated with this object."""
        return self._prompt

    def pick(self):
        """Select this object."""
        if hasattr(self, 'manager') and self.manager:
            try:
                index = self.manager._objects.index(self)
                print(f"Picking object: {self.get_name()} (ID: {index})")
                self.manager.set_selection_state([index], index)
            except (ValueError, AttributeError) as e:
                print(f"Pick failed for {self.get_name()}: {e}")

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

    def set_rotation(self, x: float, y: float, z: float) -> None:
        """Set the rotation of the object using Euler angles (in degrees). Order: XYZ."""
        # Store the angles for retrieval
        self._rotation_angles = np.array([x, y, z], dtype=float)
        
        # Get current scale to preserve it
        current_scale = self.get_scale()
        
        # Create rotation matrix from Euler angles (degrees)
        rotation = ScipyRotation.from_euler('xyz', [x, y, z], degrees=True)
        R = np.eye(4, dtype=float)
        R[:3, :3] = rotation.as_matrix()
        
        # Create scale matrix
        S = np.eye(4, dtype=float)
        S[0, 0] = current_scale[0]
        S[1, 1] = current_scale[1]
        S[2, 2] = current_scale[2]
        
        # Combine scale and rotation (same order as gizmo: S @ R)
        new_matrix = (S @ R).astype(np.float32)
        self._visual.transform.matrix = new_matrix

    def get_rotation(self) -> tuple:
        """Get the current rotation as Euler angles (in degrees). Order: XYZ."""
        return tuple(self._rotation_angles)

    def rotate_around_axis(self, axis: tuple, angle_deg: float) -> None:
        """
        Rotate the object incrementally around a given axis.
        This method composes rotations without Euler angle conversion, avoiding gimbal lock.
        
        Args:
            axis: The axis to rotate around as (x, y, z). Common values:
                  (0, 1, 0) for Y-axis, (1, 0, 0) for X-axis, (0, 0, 1) for Z-axis.
            angle_deg: The angle to rotate in degrees.
        """
        # Update tracked angles for the corresponding axis
        axis = np.asarray(axis, dtype=float)
        axis_norm = np.linalg.norm(axis)
        if axis_norm < 1e-9:
            return
        axis = axis / axis_norm
        
        # Update stored angles (approximate - works for single-axis rotations)
        if abs(axis[0] - 1.0) < 0.01:
            self._rotation_angles[0] += angle_deg
        elif abs(axis[1] - 1.0) < 0.01:
            self._rotation_angles[1] += angle_deg
        elif abs(axis[2] - 1.0) < 0.01:
            self._rotation_angles[2] += angle_deg
        
        current_scale = self.get_scale()
        current_matrix = self._visual.transform.matrix.copy()
        
        # Extract current rotation matrix (remove scale)
        sx, sy, sz = current_scale
        if sx < 1e-8: sx = 1e-8
        if sy < 1e-8: sy = 1e-8
        if sz < 1e-8: sz = 1e-8
        
        rot_matrix = current_matrix[:3, :3].copy()
        rot_matrix[0, :] /= sx
        rot_matrix[1, :] /= sy
        rot_matrix[2, :] /= sz
        
        # Convert current rotation to ScipyRotation
        current_rotation = ScipyRotation.from_matrix(rot_matrix)
        
        # Create delta rotation from axis-angle (like gizmo does)
        axis = np.asarray(axis, dtype=float)
        axis_norm = np.linalg.norm(axis)
        if axis_norm < 1e-9:
            return
        axis = axis / axis_norm
        
        angle_rad = np.radians(angle_deg)
        delta_rotation = ScipyRotation.from_rotvec(angle_rad * axis)
        
        # Compose rotations (local axis rotation)
        new_rotation = current_rotation * delta_rotation
        
        # Build new transform matrix
        R = np.eye(4, dtype=float)
        R[:3, :3] = new_rotation.as_matrix()
        
        S = np.eye(4, dtype=float)
        S[0, 0] = current_scale[0]
        S[1, 1] = current_scale[1]
        S[2, 2] = current_scale[2]
        
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


    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    def set_parent(self, parent):
        if self._parent == parent:
            return

        # 1. Capture current world state (Visual World Matrix)
        # World_Visual = Local_Visual @ World_Node
        old_world_node = self.get_world_matrix()
        old_visual_world = self._visual.transform.matrix @ old_world_node
        old_pos = self.get_position()

        if self._parent:
            self._parent._children.remove(self)
        self._parent = parent
        if parent:
            parent._children.append(self)
            self.visual.parent = parent.rotation_visual
        elif hasattr(self, 'manager') and self.manager:
            self.visual.parent = self.manager._view.scene
        
        if hasattr(self, 'manager') and self.manager:
            self.manager.notify_parent_changed(self, parent)

        # 2. Restore World Position (Updates self._node translation)
        self.set_world_position(*old_pos)

        # 3. Restore World Rotation/Scale (Updates self._visual transform)
        # New_Local_Visual = Old_Visual_World @ Inverse(New_World_Node)
        new_world_node = self.get_world_matrix()
        try:
            inv_new_world_node = np.linalg.inv(new_world_node)
        except np.linalg.LinAlgError:
            inv_new_world_node = np.eye(4)
            
        new_local_visual = old_visual_world @ inv_new_world_node
        self._visual.transform.matrix = new_local_visual

        # 4. Update stored Euler angles from the new matrix
        # Extract rotation part (normalize basis vectors to remove scale)
        m = new_local_visual
        sx = np.linalg.norm(m[0, :3])
        sy = np.linalg.norm(m[1, :3])
        sz = np.linalg.norm(m[2, :3])
        
        if sx > 1e-8 and sy > 1e-8 and sz > 1e-8:
            rot_matrix = m[:3, :3].copy()
            rot_matrix[0, :] /= sx
            rot_matrix[1, :] /= sy
            rot_matrix[2, :] /= sz
            
            try:
                r = ScipyRotation.from_matrix(rot_matrix)
                self._rotation_angles = r.as_euler('xyz', degrees=True)
            except Exception:
                pass



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

    def get_params(self):
        """
        Override this method in subclasses to provide additional constructor parameters for cloning.
        Returns a dictionary of parameters to pass to the constructor.
        """
        return {}

    def clone(self):
        """
        Create a deep copy of this geometry object.
        Subclasses can override get_params() to provide their specific constructor parameters.
        """
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

        # Get subclass-specific parameters
        clone_params = self.get_params()
        clone_params['name'] = self.name + "_copy"
        
        # Create new object of the same class type
        new_obj = type(self)(new_visual, **clone_params)

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
