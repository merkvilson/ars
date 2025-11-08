from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.load_object import selected_object
from PyQt6.QtCore import QPoint, QTimer
from prefs.pref_controller import get_path
import os
from ars_cmds.util_cmds.delete_files import delete_all_files_in_folder
from ars_cmds.render_cmds.check import check_queue

BBL_TEST_CONFIG = {"symbol": ic.ICON_TEST}
def BBL_TEST(self, position):
    run_ext(__file__, self)

def main(self):
    
    # Timer and state for loop_gif
    if not hasattr(self, '_loop_timer'):
        self._loop_timer = None
    if not hasattr(self, '_loop_index'):
        self._loop_index = 0


    config = ContextMenuConfig()
    config.use_extended_shape_items = {"A": (self.width() / (config.item_radius * 2), 1)}
    config.hover_scale_items = {"A": 0.95}
    config.auto_close = False
    config.extra_distance = [0,99999]
    config.distribution_mode = "x"
    config.custom_height = 150
    #config.custom_width = 450

    print(self.width() / (config.item_radius * 2),)

    options_list=    [
        ["   ", 'A', "   ",],
        ["   ", "R", "L", "   ",]
        ]
    config.expand = "x"


    config.slider_values = {
        'A': (0, 100, 50),
    }
    config.show_value_items = {'A': True}


    def stop_loop():
        # Stop existing timer if running
        if self._loop_timer is not None:
            self._loop_timer.stop()
            self._loop_timer.deleteLater()
            self._loop_timer = None
            print("Loop stopped")


    def set_img_by_index(val):
        # Stop existing timer if running
        stop_loop()
        
        val = int(val)
        images_path = get_path("video_frames") if os.listdir( get_path("video_frames") ) else get_path("frames")
        images_list = os.listdir(images_path)
        if not images_list:
            return
        
        # Map slider value (0-100) to image index (0 to len-1)
        max_index = len(images_list) - 1
        image_index = int((val / 100) * max_index)
        selected_image = images_list[image_index]
        image_path = os.path.join(images_path, selected_image)
        self.img.open_image(image_path)




    def loop_gif(fps=16):
        print("L pressed")
        
        # Stop existing timer if running
        stop_loop()
        

        self._loop_index = 0
        
        def next_frame():

            images_path = get_path("video_frames") if os.listdir( get_path("video_frames") ) else get_path("frames")

            # Refresh image list every frame to detect changes
            images_list = sorted([f for f in os.listdir(images_path) 
                                 if f.lower().endswith(('.jpg', ".jpeg", ".png"))])
            
            if not images_list:
                return
            
            # Wrap index if list size changed
            self._loop_index = self._loop_index % len(images_list)
            
            # Load current frame
            image_path = os.path.join(images_path, images_list[self._loop_index])
            self.img.open_image(image_path)
            ctx.update_item('A', "progress", (self._loop_index / len(images_list)) * 100 )
            
            # Move to next frame
            self._loop_index = (self._loop_index + 1) % len(images_list)
            
            # Dynamically adjust FPS based on directory
            current_fps = fps
            if images_path == get_path("frames"):
                current_fps = fps / 4
            
            # Update timer interval if it changed
            new_interval = int(1000 / current_fps)
            if self._loop_timer and self._loop_timer.interval() != new_interval:
                self._loop_timer.setInterval(new_interval)
        
        # Create and start timer
        self._loop_timer = QTimer()
        self._loop_timer.timeout.connect(next_frame)
        
        # Initial interval calculation
        initial_path = get_path("video_frames") if os.listdir( get_path("video_frames") ) else get_path("frames")
        initial_fps = fps if initial_path != get_path("frames") else fps / 4
        interval = int(1000 / initial_fps)
        
        self._loop_timer.start(interval)
        print(f"Loop started at {initial_fps} fps")
        
        # Show first frame immediately
        next_frame()

    
    def start_render():
        
        delete_all_files_in_folder( get_path('frames') )
        delete_all_files_in_folder( get_path('video_frames') )

        self.render_manager.send_render()
        
        loop_gif(fps=16)

    
    config.callbackL = {
        'A': lambda val: set_img_by_index(val),
        'R': lambda: start_render(),
        'L': lambda: loop_gif(),
        }


    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )

def execute_plugin(window):
    main(window)
