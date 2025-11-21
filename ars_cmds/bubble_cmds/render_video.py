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
from ars_cmds.core_cmds.key_check import key_check_continuous
from PIL import Image
from collections import Counter

BBL_VIDEO_CONFIG = {"symbol": ic.ICON_PLAYER_TRACK_NEXT}
def BBL_VIDEO(*args):
    run_ext(__file__)

def execute_plugin(ars_window):
    
    # Timer and state for play_video
    if not hasattr(ars_window, '_loop_timer'):
        ars_window._loop_timer = None
    if not hasattr(ars_window, '_loop_index'):
        ars_window._loop_index = 0

    def get_valid_layers(tiff_path):
        try:
            img = Image.open(tiff_path)
        except:
            return []
        valid_layers = []
        sizes = []
        n_frames = getattr(img, 'n_frames', 1)
        for i in range(n_frames):
            img.seek(i)
            sizes.append(img.size)
        
        if not sizes: return []
        # Find most common size
        most_common_size = Counter(sizes).most_common(1)[0][0]
        
        for i in range(n_frames):
            if sizes[i] == most_common_size:
                valid_layers.append(i)
                
        return valid_layers

    def get_cached_sequence():
        # Check for files first
        v_frames = get_path("video_frames")
        frames = get_path("frames")
        
        if (os.path.exists(v_frames) and os.listdir(v_frames)) or (os.path.exists(frames) and os.listdir(frames)):
            return None # Use file mode
            
        # Check for TIFFs
        input_path = get_path("input")
        tiff1 = os.path.join(input_path, "1.tiff")
        tiff2 = os.path.join(input_path, "2.tiff")
        
        if not (os.path.exists(tiff1) and os.path.exists(tiff2)):
            return None

        # Check mtimes
        mtime1 = os.path.getmtime(tiff1)
        mtime2 = os.path.getmtime(tiff2)
        
        if (hasattr(ars_window, '_tiff_cache') and 
            ars_window._tiff_cache['mtime1'] == mtime1 and 
            ars_window._tiff_cache['mtime2'] == mtime2):
            return ars_window._tiff_cache['sequence']
            
        # Recompute
        layers1 = get_valid_layers(tiff1)
        layers2 = get_valid_layers(tiff2)
        
        if layers1 and layers2:
            # 1.tiff: last(small) -> first
            seq1 = [(tiff1, l) for l in reversed(layers1)]
            # 2.tiff: first -> last(small)
            seq2 = [(tiff2, l) for l in layers2]
            sequence = seq1 + seq2
            ars_window._tiff_cache = {
                'mtime1': mtime1,
                'mtime2': mtime2,
                'sequence': sequence
            }
            return sequence
            
        return None


    config = ContextMenuConfig()
    config.use_extended_shape_items = {"timeline": (ars_window.width() / (40), 1)} #40 stands for item diameter
    config.hover_scale_items = {"timeline": 0.95}
    config.auto_close = False
    config.close_on_outside = False
    config.use_extended_shape = False
    config.extra_distance = [0,99999]
    config.distribution_mode = "x"
    config.custom_height = 110
    #config.custom_width = 450


    options_list=    [
        ["   ", "timeline", "   ",],
        [
        "   ", 
        ic.ICON_RENDER, 
        "   ",
        #ic.ICON_PLAYER_TRACK_BACK,
        ic.ICON_PLAYER_SKIP_BACK, 
        ic.ICON_PLAYER_PLAY, 
        ic.ICON_PLAYER_SKIP_FORWARD, 
        #ic.ICON_PLAYER_TRACK_NEXT,
        "   ",
        ic.ICON_SPEED_UP,
        "   ",
        ]
        ]
    config.expand = "x"
    

    config.slider_values = {
        "timeline": (0, 100, 50),
        ic.ICON_SPEED_UP: (1, 60, 30),
    }
    config.incremental_values = {
        ic.ICON_SPEED_UP: 1,
    }
    config.per_item_radius = { "timeline": 20,}


    def pause_video():
        # Stop existing timer if running
        if ars_window._loop_timer is not None:
            ars_window._loop_timer.stop()
            ars_window._loop_timer.deleteLater()
            ars_window._loop_timer = None
            print("Loop stopped")
            ctx.update_item(ic.ICON_PLAYER_PAUSE, "symbol", ic.ICON_PLAYER_PLAY)

            return True
        


    def set_img_by_index(val):
        # Stop existing timer if running
        pause_video()
        
        val = int(val)

        sequence = get_cached_sequence()
        if sequence:
            max_index = len(sequence) - 1
            image_index = int((val / 100) * max_index)
            path, layer = sequence[image_index]
            ars_window.img.open_image(path, layer=layer, auto_fit=False)
            ars_window._loop_index = image_index
            return

        images_path = get_path("video_frames") if os.listdir( get_path("video_frames") ) else get_path("frames")
        images_list = os.listdir(images_path)
        if not images_list:
            return
        
        # Map slider value (0-100) to image index (0 to len-1)
        max_index = len(images_list) - 1
        image_index = int((val / 100) * max_index)
        selected_image = images_list[image_index]
        image_path = os.path.join(images_path, selected_image)
        ars_window.img.open_image(image_path, auto_fit=False)

        ars_window._loop_index = image_index



    ars_window._loop_index = 0

    def play_video():

        if pause_video(): return

        ctx.update_item(ic.ICON_PLAYER_PLAY, "symbol", ic.ICON_PLAYER_PAUSE)

        fps = ctx.get_value(ic.ICON_SPEED_UP)
        
        
        def frame_next():
            sequence = get_cached_sequence()
            
            if sequence:
                # Wrap index if list size changed
                ars_window._loop_index = ars_window._loop_index % len(sequence)
                
                path, layer = sequence[ars_window._loop_index]
                ars_window.img.open_image(path, layer=layer, auto_fit=False)
                ctx.update_item("timeline", "progress", (ars_window._loop_index / len(sequence)) * 100 )
                
                ars_window._loop_index = (ars_window._loop_index + 1) % len(sequence)
                
                current_fps = ctx.get_value(ic.ICON_SPEED_UP)
                new_interval = int(1000 / current_fps)
                if ars_window._loop_timer and ars_window._loop_timer.interval() != new_interval:
                    ars_window._loop_timer.setInterval(new_interval)
                return

            images_path = get_path("video_frames") if os.listdir( get_path("video_frames") ) else get_path("frames")

            # Refresh image list every frame to detect changes
            images_list = sorted([f for f in os.listdir(images_path) 
                                 if f.lower().endswith(('.jpg', ".jpeg", ".png"))])
            
            if not images_list:
                return
            
            # Wrap index if list size changed
            ars_window._loop_index = ars_window._loop_index % len(images_list)
            
            # Load current frame
            image_path = os.path.join(images_path, images_list[ars_window._loop_index])
            ars_window.img.open_image(image_path, auto_fit=False)
            ctx.update_item("timeline", "progress", (ars_window._loop_index / len(images_list)) * 100 )
            
            # Move to next frame
            ars_window._loop_index = (ars_window._loop_index + 1) % len(images_list)
            
            # Dynamically adjust FPS based on directory
            current_fps = ctx.get_value(ic.ICON_SPEED_UP)
            if images_path == get_path("frames"):
                current_fps = ctx.get_value(ic.ICON_SPEED_UP) / 4

            # Update timer interval if it changed
            new_interval = int(1000 / current_fps)
            if ars_window._loop_timer and ars_window._loop_timer.interval() != new_interval:
                ars_window._loop_timer.setInterval(new_interval)
        
        # Create and start timer
        ars_window._loop_timer = QTimer()
        ars_window._loop_timer.timeout.connect(frame_next)
        
        # Initial interval calculation
        sequence = get_cached_sequence()
        if sequence:
            initial_fps = fps
        else:
            initial_path = get_path("video_frames") if os.listdir( get_path("video_frames") ) else get_path("frames")
            initial_fps = fps if initial_path != get_path("frames") else fps / 4
        
        interval = int(1000 / initial_fps)
        
        ars_window._loop_timer.start(interval)
        print(f"Loop started at {initial_fps} fps")
        
        # Show first frame immediately
        frame_next()

        

    
    def start_render():
        
        delete_all_files_in_folder( get_path('frames') )
        delete_all_files_in_folder( get_path('video_frames') )

        ars_window.render_manager.send_render()
        
        play_video()

    def frame_next():
        frame = ctx.get_value("timeline")
        set_img_by_index(frame + 1)
        ctx.update_item("timeline", "progress", frame + 1)

    def frame_back():
        frame = ctx.get_value("timeline")
        set_img_by_index(frame - 1)
        ctx.update_item("timeline", "progress", frame - 1)

    config.callbackL = {
        "timeline": lambda val: set_img_by_index(val),
        ic.ICON_RENDER: lambda: start_render(),

        ic.ICON_PLAYER_SKIP_BACK: lambda: key_check_continuous(callback=frame_back,),
        ic.ICON_PLAYER_SKIP_FORWARD: lambda: key_check_continuous(callback=frame_next,),

        ic.ICON_PLAYER_PLAY: lambda: play_video(),
        }


    ctx = open_context(
        items=options_list,
        config=config
    )
