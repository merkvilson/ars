from theme.fonts import font_icons as ic
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap
import os
from prefs.pref_controller import get_path

def generate_render(self, ctx, max_steps):

    self.render_manager.send_render()
    
    # Stop any existing timer before starting a new one
    if hasattr(self, '_sprite_timer') and self._sprite_timer is not None:
        self._sprite_timer.stop()
        self._sprite_timer.deleteLater()
    
    # Create a timer to apply the latest file every 100ms
    update_timer = QTimer()
    final_attempts = {'count': 0}
    
    def apply_latest_texture():
        current_step = len(os.listdir(get_path("steps")))
        
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
                    ctx.update_item(ic.ICON_IMAGE, "image_path", latest_file)
            except:
                pass
    
    # Start the timer
    update_timer.timeout.connect(apply_latest_texture)
    update_timer.start(100)
    
    self._sprite_timer = update_timer