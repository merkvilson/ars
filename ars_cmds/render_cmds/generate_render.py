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
    final_attempts = {'count': 0, 'last_step': 0}
    
    def apply_latest_texture():
        steps_path = get_path("steps")
        if not os.path.exists(steps_path):
            return

        all_files = os.listdir(steps_path)
        valid_exts = ('.png', '.jpg', '.jpeg', '.tiff')
        image_files = [f for f in all_files if f.lower().endswith(valid_exts)]
        
        if not image_files:
            return

        full_paths = [os.path.join(steps_path, f) for f in image_files]
        full_paths.sort(key=os.path.getmtime)
        
        current_step = len(full_paths)
        last_file = full_paths[-1]
        
        # Reset counter if new files appear
        if current_step > final_attempts['last_step']:
            final_attempts['last_step'] = current_step
            final_attempts['count'] = 0

        stop_rendering = False

        if last_file.lower().endswith('.tiff'):
            stop_rendering = True
        elif type(default_object).__name__ == "CSprite":
            if current_step >= max_steps + 1:
                stop_rendering = True
        else:
            # Image Render: Wait for stability after reaching max steps
            if current_step >= max_steps + 1:
                final_attempts['count'] += 1
                if final_attempts['count'] >= 20: # Wait ~2 seconds of silence
                    stop_rendering = True

        file_to_apply = None
        if stop_rendering:
            valid_candidates = [p for p in full_paths if p.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if valid_candidates:
                file_to_apply = valid_candidates[-1]
        else:
            if len(full_paths) >= 2:
                file_to_apply = full_paths[-2]
        
        if file_to_apply and not file_to_apply.lower().endswith(('.png', '.jpg', '.jpeg')):
            file_to_apply = None

        if type(default_object).__name__ == "CSprite":
            try:
                if file_to_apply:
                    default_object.set_texture(file_to_apply)
                    
                    # Calculate alpha based on current step (0.1 to 0.99)
                    alpha = 0.1 + (0.89 * (current_step / (max_steps + 1)))
                    default_object.set_alpha(min(alpha, 1.0))
                    
                if stop_rendering:
                    default_object.cutout()
                    #print("finish")
                    update_timer.stop()

            except Exception as e:
                print(f"Error applying texture: {e}")
            
        else:
            if file_to_apply and os.path.exists(file_to_apply):
                try:
                    pixmap = QPixmap(file_to_apply)
                    if not pixmap.isNull():
                        if type(default_object).__name__ == "CPoint":
                            self.viewport.bg.set_image(file_to_apply)
                        else:
                            ctx.update_item(ic.ICON_IMAGE, "image_path", file_to_apply)
                        if not self.viewport.isVisible() and hasattr(self, 'img') and self.img:
                            self.img.open_image(file_to_apply)
                except:
                    pass

            if stop_rendering:
                update_timer.stop()
                return
        
    # Start the timer
    update_timer.timeout.connect(apply_latest_texture)
    update_timer.start(100)
    
    self._render_timer = update_timer