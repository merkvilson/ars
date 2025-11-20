import sys, math, numpy as np
from vispy import scene
from vispy.visuals.transforms import MatrixTransform
from scipy.spatial.transform import Rotation as ScipyRotation 
try:
    from core.sound_manager import play_sound
    from core.cursor_modifier import set_cursor
    from ars_cmds.core_cmds.key_check import key_check
except ImportError:
    def play_sound(name):
        pass
    def set_cursor(name, hotspot='center'):
        pass
    def key_check(key_name):
        return False

def normalize(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n < 1e-9:
        return np.zeros_like(v)
    return v / n

class Rotation:
    def __init__(self):
        # Use Scipy's Rotation object, initialized to identity
        self._rotation = ScipyRotation.identity()

    def get_matrix(self):        # Get the 3x3 rotation matrix and embed it in a 4x4 identity matrix
        M = np.eye(4, dtype=float)
        M[:3, :3] = self._rotation.as_matrix()
        return M

    def rotate_around_local_axis(self, axis, angle_deg):        # Convert degrees to radians for the rotation vector
        angle_rad = math.radians(angle_deg)
        axis = normalize(axis)
        delta_rotation = ScipyRotation.from_rotvec(angle_rad * axis) # Create a new rotation from the axis and angle
        self._rotation = self._rotation * delta_rotation        # Compose the new rotation with the existing one (local axes)


def build_arrow_mesh(name, cone_radius=0.1, cone_height=0.15, segments=10):
    axis_letter = name[1]
    idx_axial, idx_rad1, idx_rad2 = {'x': (0,1,2), 'y': (1,2,0), 'z': (2,0,1)}[axis_letter]
    verts = []
    # cone base
    for i in range(segments):
        theta = 2 * math.pi * i / segments
        cos_th = math.cos(theta)
        sin_th = math.sin(theta)
        v = np.zeros(3)
        v[idx_rad1] = cone_radius * cos_th
        v[idx_rad2] = cone_radius * sin_th
        v[idx_axial] = -0.1  # Base at origin
        verts.append(v)
    # cone tip
    v = np.zeros(3)
    v[idx_axial] = cone_height
    verts.append(v)
    verts = np.array(verts, dtype=float)
    faces = []
    # cone sides
    cone_base_start = 0
    tip_idx = segments
    for i in range(segments):
        c0 = cone_base_start + i
        c1 = cone_base_start + (i + 1) % segments
        faces.append([c0, tip_idx, c1])
    faces = np.array(faces, dtype=np.int32)
    return verts, faces

def build_planar_mesh(axes, radius=0.18, thickness=0.06, segments=10, start_angle=110, end_angle=-20):
    axis1, axis2 = axes
    axis1 = normalize(axis1)
    axis2 = normalize(axis2)
    
    verts = []
    # Convert start and end angles to radians
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    # Generate vertices for the arc from start_angle to end_angle
    for i in range(segments + 1):
        # Linearly interpolate angle from start_rad to end_rad
        theta = start_rad + (end_rad - start_rad) * i / segments
        dir_xy = math.cos(theta) * axis1 + math.sin(theta) * axis2
        inner = dir_xy * (radius - thickness * 0.5)
        outer = dir_xy * (radius + thickness * 0.5)
        verts.append(inner)
        verts.append(outer)
    verts = np.array(verts, dtype=float)

    faces = []
    # Create faces to connect the inner and outer arcs
    for i in range(segments):
        i0 = 2 * i
        i1 = 2 * i + 1
        i2 = 2 * (i + 1)
        i3 = 2 * (i + 1) + 1
        faces.append([i0, i1, i2])
        faces.append([i1, i3, i2])
    faces = np.array(faces, dtype=np.int32)
    return verts, faces


class GizmoRenderer:
    COLORS = {
    'x': (0.70, 0.30, 0.30, 0.75),
    'y': (0.30, 0.70, 0.30, 0.75),
    'z': (0.30, 0.50, 0.70, 0.75),
   'xy': (0.30, 0.50, 0.70, 0.75),
   'yz': (0.70, 0.30, 0.30, 0.75),
   'zx': (0.30, 0.70, 0.30, 0.75),
'hover': (0.70, 0.70, 0.20, 0.90)}
    SPHERE_COLOR_DEFAULT = (0.35, 0.35, 0.35, 0.3)
    SPHERE_COLOR_HOVER = (0.82, 0.82, 0.82, 0.4)
    def __init__(self, parent_node, radius=1.4, base_thickness=0.06, segments=10, parent_view=None):
        self.parent = parent_node
        self._base_thickness = base_thickness
        self._segments = segments
        self._view = parent_view
        self.mesh_nodes = {}
        self._handle_offset_trans = 0.1

        self._create_handle('tx', np.array([1.00, 0.00, 0.00]), offset=self._handle_offset_trans)
        self._create_handle('ty', np.array([0.00, 1.00, 0.00]), offset=self._handle_offset_trans)
        self._create_handle('tz', np.array([0.00, 0.00, 1.00]), offset=self._handle_offset_trans)
        
        self._create_handle('sx', np.array([1.00, 0.00, 0.00]), offset=self._handle_offset_trans)
        self._create_handle('sy', np.array([0.00, 1.00, 0.00]), offset=self._handle_offset_trans)
        self._create_handle('sz', np.array([0.00, 0.00, 1.00]), offset=self._handle_offset_trans)

        self._create_planar_handle('txy', [np.array([1.0,0.0,0.0]), np.array([0.0,1.0,0.0])], offset=self._handle_offset_trans)
        self._create_planar_handle('tyz', [np.array([0.0,1.0,0.0]), np.array([0.0,0.0,1.0])], offset=self._handle_offset_trans)
        self._create_planar_handle('tzx', [np.array([0.0,0.0,1.0]), np.array([1.0,0.0,0.0])], offset=self._handle_offset_trans)

        self._create_planar_handle('sxy', [np.array([1.0,0.0,0.0]), np.array([0.0,1.0,0.0])], offset=self._handle_offset_trans)
        self._create_planar_handle('syz', [np.array([0.0,1.0,0.0]), np.array([0.0,0.0,1.0])], offset=self._handle_offset_trans)
        self._create_planar_handle('szx', [np.array([0.0,0.0,1.0]), np.array([1.0,0.0,0.0])], offset=self._handle_offset_trans)

        self._create_planar_handle('rxy', [np.array([1.0,0.0,0.0]), np.array([0.0,1.0,0.0])], offset=self._handle_offset_trans)
        self._create_planar_handle('ryz', [np.array([0.0,1.0,0.0]), np.array([0.0,0.0,1.0])], offset=self._handle_offset_trans)
        self._create_planar_handle('rzx', [np.array([0.0,0.0,1.0]), np.array([1.0,0.0,0.0])], offset=self._handle_offset_trans)
        
        self.update_handle_positions(np.array([1.0, 1.0, 1.0]))

    def _create_handle(self, name, axis, offset=None):
        color_key = name[1]
        if name.startswith('t'):
            pos = axis * (1.0 + offset)
            verts, faces = build_arrow_mesh(name)
            handle = scene.visuals.Mesh(vertices=verts, faces=faces, color=self.COLORS[color_key], parent=self.parent)
            self.mesh_nodes[name] = {"mesh": handle, "axis": axis, "offset": offset, "position": pos}
        else: # Scale handle
            pos = axis # Default position for scale=1
            size = 0.18
            handle = scene.visuals.Box(width=size, height=size, depth=size, parent=self.parent, color=self.COLORS[color_key])
            self.mesh_nodes[name] = {"mesh": handle, "axis": axis, "position": pos, "offset": offset}

        tr = MatrixTransform()
        tr.translate(pos)
        handle.transform = tr
        handle.set_gl_state('opaque', depth_test=False)
        handle.order = 2  # Handles render above hit spheres

        # Add semi-transparent hit sphere
        sphere_radius = 0.3
        sphere = scene.visuals.Sphere(radius=sphere_radius, color=self.SPHERE_COLOR_DEFAULT, parent=self.parent)
        sphere_tr = MatrixTransform()
        sphere_tr.translate(pos)
        sphere.transform = sphere_tr
        sphere.set_gl_state('translucent', depth_test=False)
        sphere.order = 1  # Spheres render below handles
        self.mesh_nodes[name]["hit_sphere"] = sphere
        self.mesh_nodes[name]["sphere_transform"] = sphere_tr

    def _create_planar_handle(self, name, axes, offset=None):
        axis1, axis2 = axes
        color_key = name[1:]
        if name.startswith('t') or name.startswith('r'):
            verts, faces = build_planar_mesh(axes)
        else:
            verts, faces = build_planar_mesh(axes, segments=2,radius=0.18, thickness=0.07, start_angle=110, end_angle=-20) 
        handle = scene.visuals.Mesh(vertices=verts, faces=faces, color=self.COLORS[color_key], parent=self.parent)
        
        if name.startswith('t') or name.startswith('r'):
            pos = normalize(axis1 + axis2) * (1.0 + (offset or 0))
            self.mesh_nodes[name] = {"mesh": handle, "axes": axes, "offset": offset, "position": pos}
        else: # Scale handle
            pos = axis1 + axis2 # Default position for scale=1
            self.mesh_nodes[name] = {"mesh": handle, "axes": axes, "position": pos, "offset": offset}

        tr = MatrixTransform()
        tr.translate(pos)
        handle.transform = tr
        handle.set_gl_state('opaque', depth_test=False)
        handle.order = 2  # Planar handles render above hit spheres

        # Add semi-transparent hit sphere
        sphere_radius = 0.3
        sphere = scene.visuals.Sphere(radius=sphere_radius, color=self.SPHERE_COLOR_DEFAULT, parent=self.parent)
        sphere_tr = MatrixTransform()
        sphere_tr.translate(pos)
        sphere.transform = sphere_tr
        sphere.set_gl_state('translucent', depth_test=False)
        sphere.order = 1  # Spheres render below handles
        self.mesh_nodes[name]["hit_sphere"] = sphere
        self.mesh_nodes[name]["sphere_transform"] = sphere_tr

        if name.startswith('r'):
            small_radius = 0.05
            small_sphere = scene.visuals.Sphere(radius=small_radius, color=self.COLORS[color_key], parent=self.parent)
            small_tr = MatrixTransform()
            small_tr.translate(pos)
            small_sphere.transform = small_tr
            small_sphere.set_gl_state('opaque', depth_test=False)
            small_sphere.order = 3
            self.mesh_nodes[name]["small_sphere"] = small_sphere

    def update_handle_positions(self, scale):
        # Update all handles
        for name, data in self.mesh_nodes.items():
            if name.startswith('r'):
                continue
            pos = None
            if name.startswith('t') or name.startswith('s') or name.startswith('r'):
                offset = data.get("offset", 0.0)
                axis_letters = name[1:]
                corner = np.zeros(3, dtype=float)
                for letter in axis_letters:
                    idx = {'x':0, 'y':1, 'z':2}[letter]
                    corner[idx] = scale[idx]
                if np.linalg.norm(corner) < 1e-9:
                    dir = np.zeros(3)
                else:
                    dir = normalize(corner)
                pos = corner + dir * offset
            
            if pos is not None:
                data['position'] = pos  # Store the authoritative position
                tr = MatrixTransform()
                tr.translate(pos)
                data['mesh'].transform = tr
                if "hit_sphere" in data:
                    sphere_tr = MatrixTransform()
                    sphere_tr.translate(pos)
                    data["hit_sphere"].transform = sphere_tr
                if "small_sphere" in data:
                    small_tr = MatrixTransform()
                    small_tr.translate(pos)
                    data["small_sphere"].transform = small_tr

    def highlight(self, axis_name):
        for name, data in self.mesh_nodes.items():
            is_hovered = (name == axis_name)
            mesh = data["mesh"]

            # Determine scale and color based on hover state
            transform_scale = 1.4 if is_hovered else 1.0
            sphere_scale = 1.15 if is_hovered else 1.0
            sphere_color = self.SPHERE_COLOR_HOVER if is_hovered else self.SPHERE_COLOR_DEFAULT

            pos = data["position"]

            # Apply transform to handle mesh
            tr = MatrixTransform()
            tr.scale((transform_scale, transform_scale, transform_scale))
            tr.translate(pos)
            mesh.transform = tr

            # Apply transform and color to hit sphere
            if "hit_sphere" in data:
                sphere_tr = MatrixTransform()
                sphere_tr.scale((sphere_scale, sphere_scale, sphere_scale))
                sphere_tr.translate(pos)
                data["hit_sphere"].transform = sphere_tr
                data["hit_sphere"].mesh.color = sphere_color

            if "small_sphere" in data:
                small_tr = MatrixTransform()
                small_tr.translate(pos)
                data["small_sphere"].transform = small_tr


def screen_to_world_ray(view, screen_xy):
    x,y = screen_xy
    p_screen_near = np.array([x, y, 0.0, 1.0], dtype=float)
    p_screen_far  = np.array([x, y, 1.0, 1.0], dtype=float)
    tform = view.scene.transform
    p_near_world = tform.imap(p_screen_near)
    p_far_world  = tform.imap(p_screen_far)
    if abs(p_near_world[3]) > 1e-12:
        p_near_world = p_near_world[:3] / p_near_world[3]
    else:
        p_near_world = p_near_world[:3]
    if abs(p_far_world[3]) > 1e-12:
        p_far_world = p_far_world[:3] / p_far_world[3]
    else:
        p_far_world = p_far_world[:3]
    origin = p_near_world
    direction = normalize(p_far_world - p_near_world)
    return origin, direction

def ray_intersect_sphere(ray_origin, ray_dir, center, radius):
    L = center - ray_origin
    t_ca = np.dot(L, ray_dir)
    d2 = np.dot(L, L) - t_ca * t_ca
    r2 = radius * radius
    if d2 > r2:
        return False, None, None
    thc = math.sqrt(max(0.0, r2 - d2))
    t0 = t_ca - thc
    t1 = t_ca + thc
    t = None
    if t0 >= 0:
        t = t0
    elif t1 >= 0:
        t = t1
    else:
        return False, None, None
    p = ray_origin + ray_dir * t
    return True, t, p

def closest_point_between_ray_and_line(L0, u, origin, v):
    u = normalize(u); v = normalize(v)
    w0 = L0 - origin
    a = np.dot(u,u); b = np.dot(u,v); c = np.dot(v,v)
    d = np.dot(u,w0); e = np.dot(v,w0)
    D = a*c - b*b
    if abs(D) < 1e-9:
        s = np.dot(origin - L0, u)
        point = L0 + u*s
        return s, point
    s = (b*e - c*d) / D
    point = L0 + u*s
    return s, point


class GizmoController:
    _handle_groups = {
        'r': ['rxy', 'ryz', 'rzx'],
        't': ['tx', 'ty', 'tz', 'txy', 'tyz', 'tzx'],
        's': ['sx', 'sy', 'sz', 'sxy', 'syz', 'szx'],
        'all': ['rxy', 'ryz', 'rzx', 'tx', 'ty', 'tz', 'txy', 'tyz', 'tzx', 'sx', 'sy', 'sz', 'sxy', 'syz', 'szx'],
    }

    def __init__(self, view, canvas, renderer: GizmoRenderer, rotation: Rotation):
        self.view = view
        self.canvas = canvas
        self.renderer = renderer
        self.rotation = rotation
        self._hover_axis = None
        self._dragging = False
        self._drag_axis = None
        self._drag_mode = None
        
        # Drag state variables
        self._start_vec = None
        self._fixed_normal = None
        self._start_axis_pos = 0.0
        self._start_plane_pos = None
        self._drag_axis_dir = None
        self._drag_plane_normal = None
        self._initial_handle_pos = 0.0
        self._cumulative_angle = 0.0
        
        self._uniform_scale_mode = True

        # Object properties
        self._ring_center = np.array([0.0, 0.0, 0.0], dtype=float)
        self._object_translation = np.array([0.0, 0.0, 0.0], dtype=float)
        self._object_scale = np.array([1.0, 1.0, 1.0], dtype=float)
        self._original_translation = self._object_translation.copy()
        self._original_scale = self._object_scale.copy()
        
        self._tolerance = 0.12
        self._radius = renderer._radius if hasattr(renderer, '_radius') else 1.4

        self._enabled_handles = set()
        self.set_handles(['all'])
        
        self.on_update = None

    def uniform_scale(self, mode=True):
        self._uniform_scale_mode = mode

    def set_handles(self, handles):
        self._enabled_handles.clear()
        for h in handles:
            if h in self._handle_groups:
                self._enabled_handles.update(self._handle_groups[h])
            elif h in self.renderer.mesh_nodes:
                self._enabled_handles.add(h)
        for name, data in self.renderer.mesh_nodes.items():
            if name in self._enabled_handles:
                data["mesh"].parent = self.renderer.parent
                data["mesh"].visible = True
                if "hit_sphere" in data:
                    data["hit_sphere"].parent = self.renderer.parent
                    data["hit_sphere"].visible = True
                if "small_sphere" in data:
                    data["small_sphere"].parent = self.renderer.parent
                    data["small_sphere"].visible = True
            else:
                data["mesh"].parent = None
                if "hit_sphere" in data:
                    data["hit_sphere"].parent = None
                if "small_sphere" in data:
                    data["small_sphere"].parent = None


    def set_scale(self, scale, reset_originals=True):
        self._object_scale = np.array(scale, dtype=float)
        if reset_originals:
            self._original_scale = self._object_scale.copy()
        self.renderer.update_handle_positions(self._object_scale)

    def _start_drag_rotate(self, data, origin, direction):
        if "axis" in data:
            self._fixed_normal = normalize(data["axis"])
        else:
            axis1, axis2 = data["axes"]
            self._fixed_normal = normalize(np.cross(axis1, axis2))
        ndotd = np.dot(self._fixed_normal, direction)
        if abs(ndotd) < 1e-8: return
        t = np.dot(self._ring_center - origin, self._fixed_normal) / ndotd
        p = origin + direction * t
        vec = p - self._ring_center
        self._start_vec = normalize(vec - np.dot(vec, self._fixed_normal) * self._fixed_normal)
        self._cumulative_angle = 0.0

    def _start_drag_translate(self, data, origin, direction):
        self._original_translation = self._object_translation.copy()
        self._start_plane_pos = None
        self._drag_plane_normal = None
        self._drag_axis_dir = None
        if "axis" in data:
            self._drag_axis_dir = normalize(data["axis"])
            s, _ = closest_point_between_ray_and_line(self._ring_center, self._drag_axis_dir, origin, direction)
            self._start_axis_pos = s
        else:
            axis1, axis2 = data["axes"]
            self._drag_plane_normal = normalize(np.cross(axis1, axis2))
            ndotd = np.dot(self._drag_plane_normal, direction)
            if abs(ndotd) < 1e-8: return
            t = np.dot(self._ring_center - origin, self._drag_plane_normal) / ndotd
            self._start_plane_pos = origin + direction * t

    def _start_drag_scale(self, data, origin, direction):
        self._original_scale = self._object_scale.copy()
        if "axis" in data:
            self._drag_axis_dir = normalize(data["axis"])
        else:
            axis1, axis2 = data["axes"]
            self._drag_axis_dir = normalize(axis1 + axis2)
        initial_handle_pos_vec = data["position"]
        self._initial_handle_pos = np.dot(initial_handle_pos_vec, self._drag_axis_dir)
        s, _ = closest_point_between_ray_and_line(self._ring_center, self._drag_axis_dir, origin, direction)
        self._start_axis_pos = s

    def _handle_drag_rotate(self, origin, direction):    # --- Mouse Move Helpers (Handling an Active Drag) ---
        ndotd = np.dot(self._fixed_normal, direction)
        if abs(ndotd) < 1e-8: return
        t = np.dot(self._ring_center - origin, self._fixed_normal) / ndotd
        p = origin + direction * t
        
        vec = p - self._ring_center
        cur_vec = normalize(vec - np.dot(vec, self._fixed_normal) * self._fixed_normal)

        if np.linalg.norm(cur_vec) < 1e-6 or np.linalg.norm(self._start_vec) < 1e-6: return

        dp = np.clip(np.dot(self._start_vec, cur_vec), -1.0, 1.0)
        angle_delta_rad = math.acos(dp)
        
        cross = np.cross(self._start_vec, cur_vec)
        if np.dot(cross, self._fixed_normal) < 0.0:
            angle_delta_rad = -angle_delta_rad
        
        # This is the core logic that rotates the object's state
        self.rotation.rotate_around_local_axis(self._fixed_normal, -math.degrees(angle_delta_rad))
        self._cumulative_angle += angle_delta_rad

        # Update the visual feedback for the gizmo handle during rotation drag
        deg = math.degrees(self._cumulative_angle)
        delta_rotation = ScipyRotation.from_rotvec(self._fixed_normal * self._cumulative_angle)
        data = self.renderer.mesh_nodes[self._drag_axis]
        pos = data["position"]
        rotated_pos = delta_rotation.apply(pos)

        transform_scale = 1.4
        tr = MatrixTransform()
        tr.scale((transform_scale, transform_scale, transform_scale))
        tr.rotate(deg, self._fixed_normal)
        tr.translate(rotated_pos)
        data["mesh"].transform = tr

        sphere_scale = 1.15
        sphere_color = self.renderer.SPHERE_COLOR_HOVER
        sphere_tr = MatrixTransform()
        sphere_tr.scale((sphere_scale, sphere_scale, sphere_scale))
        sphere_tr.rotate(deg, self._fixed_normal)
        sphere_tr.translate(rotated_pos)
        data["hit_sphere"].transform = sphere_tr
        data["hit_sphere"].mesh.color = sphere_color

        if "small_sphere" in data:
            small_tr = MatrixTransform()
            small_tr.rotate(deg, self._fixed_normal)
            small_tr.translate(rotated_pos)
            data["small_sphere"].transform = small_tr

        self._start_vec = cur_vec

    def _handle_drag_translate(self, origin, direction):
        if self._drag_axis_dir is not None: # Linear
            s_cur, _ = closest_point_between_ray_and_line(self._original_translation, self._drag_axis_dir, origin, direction)
            delta_s = s_cur - self._start_axis_pos
            self._object_translation = self._original_translation + self._drag_axis_dir * delta_s
        elif self._drag_plane_normal is not None: # Planar
            ndotd = np.dot(self._drag_plane_normal, direction)
            if abs(ndotd) < 1e-8: return
            t = np.dot(self._ring_center - origin, self._drag_plane_normal) / ndotd
            if t < 0: return
            p_cur = origin + direction * t
            delta = p_cur - self._start_plane_pos
            self._object_translation = self._original_translation + delta
        
        self._ring_center = self._object_translation

    def _handle_drag_scale(self, origin, direction):
        s_cur, _ = closest_point_between_ray_and_line(self._ring_center, self._drag_axis_dir, origin, direction)
        delta_s = s_cur - self._start_axis_pos
        
        new_projected_pos = self._initial_handle_pos + delta_s
        scale_factor = new_projected_pos / self._initial_handle_pos if self._initial_handle_pos != 0 else 1.0
        scale_factor = max(0.01, scale_factor)

        new_scale = self._original_scale.copy()
        if self._uniform_scale_mode:
            new_scale *= scale_factor
        elif len(self._drag_axis) == 2: # Linear 'sx', 'sy', 'sz'
            axis_idx = {'x':0, 'y':1, 'z':2}[self._drag_axis[1]]
            new_scale[axis_idx] *= scale_factor
        else: # Planar 'sxy', 'syz', 'szx'
            axis_letters = self._drag_axis[1:]
            for letter in axis_letters:
                axis_idx = {'x':0, 'y':1, 'z':2}[letter]
                new_scale[axis_idx] *= scale_factor
        
        self.set_scale(new_scale, reset_originals=False)
        
    def handle_mouse_press(self, event):    # --- Main Event Handlers ---
        if event.button not in [1, 2, 3]:  # Allow left, right, and middle click
            return
        

        origin, direction = screen_to_world_ray(self.view, event.pos)
        candidates = self._get_candidates(origin, direction)
        if not candidates: return

        candidates.sort(key=lambda x: x[0])
        _, self._drag_axis, self._drag_mode, picked_p = candidates[0]
        
        # Check for alternative drag modes on translate handles
        if self._drag_axis.startswith('t'):
            if event.button == 2: # Right-click -> Scale
                self._drag_mode = 'scale'
            elif event.button == 3: # Middle-click -> Rotate
                self._drag_mode = 'rotate'

        # If not a primary action, ignore
        if self._drag_mode == 'translate' and event.button != 1:
            return
        
        self._dragging = True
        
        if key_check("ctrl"):
            print("press", event.button, self._ring_center, file=sys.stderr)
            viewport = self.canvas.native.parent()
            viewport._objectManager.duplicate_selected()
    
        data = self.renderer.mesh_nodes[self._drag_axis]
        
        # Call the appropriate helper to initialize the drag
        if self._drag_mode == 'rotate':
            self._start_drag_rotate(data, origin, direction)
        elif self._drag_mode == 'translate':
            self._start_drag_translate(data, origin, direction)
        elif self._drag_mode == 'scale':
            self._start_drag_scale(data, origin, direction)

        self.renderer.highlight(self._drag_axis)        # Update visuals
        for name, node_data in self.renderer.mesh_nodes.items():
            if name != self._drag_axis:
                node_data["mesh"].parent = None
                if "hit_sphere" in node_data:
                    node_data["hit_sphere"].parent = None
                if "small_sphere" in node_data:
                    node_data["small_sphere"].parent = None
        
        event.handled = True

    def handle_mouse_move(self, event):

        origin, direction = screen_to_world_ray(self.view, event.pos)

        if self._dragging:# Call the appropriate helper to handle the drag update

            if self._drag_mode == 'rotate': self._handle_drag_rotate(origin, direction)
            elif self._drag_mode == 'translate': self._handle_drag_translate(origin, direction)
            elif self._drag_mode == 'scale': self._handle_drag_scale(origin, direction)
            event.handled = True
            self.canvas.update()
            return

        candidates = self._get_candidates(origin, direction)# Hover detection when not dragging
        picked_name = candidates[0][1] if candidates else None
        
        if self._hover_axis != picked_name:
            if picked_name is not None:
                play_sound("hover")
                set_cursor("arrows-move", 'center')
            else:
                set_cursor("cursor")
            self._hover_axis = picked_name
            self.renderer.highlight(picked_name)

    def handle_mouse_release(self, event):
        if self._dragging:
            if self._drag_mode == 'scale':
                self.set_scale(self._object_scale, reset_originals=True)
            self._dragging = False
            self._drag_axis = None
            self._drag_mode = None
            # Reset temporary drag state variables
            self._start_vec = self._fixed_normal = self._start_plane_pos = None
            self._drag_axis_dir = self._drag_plane_normal = None
            self._cumulative_angle = 0.0
            
            self.renderer.highlight(self._hover_axis) # Highlight what's currently hovered
            self.restore_visibility()
            event.handled = True


    def get_visibility(self, mode):
        _handle_groups = {
            'move': ['tx', 'ty', 'tz', 'txy', 'tyz', 'tzx'],  # Translation
            'rotate': ['rxy', 'ryz', 'rzx'],                     # Rotation
            'scale': ['sx', 'sy', 'sz', 'sxy', 'syz', 'szx'], # Scale
        }
        if mode not in _handle_groups:
            return False
        return bool(self._enabled_handles.intersection(_handle_groups[mode]))


    def _get_candidates(self, origin, direction):
        candidates = []
        for name in self.renderer.mesh_nodes:
            if name not in self._enabled_handles: continue
            data = self.renderer.mesh_nodes[name]
            center = self._ring_center + data.get('position', np.zeros(3))

            hit, t, p = ray_intersect_sphere(origin, direction, center, 0.3)
            if hit:
                if name.startswith('r'):
                    mode = 'rotate'
                elif name.startswith('s'):
                    mode = 'scale'
                else:
                    mode = 'translate'
                candidates.append((t, name, mode, p))
        return candidates

    ### MODIFIED ###
    def handle_mouse_wheel(self, event):
        # Allow mouse wheel rotation during a translate or scale drag operation.
        if not self._dragging or self._drag_mode not in ['translate', 'scale']:
            return
        
        delta = event.delta[1]
        if delta == 0:
            return
        
        # Determine rotation amount and the handle being dragged
        angle_deg = 15 * (1 if delta > 0 else -1)
        data = self.renderer.mesh_nodes[self._drag_axis]
        
        # Determine the axis of rotation from the handle
        if "axis" in data:  # Linear handle (tx, sx, etc.)
            axis = data["axis"]
        else:  # Planar handle (txy, sxy, etc.)
            axis1, axis2 = data["axes"]
            axis = normalize(np.cross(axis1, axis2))
        
        # Apply rotation and update the scene
        self.rotation.rotate_around_local_axis(axis, angle_deg)
        if self.on_update:
            self.on_update()
        self.canvas.update()
        event.handled = True

    def restore_visibility(self):
        for name, data in self.renderer.mesh_nodes.items():
            if name in self._enabled_handles:
                data["mesh"].parent = self.renderer.parent
                data["mesh"].visible = True
                if "hit_sphere" in data:
                    data["hit_sphere"].parent = self.renderer.parent
                    data["hit_sphere"].visible = True
                if "small_sphere" in data:
                    data["small_sphere"].parent = self.renderer.parent
                    data["small_sphere"].visible = True

# =======================================================================
# IMPORTANT:
# Everything ABOVE this line is part of the reusable "gizmo.py" module.
# That code is safe to import into the main application.
#
# Everything BELOW this line is ONLY a self-contained test/demo harness.
# It exists solely to run "gizmo.py" in isolation for debugging or
# experimentation. None of the functions, variables, or classes defined
# below (e.g. `cube_node`, `cube_parent`, or the Qt main loop) should
# ever be referenced or relied upon by the main app or by the reusable
# classes above. Treat this as disposable demo code.
# =======================================================================
testing = True
if testing:
    def create_cube_node(parent, size=(2.0,2.0,2.0), color=(0.4,0.5,0.6,1.0), edge_color='black'):
        sx, sy, sz = float(size[0]), float(size[1]), float(size[2])
        try:
            cube = scene.visuals.Box(sx, sy, sz, color=color, edge_color=edge_color, parent=parent)
            return cube
        except Exception:
            pass
        hx, hy, hz = sx*0.5, sy*0.5, sz*0.5
        verts = np.array([
            [-hx,-hy,-hz],[ hx,-hy,-hz],[ hx, hy,-hz],[-hx, hy,-hz],
            [-hx,-hy, hz],[ hx,-hy, hz],[ hx, hy, hz],[-hx, hy, hz]
        ], dtype=float)
        faces = np.array([[0,1,2],[0,2,3],[4,6,5],[4,7,6],[0,4,5],[0,5,1],[2,6,7],[2,7,3],[1,5,6],[1,6,2],[0,3,7],[0,7,4]], dtype=np.int32)
        cube = scene.visuals.Mesh(vertices=verts, faces=faces, color=color, parent=parent)
        return cube

    def create_grid(parent, size=10, spacing=1.0, color=(0.6,0.6,0.6,0.6)):
        node = scene.Node(parent=parent)
        segs = []
        for i in range(-size, size+1):
            segs.append(np.array([[i*spacing, 0.0, -size*spacing],[i*spacing, 0.0, size*spacing]]))
            segs.append(np.array([[-size*spacing, 0.0, i*spacing],[size*spacing, 0.0, i*spacing]]))
        verts = np.vstack(segs)
        lines = scene.visuals.Line(pos=verts, connect='segments', parent=node)
        try:
            lines.set_gl_state('translucent', depth_test=False)
        except Exception:
            pass
        lines.antialias = 0
        return node


    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
    import sys

    def main():
        app_qt = QApplication(sys.argv)

        # create main window
        win = QWidget()
        layout = QVBoxLayout(win)

        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        # create vispy canvas
        canvas = scene.SceneCanvas(keys='interactive', size=(800, 600), bgcolor='black', parent=win)
        layout.addWidget(canvas.native)  # embed vispy canvas into Qt

        view = canvas.central_widget.add_view()
        view.camera = scene.cameras.TurntableCamera(parent=view.scene, fov=45.0,
                                                   distance=8.0, interactive=True, up="Y")

        # grid
        grid_node = create_grid(parent=view.scene, size=12, spacing=0.5)

        # object hierarchy
        cube_parent = scene.Node(parent=view.scene)
        cube_node = scene.Node(parent=cube_parent)
        cube_visual = create_cube_node(parent=cube_node)
        cube_node.transform = MatrixTransform()
        cube_parent.transform = MatrixTransform()

        # gizmo
        gizmo_node = scene.Node(parent=view.scene)
        rot = Rotation()
        renderer = GizmoRenderer(parent_node=gizmo_node, radius=1.45,
                                 base_thickness=0.06, segments=10, parent_view=view)
        controller = GizmoController(view=view, canvas=canvas,
                                     renderer=renderer, rotation=rot)

        def update_transforms():
            R = rot.get_matrix()
            S = np.eye(4, dtype=float)
            S[0,0] = controller._object_scale[0]
            S[1,1] = controller._object_scale[1]
            S[2,2] = controller._object_scale[2]
            
            # FIX: Swapped matrix order to resolve skewing issue.
            # This forces the scale to be applied before the rotation.
            cube_node.transform.matrix = (S @ R).astype(np.float32)

            tr_parent = MatrixTransform()
            tr_parent.translate(controller._object_translation)
            cube_parent.transform = tr_parent
            tr = MatrixTransform()
            tr.translate(controller._object_translation)
            renderer.parent.transform = tr

        controller.on_update = update_transforms

        # connect events
        @canvas.events.mouse_press.connect
        def on_mouse_press(event):
            controller.handle_mouse_press(event)

        @canvas.events.mouse_move.connect
        def on_mouse_move(event):
            controller.handle_mouse_move(event)
            update_transforms()
            view.camera.interactive = not controller._dragging

        @canvas.events.mouse_release.connect
        def on_mouse_release(event):
            controller.handle_mouse_release(event)
            view.camera.interactive = True

        @canvas.events.mouse_wheel.connect
        def on_mouse_wheel(event):
            controller.handle_mouse_wheel(event)

        # add 3 buttons
        trans_on = QPushButton("Translate ON")
        rot_on = QPushButton("Rotate ON")
        scale_on = QPushButton("Scale ON")


        trans_on.clicked.connect(lambda: controller.set_handles(['t'])  )
        rot_on.clicked.connect(lambda:   controller.set_handles(['r'])  )
        scale_on.clicked.connect(lambda: controller.set_handles(['s'])  ) 


        btn_layout.addWidget(trans_on)
        btn_layout.addWidget(rot_on)
        btn_layout.addWidget(scale_on)

        win.show()

        sys.exit(app_qt.exec())

    if __name__ == '__main__':
        main()