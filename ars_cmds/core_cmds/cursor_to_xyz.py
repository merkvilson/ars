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

def get_xyz(ars_window):
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

    # Check for object intersection via picking
    picked_idx = viewport._objectManager.picking().pick_at(x, y)
    
    closest_point = None
    
    if picked_idx is not None:
        try:
            obj = viewport._objectManager._objects[picked_idx]
            
            # Transform ray from World Space to Object Local Space
            # We manually traverse the transform hierarchy (World -> Node -> Local)
            # to avoid issues with Vispy's get_transform in SubScenes.
            
            # World -> Node (Translation)
            p_node_origin = obj.visual.transform.imap(ray_origin)
            p_node_point = obj.visual.transform.imap(ray_origin + ray_dir)
            
            # Node -> Local (Rotation/Scale)
            local_origin = obj._visual.transform.imap(p_node_origin)[:3]
            local_point_on_ray = obj._visual.transform.imap(p_node_point)[:3]
            
            local_dir = local_point_on_ray - local_origin
            
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
                        p_node = obj._visual.transform.map(p_local)
                        p_world = obj.visual.transform.map(p_node)[:3]
                        
                        closest_point = p_world

        except Exception as e:
            print(f"Error intersecting object: {e}")
            pass

    if closest_point is not None:
        return (closest_point[0], closest_point[1], closest_point[2])

    # Fallback: Intersection with the ground plane (Y=0)
    if abs(ray_dir[1]) > 1e-6:
        t = -ray_origin[1] / ray_dir[1]
        if t > 0:
            grid_pos = ray_origin + t * ray_dir
            return (grid_pos[0], grid_pos[1], grid_pos[2])
            
    return None
