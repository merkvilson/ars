from theme.fonts import font_icons as ic
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap
import os
from prefs.pref_controller import get_path

def generate_sprite(self, ctx, max_steps, default_object):

    self.render_manager.send_render()
    
    # Stop any existing timer before starting a new one
    if hasattr(self, '_render_timer') and self._render_timer is not None:
        self._render_timer.stop()
        self._render_timer.deleteLater()
    
    # Create a timer to apply the latest file every 500ms
    update_timer = QTimer()
    final_attempts = {'count': 0}

    def apply_latest_texture():
        try:
            latest_file = get_path("last_step")
            if latest_file:
                default_object.set_texture(latest_file)
                
                # Calculate alpha based on current step (0.1 to 0.99)
                current_files = os.listdir(get_path("steps"))
                current_step = len(current_files)
                alpha = 0.1 + (0.89 * (current_step / (max_steps + 1)))
                default_object.set_alpha( alpha)
                
                # Check if we've reached max_steps + 1
                if current_step >= max_steps + 1:
                    default_object.cutout()
                    #print("finish")
                    update_timer.stop()

        except Exception as e:
            print(f"Error applying texture: {e}")
    
    # Start the timer
    update_timer.timeout.connect(apply_latest_texture)
    update_timer.start(100)
    
    # Store timer reference to prevent garbage collection
    self._render_timer = update_timer
    