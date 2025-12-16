from PyQt6.QtGui import QCursor
import numpy as np
from ars_3d_engine.gizmo.gizmo import screen_to_world_ray

def ray_triangle_intersection(ray_origin, ray_dir, v0, v1, v2):
    """
    Calculates the intersection of a ray with a set of triangles using the Möller-Trumbore algorithm.
    
    Args:
        ray_origin (np.array): Origin of the ray.
        ray_dir (np.array): Direction of the ray.
        v0, v1, v2 (np.array): Vertices of the triangles.
        
    Returns:
        float or None: The distance to the closest intersection, or None if no intersection.
    """
    epsilon = 1e-6
    edge1 = v1 - v0
    edge2 = v2 - v0
    h = np.cross(ray_dir, edge2)
    a = np.einsum('ij,ij->i', edge1, h)
    
    mask = np.abs(a) > epsilon
    if not np.any(mask):
        return None
        
    f = 1.0 / a[mask]
    s = ray_origin - v0[mask]
    u = f * np.einsum('ij,ij->i', s, h[mask])
    
    mask_u = (u >= 0.0) & (u <= 1.0)
    if not np.any(mask_u):
        return None
        
    q = np.cross(s, edge1[mask])
    v = f * np.einsum('j,ij->i', ray_dir, q)
    
    mask_v = (v >= 0.0) & (u + v <= 1.0)
    if not np.any(mask_v):
        return None
        
    t = f * np.einsum('ij,ij->i', edge2[mask], q)
    mask_t = (t > epsilon)
    
    final_mask = mask_u & mask_v & mask_t
    
    if np.any(final_mask):
        valid_t = t[final_mask]
        return np.min(valid_t)
        
    return None

def get_xyz(ars_window, ignore_objs=None, callback_object=None, callback_background=None, callback_grid=None):
    """
    Calculates the 3D world coordinates of the point under the mouse cursor.
    Checks for intersection with scene objects first, then falls back to the ground plane (Y=0).
    
    Args:
        ars_window: The main application window instance.
        
    Returns:
        tuple: (x, y, z) coordinates of the intersection point, or None.
    """
    viewport = ars_window.viewport
    canvas = viewport._canvas
    view = viewport._view
    
    # Get mouse position in widget coordinates
    global_pos = QCursor.pos()
    widget_pos = canvas.native.mapFromGlobal(global_pos)
    x, y = widget_pos.x(), widget_pos.y()
    
    try:
        ray_origin, ray_dir = screen_to_world_ray(view, (x, y))
    except Exception as e:
        print(f"Error calculating ray: {e}")
        return None

    # Handle ignore_objs
    hidden_objects = []
    if ignore_objs:
        for obj in ignore_objs:
            if hasattr(obj, 'visual') and obj.visual.visible:
                obj.visual.visible = False
                hidden_objects.append(obj)

    # Check for object intersection via picking
    try:
        picked_idx = viewport._objectManager.picking().pick_at(x, y)
    finally:
        # Restore visibility
        for obj in hidden_objects:
            obj.visual.visible = True
    
    closest_point = None
    
    if picked_idx is not None:
        try:
            obj = viewport._objectManager._objects[picked_idx]
            
            # Build transform chain from Mesh Visual up to Scene Root
            # This handles arbitrary hierarchy depth (Child -> Parent -> ... -> World)
            chain = []
            # Start with the visual that holds the mesh (Rotation/Scale node)
            current = obj._visual 
            
            # Traverse up
            while current is not None and current != view.scene:
                chain.append(current)
                current = current.parent
            
            # Calculate World Matrix (Row-Major: v_world = v_local @ M)
            world_matrix = np.eye(4, dtype=np.float32)
            for node in chain:
                if hasattr(node, 'transform') and hasattr(node.transform, 'matrix'):
                    world_matrix = world_matrix @ node.transform.matrix
            
            try:
                inv_world_matrix = np.linalg.inv(world_matrix)
            except np.linalg.LinAlgError:
                raise Exception("Singular matrix")

            # Transform Ray to Local Space
            # Origin
            ro_4 = np.append(ray_origin, 1.0)
            ro_local = ro_4 @ inv_world_matrix
            local_origin = ro_local[:3] / ro_local[3]

            # Direction (using point + dir to handle perspective correctly if needed)
            rd_point_4 = np.append(ray_origin + ray_dir, 1.0)
            rd_local = rd_point_4 @ inv_world_matrix
            local_point = rd_local[:3] / rd_local[3]
            local_dir = local_point - local_origin
            
            if hasattr(obj, '_visual') and hasattr(obj._visual, 'mesh_data') and obj._visual.mesh_data is not None:
                md = obj._visual.mesh_data
                vertices = md.get_vertices()
                faces = md.get_faces()
                
                if vertices is not None and faces is not None:
                    v0 = vertices[faces[:, 0]]
                    v1 = vertices[faces[:, 1]]
                    v2 = vertices[faces[:, 2]]
                    
                    t = ray_triangle_intersection(local_origin, local_dir, v0, v1, v2)
                    
                    if t is not None:
                        p_local = local_origin + t * local_dir
                        
                        # Transform intersection point back to World Space
                        p_local_4 = np.append(p_local, 1.0)
                        p_world_4 = p_local_4 @ world_matrix
                        closest_point = p_world_4[:3] / p_world_4[3]

        except Exception as e:
            print(f"Error intersecting object: {e}")
            pass

    if closest_point is not None: # Intersection with an object
        if callback_object:
            callback_object(obj)
        return (closest_point[0], closest_point[1], closest_point[2])

   
    if abs(ray_dir[1]) > 1e-6: # Fallback: Intersection with the ground plane (Y=0)
        t = -ray_origin[1] / ray_dir[1]
        if t > 0:
            if callback_grid:
                callback_grid()
            grid_pos = ray_origin + t * ray_dir
            return (grid_pos[0], grid_pos[1], grid_pos[2])
            
    if callback_background:
        callback_background()
    return None