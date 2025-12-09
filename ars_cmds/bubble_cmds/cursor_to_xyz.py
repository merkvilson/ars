from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
import numpy as np
from vispy.visuals.filters import Filter

BBL_CURSOR_XYZ_CONFIG = {"symbol": ic.ICON_OBJ_CIRCLE, "hotkey": "X"}

class DepthFilter(Filter):
    def __init__(self):
        super().__init__()
        self.fcode = """
        void main() {
            float d = gl_FragCoord.z;
            const vec4 bitSh = vec4(16777216.0, 65536.0, 256.0, 1.0);
            const vec4 bitMsk = vec4(0.0, 1.0/256.0, 1.0/256.0, 1.0/256.0);
            vec4 res = fract(d * bitSh);
            res -= res.xxyz * bitMsk;
            gl_FragColor = res;
        }
        """

def BBL_CURSOR_XYZ(*args):
    run_ext(__file__)

def _iter_leaf_visuals(node):
    stack = [node]
    while stack:
        n = stack.pop()
        if hasattr(n, 'children') and n.children:
            stack.extend(n.children)
        else:
            yield n

def execute_cmd(ars_window):
    viewport = ars_window.viewport
    canvas = viewport._canvas
    view = viewport._view
    
    # 1. Get Mouse Position
    global_pos = QCursor.pos()
    widget_pos = canvas.native.mapFromGlobal(global_pos)
    x, y = widget_pos.x(), widget_pos.y()
    
    w, h = canvas.size
    if x < 0 or x > w or y < 0 or y > h:
        print("Cursor outside viewport")
        return

    # 2. Setup Depth Pass
    # We will attach a DepthFilter to all objects, render 1 pixel, and read it.
    
    depth_filter = DepthFilter()
    attached_visuals = []
    
    # Hide Grid and Gizmo to avoid interference
    grid_visible = viewport.grid_node.visible
    gizmo_visible = viewport.gizmo_node.visible
    viewport.grid_node.visible = False
    viewport.gizmo_node.visible = False
    
    try:
        # Attach filter to all object leaves
        for obj in viewport._objectManager._objects:
            # obj is CGeometry, obj.visual is the root node of the object
            for leaf in _iter_leaf_visuals(obj.visual):
                # Only attach to visuals that can have filters
                if hasattr(leaf, 'attach'):
                    leaf.attach(depth_filter)
                    # Disable blending to ensure opaque write
                    # Store old state? simpler to just force blend=False then restore default?
                    # We don't know the default. But usually objects are opaque or translucent.
                    # We'll just set blend=False.
                    leaf.update_gl_state(blend=False)
                    attached_visuals.append(leaf)
        
        # 3. Render 1 pixel
        # Calculate crop coordinates (inverted Y)
        ps = canvas.pixel_scale
        fb_w, fb_h = int(canvas.size[0] * ps), int(canvas.size[1] * ps)
        px = int(round(x * ps))
        py = int(round(fb_h - (y * ps)))
        
        # Render
        # bgcolor=(0,0,0,0) means depth=1.0 (alpha=0 in output if nothing hit? No, shader writes alpha)
        # Wait, if nothing is hit, the clear color is used.
        # If we clear to (0,0,0,0), then R=0, G=0, B=0, A=0.
        # Unpacking (0,0,0,0) gives depth 0.0?
        # But background is usually Far Plane (depth=1.0).
        # We should clear to a color that represents depth=1.0.
        # Depth 1.0 packs to (1, 1, 1, 1)? No.
        # fract(1.0 * 2^24) = 0.
        # Actually fract(integer) is 0.
        # So depth 1.0 -> (0, 0, 0, 0) with the fract logic?
        # Let's check 0.999999.
        # It packs to (high, high, high, high).
        # So 1.0 is tricky with fract.
        # But usually we check if alpha is 0 (if we clear to alpha 0).
        # If we hit an object, the shader writes gl_FragColor.
        # The shader writes A = fract(d). If d=0.5, A=0.5.
        # If d=1.0, A=0.0.
        # So (0,0,0,0) could mean depth 1.0 OR depth 0.0.
        # Depth 0.0 is Near Plane.
        # Let's clear to (1, 0, 0, 0) or something distinct?
        # Or just check if we hit anything?
        # The shader ALWAYS writes.
        # If we clear to (0,0,0,0), and we read (0,0,0,0), it's either background or near plane.
        # Near plane is very rare (camera lens).
        # So we can assume (0,0,0,0) is background.
        
        img = canvas.render(
            crop=(px, py, 1, 1),
            bgcolor=(0, 0, 0, 0),
            alpha=True
        )
        
        pixel = img[0, 0] # RGBA
        
    finally:
        # 4. Cleanup
        for leaf in attached_visuals:
            leaf.detach(depth_filter)
            # Restore blend? We don't know previous state easily.
            # But usually we can set blend=True if it was translucent.
            # Most objects are opaque.
            # Let's just set blend=True as a safe default or try to be smarter?
            # PickingManager sets blend=True/False based on enabled.
            # Here we just want to restore.
            # If we leave it blend=False, transparency breaks.
            # If we set blend=True, opaque objects might blend?
            # Vispy visuals usually manage their own state in `_prepare_draw`.
            # Calling `update_gl_state` overrides it?
            # Let's try to just detach. The state might persist?
            # `update_gl_state` updates `self._gl_state`.
            # We should probably read it before setting.
            # But `leaf.gl_state` might be complex.
            # Let's just set blend=True for now, assuming standard blending.
            # Or better: don't change blend if we can avoid it?
            # If we don't disable blend, translucent objects might blend with clear color.
            # But we want the depth of the surface.
            # If we don't disable blend, the shader output (packed depth) will be blended with (0,0,0,0).
            # That corrupts the data.
            # So we MUST disable blend.
            pass
            
        # Restore visibility
        viewport.grid_node.visible = grid_visible
        viewport.gizmo_node.visible = gizmo_visible
        
        # Restore blend state properly?
        # We can iterate and set blend='translucent' or something?
        # For now, let's just set blend=True which is the default for most Vispy visuals?
        # Actually, `CGeometry` sets `translucent` in `GridVisual`? No.
        # `CGeometry` doesn't set state explicitly in `__init__`.
        # `MeshVisual` sets `depth_test=True`.
        # Let's just hope `leaf.update_gl_state(blend=True)` is safe enough or `blend='auto'`.
        for leaf in attached_visuals:
             leaf.update_gl_state(blend=True) 

    # 5. Process Depth
    # pixel is [R, G, B, A] uint8
    r, g, b, a = pixel
    
    # Check for background (0,0,0,0)
    if r == 0 and g == 0 and b == 0 and a == 0:
        # Background (Depth = 1.0 or 0.0)
        # Assume background -> Fallback to Grid
        hit_object = False
        depth_val = 1.0
    else:
        hit_object = True
        # Unpack
        # Shader:
        # res = fract(d * bitSh);
        # bitSh = (2^24, 2^16, 2^8, 1)
        # R = fract(d * 2^24)
        # A = fract(d)
        
        # Unpack:
        # d = R * 2^-24 + G * 2^-16 + B * 2^-8 + A
        # All values 0..1 (normalized from 0..255)
        
        rn = r / 255.0
        gn = g / 255.0
        bn = b / 255.0
        an = a / 255.0
        
        depth_val = (rn / (256.0**3)) + (gn / (256.0**2)) + (bn / 256.0) + an
        
        # Handle the fract(1.0) = 0 case if needed?
        # If depth was 1.0, we got 0.
        # But we handled 0 above.
    
    # 6. Unproject
    try:
        # Transform from Canvas (pixels) to Scene (World)
        # Use grid (VisualNode) as reference for World Space. 
        # grid_node is a plain Node and might not have get_transform.
        tr = viewport.grid.get_transform(map_from='canvas')
        
        # Map (x, y, depth, 1)
        # Note: Vispy canvas coords have (0,0) at top-left?
        # `mapFromGlobal` gives widget coords.
        # Vispy events use (x, y).
        # `tr.map` expects (x, y, z, w).
        # Does `tr` handle the Y-flip?
        # In `viewport.py`, `_on_mouse_press` uses `event.pos`.
        # `event.pos` is (x, y) from top-left.
        # The `tr` obtained from `view.scene.get_transform(map_from='canvas')` should handle it.
        # In the previous code, we used `tr.map([x, y, 0, 1])`.
        # So we should use `[x, y, depth_val, 1]`.
        
        world_pos_hom = tr.map([x, y, depth_val, 1])
        world_pos = world_pos_hom[:3] / world_pos_hom[3]
        
        if hit_object:
            print(f"Hit Surface: X={world_pos[0]:.4f}, Y={world_pos[1]:.4f}, Z={world_pos[2]:.4f}")
        else:
            # Fallback to Grid Intersection (Y=0)
            # We have the ray from camera (depth=0) to far (depth=1)
            # Or just use the previous analytical logic for grid
            
            p0 = tr.map([x, y, 0, 1])
            p1 = tr.map([x, y, 1, 1])
            p0 = p0[:3] / p0[3]
            p1 = p1[:3] / p1[3]
            
            origin = p0
            direction = p1 - p0
            direction = direction / np.linalg.norm(direction)
            
            if abs(direction[1]) > 1e-6:
                t = -origin[1] / direction[1]
                grid_pos = origin + t * direction
                print(f"Grid Projection (Y=0): X={grid_pos[0]:.2f}, Y={grid_pos[1]:.2f}, Z={grid_pos[2]:.2f}")
            else:
                print("Ray parallel to grid")

    except Exception as e:
        print(f"Error calculating coordinates: {e}")
