from theme.fonts import font_icons as ic
from PyQt6.QtCore import QFileSystemWatcher, QTimer
import os
from prefs.pref_controller import get_path
from ars_cmds.core_cmds.load_object import add_mesh

from ars_cmds.mesh_gen.animated_bbox import bbox_loading_animation, remove_bbox_loading_animation
from ars_cmds.render_cmds.check import check_queue



def generate_sprite(self, ctx, max_steps):
    """
    Generates a sprite by monitoring a directory for new images and creating a sprite sheet.
    sprite images are saved in the 'steps' directory.
    
    """

    selected = self.viewport._objectManager.get_selected_objects()
    if not selected:
        return
    
    sprite_plane = selected[0]

    ctx.update_item(ic.ICON_RENDER , "progress_bar", 1)
    self.render_manager.send_render()
    sprite_dir = get_path("steps")

    os.makedirs(sprite_dir, exist_ok=True)    # Ensure the sprite directory exists
    
    initial_files = os.listdir(sprite_dir)
    if initial_files:
        sprite_plane.set_texture(os.path.join(sprite_dir, initial_files[-1]))
    
    print(initial_files)
    