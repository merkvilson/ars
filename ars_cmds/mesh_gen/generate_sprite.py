from theme.fonts import font_icons as ic
from PyQt6.QtCore import QFileSystemWatcher, QTimer
import os
from prefs.pref_controller import get_path
from ars_cmds.core_cmds.load_object import add_mesh

from ars_cmds.mesh_gen.animated_bbox import bbox_loading_animation, remove_bbox_loading_animation
from ars_cmds.render_cmds.check import check_queue

from prefs.pref_controller import get_path

def generate_sprite(self, ctx, max_steps):
    """
    Generates a sprite by monitoring a directory for new images and creating a sprite sheet.
    sprite images are saved in the 'steps' directory.
    
    """

    selected = self.viewport._objectManager.get_selected_objects()
    if not selected:
        return
    
    sprite_plane = selected[0]

    sprite_plane.set_color((1,1,1,0.99)) # Set to white to ensure textures are visible


    ctx.update_item(ic.ICON_RENDER , "progress_bar", 1)
    self.render_manager.send_render()
    sprite_dir = get_path("steps")

    os.makedirs(sprite_dir, exist_ok=True)    # Ensure the sprite directory exists
    
    # Stop any existing timer before starting a new one
    if hasattr(self, '_sprite_timer') and self._sprite_timer is not None:
        self._sprite_timer.stop()
        self._sprite_timer.deleteLater()
    
    # Create a timer to apply the latest file every 500ms
    update_timer = QTimer()
    
    def apply_latest_texture():
        try:
            latest_file = get_path("last_step")
            if latest_file:
                sprite_plane.set_texture(latest_file)
                
                # Check if we've reached max_steps + 1
                current_files = os.listdir(sprite_dir)
                if len(current_files) >= max_steps + 1:
                    print("finish")
                    update_timer.stop()
        except Exception as e:
            print(f"Error applying texture: {e}")
    
    # Start the timer
    update_timer.timeout.connect(apply_latest_texture)
    update_timer.start(100)
    
    # Store timer reference to prevent garbage collection
    self._sprite_timer = update_timer
    