from theme.fonts import font_icons as ic
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap
import os
from prefs.pref_controller import get_path

def generate_render(self, ctx, max_steps, default_object):

    self.render_manager.send_render()
    
    # Stop any existing timer before starting a new one
    if hasattr(self, '_render_timer') and self._render_timer is not None:
        self._render_timer.stop()
        self._render_timer.deleteLater()
    
    # Create a timer to apply the latest file every 100ms
    update_timer = QTimer()
    final_attempts = {'count': 0}
    
    def apply_latest_texture():
        current_files = os.listdir(get_path("steps"))
        current_step = len(current_files)

        if type(default_object).__name__ == "CSprite":
            try:
                latest_file = get_path("last_step")
                if latest_file:
                    default_object.set_texture(latest_file)
                    
                    # Calculate alpha based on current step (0.1 to 0.99)
                    alpha = 0.1 + (0.89 * (current_step / (max_steps + 1)))
                    default_object.set_alpha( alpha)
                    
                    # Check if we've reached max_steps + 1
                    if current_step >= max_steps + 1:
                        default_object.cutout()
                        #print("finish")
                        update_timer.stop()

            except Exception as e:
                print(f"Error applying texture: {e}")
            
        else:

            if current_step >= max_steps + 2:
                final_attempts['count'] += 1
                if final_attempts['count'] >= 10:
                    #print("finish")
                    update_timer.stop()
                    return
            
            latest_file = get_path("last_step")
            if latest_file and os.path.exists(latest_file):
                try:
                    pixmap = QPixmap(latest_file)
                    if not pixmap.isNull():
                        if type(default_object).__name__ == "CPoint":
                            self.viewport.bg.set_image(latest_file)
                        else:
                            ctx.update_item(ic.ICON_IMAGE, "image_path", latest_file)
                        if not self.viewport.isVisible() and hasattr(self, 'img') and self.img and get_path('last_step'):
                            self.img.open_image(get_path('last_step'))

                except:
                    pass
        
    # Start the timer
    update_timer.timeout.connect(apply_latest_texture)
    update_timer.start(100)
    
    self._render_timer = update_timer