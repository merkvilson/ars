from theme.fonts import font_icons as ic
from PyQt6.QtCore import QTimer
import os
from prefs.pref_controller import get_path

def generate_sprite(self, ctx, max_steps, default_object):

    sprite_plane = default_object
    sprite_plane.set_color((1,1,1,0.3)) # Set to white to ensure textures are visible


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
                
                # Calculate alpha based on current step (0.1 to 0.99)
                current_files = os.listdir(sprite_dir)
                current_step = len(current_files)
                alpha = 0.1 + (0.89 * (current_step / (max_steps + 1)))
                sprite_plane.set_alpha( alpha)
                
                # Check if we've reached max_steps + 1
                if current_step >= max_steps + 1:
                    sprite_plane.cutout()
                    print("finish")
                    update_timer.stop()
        except Exception as e:
            print(f"Error applying texture: {e}")
    
    # Start the timer
    update_timer.timeout.connect(apply_latest_texture)
    update_timer.start(100)
    
    # Store timer reference to prevent garbage collection
    self._sprite_timer = update_timer
    