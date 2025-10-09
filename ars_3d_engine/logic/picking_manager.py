import numpy as np
from vispy import scene
from vispy.visuals.filters.picking import PickingFilter
from typing import Optional

class CPickingManager:
    def __init__(self, canvas: scene.SceneCanvas):
        self._canvas = canvas
        self._next_id: int = 1
        self._entries: list[tuple[object, PickingFilter]] = []
        self._id_to_index: dict[int, int] = {}

    def _iter_leaf_visuals(self, node):
        stack = [node]
        while stack:
            n = stack.pop()
            ch = n.children
            if ch:
                stack.extend(ch)
            else:
                yield n

    def register_visual(self, index: int, visual) -> None:
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

    def _set_enabled(self, enabled: bool) -> None:
        for leaf, flt in self._entries:
            try:
                flt.enabled = enabled
            except Exception:
                pass
            try:
                leaf.update_gl_state(blend=not enabled)
            except Exception:
                pass

    def pick_at(self, x: float, y: float) -> Optional[int]:
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
            return self._id_to_index.get(obj_id, None)
        finally:
            self._set_enabled(False)