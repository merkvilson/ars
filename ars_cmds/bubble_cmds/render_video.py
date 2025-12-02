"""
This module provides functionality for rendering and playing back video sequences.
"""
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
from ars_cmds.bubble_cmds.open_keyframes import BBL_KEYFRAMES as open_keyframes
from ars_cmds.bubble_cmds.prompt_editor_cmd import BBL_P as open_prompt_editor

BBL_VIDEO_CONFIG = {"symbol": ic.ICON_PLAYER_TRACK_NEXT}
def BBL_VIDEO(*args):
    """
    Entry point for the video bubble command.
    Runs the current file as an extension.
    """
    run_ext(__file__)

def execute_cmd(ars_window):
    """
    Executes the video player/renderer plugin.
    
    Sets up the context menu for video control, including timeline, playback controls,
    and rendering options. Handles image sequence loading and caching.
    
    Args:
        ars_window: The main application window instance.
    """

    #Prepare GUI
    ars_window.viewport.hide()
    ars_window.img.show()

    # Timer and state for play_video
    if not hasattr(ars_window, '_loop_timer'):
        ars_window._loop_timer = None
    if not hasattr(ars_window, '_loop_index'):
        ars_window._loop_index = 0
    if not hasattr(ars_window, '_last_source_type'):
        ars_window._last_source_type = None

    def check_source_changed(new_type):
        """
        Checks if the video source type has changed.
        
        Args:
            new_type: The new source type identifier.
            
        Returns:
            bool: True if the source type changed, False otherwise.
        """
        if ars_window._last_source_type != new_type:
            ars_window._last_source_type = new_type
            return True
        return False

    def get_valid_layers(tiff_path):
        """
        Extracts valid layer indices from a multi-page TIFF file.
        
        Identifies layers with the most common size to ensure consistency.
        
        Args:
            tiff_path (str): Path to the TIFF file.
            
        Returns:
            list: A list of valid layer indices.
        """
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
        """
        Retrieves the cached image sequence or generates a new one.
        
        Prioritizes file-based sequences (video_frames/frames) over TIFF sequences.
        Caches TIFF sequences based on file modification times.
        
        Returns:
            list or None: A list of (path, layer) tuples for the sequence, or None if using file mode.
        """
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
    config.incremental_value = True
    config.incremental_values = {"timeline": False,}
    #config.custom_width = 450


    options_list=    [
        [
        "   ", 
        ic.ICON_RENDER, 
        ic.ICON_STEPS,
        ic.ICON_GIZMO_SCALE,
        ic.ICON_TXT_FONT,
        "   ",
        #ic.ICON_PLAYER_TRACK_BACK,
        ic.ICON_PLAYER_SKIP_BACK, 
        ic.ICON_PLAYER_PLAY, 
        ic.ICON_PLAYER_SKIP_FORWARD, 
        #ic.ICON_PLAYER_TRACK_NEXT,
        "   ",
        ic.ICON_SPEED_UP,
        ic.ICON_SIZE,
        ic.ICON_WINDOW_FULLSCREEN,
        ic.ICON_TRASH_X,
        "   ",
        ],
        ["   ", "timeline", "   ",],
        ]
    config.expand = "x"
    

    config.slider_values = {
        "timeline": (0, 100, ars_window.prefs.timeline_frame),
        ic.ICON_GIZMO_SCALE: (25, 1024, ars_window.prefs.timeline_resolution),
        ic.ICON_SPEED_UP: (1, 60, ars_window.prefs.timeline_fps),
        ic.ICON_STEPS: (1, 50, ars_window.prefs.timeline_steps),
    }
    config.per_item_radius = { "timeline": 20,}


    def pause_video():
        """
        Pauses video playback.
        
        Stops the loop timer and updates the play/pause icon.
        
        Returns:
            bool: True if video was paused, False otherwise.
        """
        # Stop existing timer if running
        if ars_window._loop_timer is not None:
            ars_window._loop_timer.stop()
            ars_window._loop_timer.deleteLater()
            ars_window._loop_timer = None
            print("Loop stopped")
            ctx.update_item(ic.ICON_PLAYER_PAUSE, "symbol", ic.ICON_PLAYER_PLAY)

            return True
        


    def set_img_by_index(val):
        """
        Sets the current image based on a timeline value (0-100).
        
        Pauses playback and updates the displayed image.
        
        Args:
            val (float): The timeline value (0-100).
        """
        # Stop existing timer if running
        pause_video()
        
        val = int(val)

        sequence = get_cached_sequence()
        if sequence:
            should_fit = check_source_changed("tiff_sequence")
            max_index = len(sequence) - 1
            image_index = int((val / 100) * max_index)
            path, layer = sequence[image_index]
            ars_window.img.open_image(path, layer=layer, auto_fit=should_fit)
            ars_window._loop_index = image_index
            return

        images_path = get_path("video_frames") if os.listdir( get_path("video_frames") ) else get_path("frames")
        should_fit = check_source_changed(images_path)
        images_list = os.listdir(images_path)
        if not images_list:
            return
        
        # Map slider value (0-100) to image index (0 to len-1)
        max_index = len(images_list) - 1
        image_index = int((val / 100) * max_index)
        selected_image = images_list[image_index]
        image_path = os.path.join(images_path, selected_image)
        ars_window.img.open_image(image_path, auto_fit=should_fit)

        ars_window._loop_index = image_index



    ars_window._loop_index = 0

    def play_video():
        """
        Toggles video playback.
        
        Starts or stops the playback timer. Handles frame updates and FPS adjustments.
        """

        if pause_video(): return

        ctx.update_item(ic.ICON_PLAYER_PLAY, "symbol", ic.ICON_PLAYER_PAUSE)

        fps = ctx.get_value(ic.ICON_SPEED_UP)
        
        
        def frame_next():
            """
            Advances to the next frame in the sequence.
            
            Updates the displayed image and timeline progress.
            """
            sequence = get_cached_sequence()
            
            if sequence:
                should_fit = check_source_changed("tiff_sequence")
                # Wrap index if list size changed
                ars_window._loop_index = ars_window._loop_index % len(sequence)
                
                path, layer = sequence[ars_window._loop_index]
                ars_window.img.open_image(path, layer=layer, auto_fit=should_fit)
                ctx.update_item("timeline", "progress", (ars_window._loop_index / len(sequence)) * 100 )
                
                ars_window._loop_index = (ars_window._loop_index + 1) % len(sequence)
                
                current_fps = ctx.get_value(ic.ICON_SPEED_UP)
                new_interval = int(1000 / current_fps)
                if ars_window._loop_timer and ars_window._loop_timer.interval() != new_interval:
                    ars_window._loop_timer.setInterval(new_interval)
                return

            images_path = get_path("video_frames") if os.listdir( get_path("video_frames") ) else get_path("frames")
            should_fit = check_source_changed(images_path)

            # Refresh image list every frame to detect changes
            images_list = sorted([f for f in os.listdir(images_path) 
                                 if f.lower().endswith(('.jpg', ".jpeg", ".png"))])
            
            if not images_list:
                return
            
            # Wrap index if list size changed
            ars_window._loop_index = ars_window._loop_index % len(images_list)
            
            # Load current frame
            image_path = os.path.join(images_path, images_list[ars_window._loop_index])
            ars_window.img.open_image(image_path, auto_fit=should_fit)
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
        """
        Initiates the video rendering process.
        
        Sets up the render manager, clears old frames, sends the render request,
        and starts playback.
        """
        ars_window.render_manager.set_workflow("video")
        ars_window.render_manager.set_ud('steps', ctx.get_value(ic.ICON_STEPS))
        ars_window.render_manager.set_ud('steps_noise', int(ctx.get_value(ic.ICON_STEPS)/2))
        ars_window.render_manager.set_ud('size', ctx.get_value(ic.ICON_GIZMO_SCALE))
        ars_window.render_manager.set_ud('seed', 1)
        ars_window.render_manager.set_ud('length', 81)
        ars_window.render_manager.set_ud('positive', ars_window.prefs.render_prompt)
        ars_window.render_manager.set_ud('fps', ctx.get_value(ic.ICON_SPEED_UP))
        # Check if second image exists and disconnect if missing
        input_path = get_path("input")
        tiff2 = os.path.join(input_path, "2.tiff")
        
        if not os.path.exists(tiff2):
            workflow = ars_window.render_manager.workflow_template
            for node_id, node in workflow.items():
                if node.get("class_type") == "WanFirstLastFrameToVideo":
                    if "end_image" in node["inputs"]:
                        del node["inputs"]["end_image"]
                    break

        delete_all_files_in_folder( get_path('frames') )
        delete_all_files_in_folder( get_path('video_frames') )

        ars_window.render_manager.send_render()
        
        play_video()

    def frame_next():
        """Advances the timeline by one frame."""
        frame = ctx.get_value("timeline")
        set_img_by_index(frame + 1)
        ctx.update_item("timeline", "progress", frame + 1)

    def frame_back():
        """Moves the timeline back by one frame."""
        frame = ctx.get_value("timeline")
        set_img_by_index(frame - 1)
        ctx.update_item("timeline", "progress", frame - 1)

    config.callbackL = {
        "timeline": lambda val:( 
            set_img_by_index(val), 
            setattr(ars_window.prefs, 'timeline_frame', int(val)),
            ),
        ic.ICON_RENDER: lambda: start_render(),
        ic.ICON_PLAYER_SKIP_BACK: lambda: key_check_continuous(callback=frame_back,),
        ic.ICON_PLAYER_SKIP_FORWARD: lambda: key_check_continuous(callback=frame_next,),
        ic.ICON_PLAYER_PLAY: lambda: play_video(),
        ic.ICON_SPEED_UP: lambda val: setattr(ars_window.prefs, 'timeline_fps', int(val)),
        ic.ICON_GIZMO_SCALE: lambda val: setattr(ars_window.prefs, 'timeline_resolution', int(val)),
        ic.ICON_STEPS: lambda val: setattr(ars_window.prefs, 'timeline_steps', int(val)),
        ic.ICON_SIZE: lambda: open_keyframes(ars_window),
        ic.ICON_WINDOW_FULLSCREEN: lambda: ars_window.img.fit_image(),
        ic.ICON_TXT_FONT: lambda: open_prompt_editor(ars_window),
        ic.ICON_TRASH_X: lambda: ars_window.img.clear_image()
        }


    ctx = open_context(
        items=options_list,
        config=config
    )
