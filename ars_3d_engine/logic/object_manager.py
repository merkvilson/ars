from typing import List, Optional
from vispy import scene
from .scene_objects import IObject3D
from .picking_manager import CPickingManager
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class CObjectManager(QObject):
    object_added = pyqtSignal(int, IObject3D)
    object_removed = pyqtSignal(int, IObject3D)
    active_changed = pyqtSignal(int)
    selection_changed = pyqtSignal()

    def __init__(self, view: scene.widgets.ViewBox
                 , canvas: scene.SceneCanvas
                 , mover: None
                 , picking: CPickingManager,
                 parent=None):
        super().__init__(parent)
        self._view = view
        self._canvas = canvas
        self._mover = mover
        self._picking = picking
        self._objects: List[IObject3D] = []
        self._active_idx = -1
        self._selected_indices: List[int] = []
        self._selected_set: set[int] = set()

    #used by camera
    def update_lights(self, light_dir):
            """Update light direction across all objects' shading filters."""
            for obj in self._objects:
                if hasattr(obj, 'update_light_dir'):
                    obj.update_light_dir(light_dir)


    def add_object(self, obj: IObject3D) -> None:
        index = len(self._objects)
        self._objects.append(obj)
        obj.visual.parent = self._view.scene
        self._picking.register_visual(index=index, visual=obj.visual)
        self.object_added.emit(index, obj)
        # Immediately deselect current selection
        self.set_selection_state([], None)
        # Schedule new object selection after 250ms delay
        QTimer.singleShot(250, lambda: self.set_selection_state([index], index))
        
    def duplicate_selected(self, offset = (0,0,0)) -> None:
        """Duplicate the currently selected objects and add them to the scene."""
        selected = self.get_selected_objects()
        if not selected:
            return  # Nothing to duplicate

        new_indices = []
        for obj in selected:
            clone = obj.clone()
            # Optionally offset the position slightly to avoid perfect overlap
            if offset:
                current_pos = clone.get_position()
                clone.set_position(current_pos[0] + offset[0], current_pos[1] + offset[1], current_pos[2] + offset[2])
            
            self.add_object(clone)
            new_indices.append(len(self._objects) - 1)  # Clone was added at the end

        # Select the new clones (deselect originals)
        self.set_selection_state(new_indices, new_indices[-1] if new_indices else None)


    def remove_object_at(self, index: int) -> Optional[IObject3D]:
        if index < 0 or index >= len(self._objects):
            return None
        obj = self._objects.pop(index)
        for child in list(obj._children):
            child.set_parent(obj._parent)
        obj._children = []
        obj._parent = None
        obj.visual.parent = None
        self._rebuild_picking()
        self._selected_indices = [i for i in self._selected_indices if i != index]
        self._selected_set = set(self._selected_indices)
        self.object_removed.emit(index, obj)
        if self._objects:
            new_active = min(self._active_idx, len(self._objects) - 1)
            self.set_active(new_active)
        else:
            self._active_idx = -1
        return obj

    def _rebuild_picking(self) -> None:
        self._picking = CPickingManager(self._canvas)
        for idx, o in enumerate(self._objects):
            self._picking.register_visual(index=idx, visual=o.visual)

    def set_active(self, index: int) -> None:
        if 0 <= index < len(self._objects):
            if self._active_idx != index:
                self._active_idx = index
                self.active_changed.emit(index)

    def active_object(self) -> Optional[IObject3D]:
        if 0 <= self._active_idx < len(self._objects):
            return self._objects[self._active_idx]
        return None

    def active_index(self) -> int:
        return self._active_idx

    def count(self) -> int:
        return len(self._objects)

    def picking(self) -> CPickingManager:
        return self._picking

    def selected_indices(self) -> List[int]:
        return list(self._selected_indices)

    def get_selected_objects(self) -> List[IObject3D]:
        return [self._objects[i] for i in self._selected_indices if 0 <= i < len(self._objects)]

    def resolve_targets(self) -> List[IObject3D]:
        if self._selected_indices:
            return [self._objects[i] for i in self._selected_indices if 0 <= i < len(self._objects)]
        if 0 <= self._active_idx < len(self._objects):
            return [self._objects[self._active_idx]]
        return []

    def set_selection_state(self, indices: List[int], active: Optional[int]) -> None:
        valid = []
        seen = set()
        n = len(self._objects)
        for i in indices:
            if isinstance(i, int) and 0 <= i < n and i not in seen:
                valid.append(i)
                seen.add(i)
                
        sel_changed = valid != self._selected_indices
        self._selected_indices = valid
        self._selected_set = set(valid)
        if sel_changed:
            self.selection_changed.emit()
        if active is None:
            new_active = -1
        else:
            new_active = active if isinstance(active, int) and 0 <= active < n else -1
        if new_active != self._active_idx:
            self._active_idx = new_active
            self.active_changed.emit(self._active_idx)
