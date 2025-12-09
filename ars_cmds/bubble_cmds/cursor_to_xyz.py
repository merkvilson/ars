from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
import numpy as np
from ars_3d_engine.gizmo.gizmo import screen_to_world_ray
from ars_cmds.core_cmds.load_object import selected_object

BBL_CURSOR_XYZ_CONFIG = {"symbol": ic.ICON_OBJ_CIRCLE, "hotkey": "X"}

def BBL_CURSOR_XYZ(*args):
    run_ext(__file__)

def ray_triangle_intersection(ray_origin, ray_dir, v0, v1, v2):
    # Vectorized Möller-Trumbore intersection algorithm
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
    viewport = ars_window.viewport
    canvas = viewport._canvas
    view = viewport._view
    
    # 1. Get Mouse Position
    global_pos = QCursor.pos()
    widget_pos = canvas.native.mapFromGlobal(global_pos)
    x, y = widget_pos.x(), widget_pos.y()
    
    # 2. Calculate Ray in World Space using Gizmo's robust method
    try:
        # screen_to_world_ray uses view.scene.transform to unproject
        # This gives us the ray in the Scene coordinate system (World)
        ray_origin, ray_dir = screen_to_world_ray(view, (x, y))
    except Exception as e:
        print(f"Error calculating ray: {e}")
        return None

    # 3. Check Picking
    picked_idx = viewport._objectManager.picking().pick_at(x, y)
    
    closest_point = None
    
    if picked_idx is not None:
        try:
            obj = viewport._objectManager._objects[picked_idx]
            
            # Manual transform from World (view.scene) to Local (obj._visual)
            # Avoid using get_transform(map_from=...) as it can be flaky with SubScenes
            
            # 1. World -> Node (obj.visual)
            # obj.visual.transform maps Node -> World, so imap maps World -> Node
            # We use imap (inverse map) to go down the hierarchy
            p_node_origin = obj.visual.transform.imap(ray_origin)
            p_node_point = obj.visual.transform.imap(ray_origin + ray_dir)
            
            # 2. Node -> Local (obj._visual)
            # obj._visual.transform maps Local -> Node, so imap maps Node -> Local
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
                        # Calculate point in Local Space
                        p_local = local_origin + t * local_dir
                        
                        # Transform back to World Space manually
                        # 1. Local -> Node
                        p_node = obj._visual.transform.map(p_local)
                        
                        # 2. Node -> World
                        p_world = obj.visual.transform.map(p_node)[:3]
                        
                        closest_point = p_world

        except Exception as e:
            print(f"Error intersecting object: {e}")
            pass

    if closest_point is not None:
        return (closest_point[0], closest_point[1], closest_point[2])

    # 4. Fallback to Grid Intersection (Y=0 plane)
    # Ray P = O + t*D
    # P.y = 0 => O.y + t*D.y = 0 => t = -O.y / D.y
    if abs(ray_dir[1]) > 1e-6:
        t = -ray_origin[1] / ray_dir[1]
        # Allow t > 0 (forward)
        # Also check if intersection is within reasonable bounds if needed
        if t > 0:
            grid_pos = ray_origin + t * ray_dir
            return (grid_pos[0], grid_pos[1], grid_pos[2])
            
    return None

def execute_cmd(ars_window):
    obj = selected_object()
    if not obj:
        print("No object selected")
        return
    xyz = get_xyz(ars_window)
    if xyz:
        print(f"XYZ: {xyz}")
        obj.set_position(*xyz)
    else:
        print("No intersection found")
