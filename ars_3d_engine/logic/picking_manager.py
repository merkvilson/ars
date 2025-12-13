import numpy as np
import time
from vispy import scene
from vispy.visuals.filters.picking import PickingFilter
from typing import Optional

class CPickingManager:
    """Handles GPU-based object picking for mouse selection in 3D scenes.
    
    Uses PickingFilter to render unique IDs for each visual, enabling
    accurate object selection via pixel color lookup.
    """
    
    def __init__(self, canvas: scene.SceneCanvas):
        """Initialize the picking manager.
        
        Args:
            canvas: The SceneCanvas used for rendering pick buffers.
        """
        self._canvas = canvas
        self._next_id: int = 1
        self._entries: list[tuple[object, PickingFilter]] = []
        self._id_to_index: dict[int, int] = {}
        self._picking_enabled: bool = False
        self._last_pick: tuple[int, int, float, Optional[int]] = (-1, -1, 0.0, None)
        self._enabled: bool = True

    @property
    def enabled(self) -> bool:
        """Whether picking is enabled for this manager."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable picking.

        When disabled, calls to pick_at() return None and no offscreen pick render
        is performed.
        """
        self._enabled = bool(enabled)

    def enable(self) -> None:
        """Convenience wrapper for set_enabled(True)."""
        self.set_enabled(True)

    def disable(self) -> None:
        """Convenience wrapper for set_enabled(False)."""
        self.set_enabled(False)

    def _iter_leaf_visuals(self, node):
        """Iterate over all leaf visuals in a node hierarchy.
        
        Args:
            node: The root visual node to traverse.
            
        Yields:
            Leaf visual nodes (nodes without children).
        """
        stack = [node]
        while stack:
            n = stack.pop()
            ch = n.children
            if ch:
                stack.extend(ch)
            else:
                yield n

    def register_visual(self, index: int, visual) -> int:
        """Register a visual for picking.
        
        Args:
            index: The object index to associate with this visual.
            visual: The visual node to register.
            
        Returns:
            The unique picking ID assigned to this visual.
        """
        pid = self._next_id
        self._next_id += 1
        for leaf in self._iter_leaf_visuals(visual):
            flt = PickingFilter(id_=pid)
            leaf.attach(flt)
            try:
                flt.enabled = False
            except Exception:
                pass
            self._entries.append((leaf, flt))
        self._id_to_index[pid] = index
        #TODO: uncomment and check later.
        #print(f"Registered visual for picking with ID {pid} and index {index}")
        return pid

    def update_index(self, pid: int, index: int) -> None:
        """Update the object index for a picking ID.
        
        Args:
            pid: The picking ID to update.
            index: The new object index.
        """
        self._id_to_index[pid] = index

    def clear_index_map(self) -> None:
        """Clear all picking ID to index mappings."""
        self._id_to_index.clear()

    def _set_enabled(self, enabled: bool) -> None:
        """Enable or disable picking filters on all registered visuals.
        
        Args:
            enabled: True to enable picking mode, False for normal rendering.
        """
        if enabled == self._picking_enabled:
            return

        # Avoid per-pick GL-state churn. Toggling blend/depth per-leaf is expensive
        # with many objects and isn't necessary for most opaque meshes.
        for leaf, flt in self._entries:
            flt.enabled = enabled

        self._picking_enabled = enabled

    def pick_at(self, x: float, y: float) -> Optional[int]:
        """Pick an object at the given screen coordinates.
        
        Args:
            x: Screen X coordinate.
            y: Screen Y coordinate.
            
        Returns:
            The object index at the coordinates, or None if nothing was picked.
        """
        if not self._enabled:
            return None

        # Fast-path: repeated queries at the same pixel within a short time window.
        # This helps if pick_at is called multiple times in the same interaction.
        now = time.time()
        lx, ly, lt, lres = self._last_pick
        ix = int(round(float(x)))
        iy = int(round(float(y)))
        if ix == lx and iy == ly and (now - lt) < 0.05:
            return lres

        self._set_enabled(True)
        try:
            ps = float(self._canvas.pixel_scale or 1.0)
            fb_w, fb_h = int(self._canvas.size[0] * ps), int(self._canvas.size[1] * ps)
            px = int(round(x * ps))
            py = int(round(fb_h - (y * ps)))
            if px < 0 or py < 0 or px >= fb_w or py >= fb_h:
                return None
            img = self._canvas.render(
                crop=(px, py, 1, 1),
                bgcolor=(0, 0, 0, 0),
                alpha=True,
            )
            obj_id = int(img.view(np.uint32)[0, 0, 0])
            if obj_id < 0:
                return None
            res = self._id_to_index.get(obj_id, None)
            self._last_pick = (ix, iy, now, res)
            return res
        finally:
            self._set_enabled(False)