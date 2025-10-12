from theme.fonts import font_icons as ic
from core.sound_manager import play_sound
from PyQt6.QtCore import QTimer
import time
import numpy as np

BBL_TRASH_CONFIG = {'symbol': ic.ICON_TRASH, 'hotkey': 'del'}
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
        
        # Extract initial scales for animation
        current_matrix = obj.rotation_visual.transform.matrix.copy()
        
        sx = np.linalg.norm(current_matrix[0, :3])
        sy = np.linalg.norm(current_matrix[1, :3])
        sz = np.linalg.norm(current_matrix[2, :3])
        
        # Start scale up animation (50ms to 1.2, linear)
        def start_scale_up():

            start_time = time.time()
            duration = 0.050
            
            timer = QTimer(self)
            
            def update_scale():
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    timer.stop()
                    start_scale_down()
                    return
                
                t = elapsed / duration
                f = 1 + 0.2 * t  # Linear scale up
                obj.set_scale((sx * f, sy * f, sz * f))
                self.viewport._canvas.update()
            
            timer.timeout.connect(update_scale)
            timer.start(10)  # Update every 10 ms
        
        # Scale down animation (150ms to 0, ease in)
        def start_scale_down():
            play_sound("obj-delete")

            start_time = time.time()
            duration = 0.150
            
            timer = QTimer(self)
            
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
                obj.set_scale((sx * f, sy * f, sz * f))
                self.viewport._canvas.update()
            
            timer.timeout.connect(update_scale)
            timer.start(10)
        
        # Start the animation sequence
        QTimer.singleShot(0, start_scale_up)