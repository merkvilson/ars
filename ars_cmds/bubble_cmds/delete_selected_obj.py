from theme.fonts.font_icons import *
from core.sound_manager import play_sound
from PyQt6.QtCore import QTimer
import time
import numpy as np

BBL_TRASH_CONFIG = {'symbol': ICON_TRASH, 'hotkey': 'del'}
def BBL_TRASH(self, position):
    if self.viewport.is_not_empty():
        om = self.viewport._objectManager
        index = om._active_idx
        if index < 0 or index >= len(om._objects):
            return
        
        obj = om._objects.pop(index)
        
        # Handle children hierarchy
        for child in list(obj._children):
            child.set_parent(obj._parent)
        obj._children = []
        obj._parent = None
        
        # Adjust selected indices
        old_selected = om._selected_indices[:]
        new_selected = []
        for i in old_selected:
            if i != index:
                new_selected.append(i - 1 if i > index else i)
        sel_changed = new_selected != old_selected
        om._selected_indices = new_selected
        om._selected_set = set(new_selected)
        
        # Adjust active index
        if index < om._active_idx:
            om._active_idx -= 1
        # If removed active, keep it pointing to the next (now shifted)
        # No further adjustment needed here
        
        new_len = len(om._objects)
        om._active_idx = max(-1, min(om._active_idx, new_len - 1))
        
        # Rebuild picking without removing visual yet
        om._rebuild_picking()
        
        # Emit signals
        om.object_removed.emit(index, obj)
        if sel_changed:
            om.selection_changed.emit()
        om.set_active(om._active_idx)  # This will emit active_changed if needed
        
        # Extract current rotation and scale for animation
        current_matrix = obj.rotation_visual.transform.matrix.copy()
        
        sx = np.linalg.norm(current_matrix[0, :3])
        sy = np.linalg.norm(current_matrix[1, :3])
        sz = np.linalg.norm(current_matrix[2, :3])
        
        if sx < 1e-8: sx = 1.0
        if sy < 1e-8: sy = 1.0
        if sz < 1e-8: sz = 1.0
        
        rot_matrix_part = current_matrix[:3, :3].copy()
        rot_matrix_part[0, :] /= sx
        rot_matrix_part[1, :] /= sy
        rot_matrix_part[2, :] /= sz
        
        # Function to build transform matrix
        def build_transform(f):
            S_vec = [sx * f, sy * f, sz * f]
            S = np.eye(4)
            S[0, 0] = S_vec[0]
            S[1, 1] = S_vec[1]
            S[2, 2] = S_vec[2]
            R_full = np.eye(4)
            R_full[:3, :3] = rot_matrix_part
            return (S @ R_full).astype(np.float32)
        
        # Start scale up animation (50ms to 1.2, linear)
        def start_scale_up():

            start_time = time.time()
            duration = 0.050
            
            timer = QTimer()
            
            def update_scale():
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    timer.stop()
                    start_scale_down()
                    return
                
                t = elapsed / duration
                f = 1 + 0.2 * t  # Linear scale up
                obj.rotation_visual.transform.matrix = build_transform(f)
                self.viewport._canvas.update()
            
            timer.timeout.connect(update_scale)
            timer.start(10)  # Update every 10 ms
        
        # Scale down animation (150ms to 0, ease in)
        def start_scale_down():
            play_sound("obj-delete")

            start_time = time.time()
            duration = 0.150
            
            timer = QTimer()
            
            def update_scale():
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    timer.stop()
                    obj.visual.parent = None
                    self.viewport._canvas.update()
                    return
                
                t = elapsed / duration
                ease = t ** 2  # Ease-in quadratic
                f = 1.2 - 1.2 * ease
                obj.rotation_visual.transform.matrix = build_transform(f)
                self.viewport._canvas.update()
            
            timer.timeout.connect(update_scale)
            timer.start(10)
        
        # Start the animation sequence
        QTimer.singleShot(0, start_scale_up)