from typing import List, Optional
from vispy import scene
from ..mesh_objects.scene_objects import CGeometry
from .picking_manager import CPickingManager
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class CObjectManager(QObject):
    """Manages 3D scene objects including selection, ordering, and picking.
    
    Signals:
        object_added(int, CGeometry): Emitted when an object is added (index, object).
        object_removed(int, CGeometry): Emitted when an object is removed (index, object).
        active_changed(int): Emitted when the active object index changes.
        selection_changed(): Emitted when the selection state changes.
    """
    object_added = pyqtSignal(int, CGeometry)
    object_removed = pyqtSignal(int, CGeometry)
    active_changed = pyqtSignal(int)
    selection_changed = pyqtSignal()
    parent_changed = pyqtSignal(object, object)

    def __init__(self, view: scene.widgets.ViewBox
                 , canvas: scene.SceneCanvas
                 , mover: None
                 , picking: CPickingManager,
                 parent=None):
        """Initialize the object manager.
        
        Args:
            view: The ViewBox containing the 3D scene.
            canvas: The SceneCanvas for rendering.
            mover: Optional mover/gizmo controller.
            picking: The picking manager for mouse selection.
            parent: Optional Qt parent object.
        """
        super().__init__(parent)
        self._view = view
        self._canvas = canvas
        self._mover = mover
        self._picking = picking
        self._objects: List[CGeometry] = []
        self._active_idx = -1
        self._selected_indices: List[int] = []
        self._selected_set: set[int] = set()
        self._obj_to_pid = {}
        
        # Timer for auto-selecting newly added objects
        self._auto_select_timer = QTimer()
        self._auto_select_timer.setSingleShot(True)
        self._auto_select_timer.setInterval(250)

    def update_lights(self, light_dir):
            """Update light direction across all objects' shading filters.
            
            Args:
                light_dir: The new light direction vector.
            """
            for obj in self._objects:
                if hasattr(obj, 'update_light_dir'):
                    obj.update_light_dir(light_dir)

    def notify_parent_changed(self, child: CGeometry, new_parent: Optional[CGeometry]) -> None:
        """Notify listeners that an object's parent has changed."""
        self.parent_changed.emit(child, new_parent)

    def add_object(self, obj: CGeometry) -> None:
        """Add a geometry object to the scene.
        
        Args:
            obj: The geometry object to add.
        """
        obj.manager = self
        index = len(self._objects)
        self._objects.append(obj)
        obj.visual.parent = self._view.scene
        # Use rotation_visual (the mesh) for picking to avoid traversing children
        pid = self._picking.register_visual(index=index, visual=obj.rotation_visual)
        self._obj_to_pid[id(obj)] = pid
        self.object_added.emit(index, obj)
        # Immediately deselect current selection
        self.set_selection_state([], None)
        
        # Schedule new object selection (restarts timer if already running)
        # This ensures only the last added object in a batch is selected
        try:
            self._auto_select_timer.timeout.disconnect()
        except TypeError:
            pass # No connection
            
        self._auto_select_timer.timeout.connect(lambda: self.set_selection_state([index], index))
        self._auto_select_timer.start()
        
    def duplicate_selected(self, offset = (0,0,0)) -> None:
        """Duplicate the currently selected objects and add them to the scene.
        
        Args:
            offset: Position offset (x, y, z) to apply to duplicates.
        """
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

    def remove_object(self, obj: CGeometry) -> None:
        """Remove an object from the scene by reference.
        
        Args:
            obj: The geometry object to remove.
        """
        try:
            index = self._objects.index(obj)
            self.remove_object_at(index)
        except ValueError:
            pass

    def remove_object_at(self, index: int) -> Optional[CGeometry]:
        """Remove an object from the scene by index.
        
        Args:
            index: The index of the object to remove.
            
        Returns:
            The removed object, or None if index was invalid.
        """
        if index < 0 or index >= len(self._objects):
            return None
        obj = self._objects.pop(index)
        if id(obj) in self._obj_to_pid:
            del self._obj_to_pid[id(obj)]
            
        if obj._parent:
            obj._parent._children.remove(obj)

        for child in list(obj._children):
            child.set_parent(obj._parent)
        obj._children = []
        obj._parent = None
        obj.visual.parent = None
        
        # Rebuild picking to ensure clean state and correct indices
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
        """Rebuild the picking manager and re-register all objects."""
        self._picking = CPickingManager(self._canvas)
        self._obj_to_pid.clear()
        for idx, o in enumerate(self._objects):
            pid = self._picking.register_visual(index=idx, visual=o.rotation_visual)
            self._obj_to_pid[id(o)] = pid

    def reorder_objects(self, new_objects: List[CGeometry]) -> None:
        """Reorder the objects list and update picking indices.
        
        Args:
            new_objects: The new ordered list of geometry objects.
        """
        self._objects = new_objects
        self._picking.clear_index_map()
        for i, obj in enumerate(self._objects):
            pid = self._obj_to_pid.get(id(obj))
            if pid is not None:
                self._picking.update_index(pid, i)
            else:
                # Fallback if pid missing
                pid = self._picking.register_visual(index=i, visual=obj.rotation_visual)
                self._obj_to_pid[id(obj)] = pid

    def set_active(self, index: int) -> None:
        """Set the active object by index.
        
        Args:
            index: The index of the object to make active.
        """
        if 0 <= index < len(self._objects):
            if self._active_idx != index:
                self._active_idx = index
                self.active_changed.emit(index)

    def active_object(self) -> Optional[CGeometry]:
        """Get the currently active object.
        
        Returns:
            The active geometry object, or None if no object is active.
        """
        if 0 <= self._active_idx < len(self._objects):
            return self._objects[self._active_idx]
        return None

    def active_index(self) -> int:
        """Get the index of the currently active object."""
        return self._active_idx

    def count(self) -> int:
        """Get the total number of objects in the scene."""
        return len(self._objects)

    def object_at(self, index: int) -> Optional[CGeometry]:
        """Get an object by index, or None if invalid."""
        if 0 <= index < len(self._objects):
            return self._objects[index]
        return None

    def picking(self) -> CPickingManager:
        """Get the picking manager instance."""
        return self._picking

    def selected_indices(self) -> List[int]:
        """Get a copy of the selected object indices."""
        return list(self._selected_indices)

    def get_selected_objects(self) -> List[CGeometry]:
        """Get a list of currently selected geometry objects."""
        return [self._objects[i] for i in self._selected_indices if 0 <= i < len(self._objects)]

    def resolve_targets(self) -> List[CGeometry]:
        """Get target objects for operations (selected or active).
        
        Returns:
            Selected objects if any, otherwise the active object, or empty list.
        """
        if self._selected_indices:
            return [self._objects[i] for i in self._selected_indices if 0 <= i < len(self._objects)]
        if 0 <= self._active_idx < len(self._objects):
            return [self._objects[self._active_idx]]
        return []

    def set_selection_state(self, indices: List[int], active: Optional[int]) -> None:
        """Set the selection and active state.
        
        Args:
            indices: List of object indices to select.
            active: Index of the object to make active, or None.
        """
        # Stop auto-selection timer if manual selection occurs
        if self._auto_select_timer.isActive():
            self._auto_select_timer.stop()

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
