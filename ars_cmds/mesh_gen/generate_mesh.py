from theme.fonts import font_icons as ic
from PyQt6.QtCore import QFileSystemWatcher, QTimer
import os
from prefs.pref_controller import get_path
from ars_cmds.core_cmds.load_object import add_mesh

from ars_cmds.mesh_gen.animated_bbox import bbox_loading_animation, remove_bbox_loading_animation, delete_bbox_animations
from ars_cmds.render_cmds.check import check_queue

def generate_mesh(self, ctx):
    delete_bbox_animations(self.viewport._view.scene)
    
    self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "mesh.json")),


    timer = bbox_loading_animation(self.viewport._view.scene)

    ctx.update_item(ic.ICON_RENDER , "progress_bar", 1)
    #self.render_manager.set_userdata("resolution", ctx.get_value("3"))
    self.render_manager.send_render()
    mesh_dir = get_path("mesh")

    os.makedirs(mesh_dir, exist_ok=True)    # Ensure the mesh directory exists
    
    # Get initial list of files in the directory
    initial_files = set(os.listdir(mesh_dir))
    
    print(f"Monitoring directory: {mesh_dir}")
    
    # Create a file system watcher and store it as an attribute
    if not hasattr(self, '_mesh_watcher'):
        self._mesh_watcher = QFileSystemWatcher()
    
    # Disconnect all previous signals to avoid duplicate triggers
    try:
        self._mesh_watcher.directoryChanged.disconnect()
    except TypeError:
        # No connections exist yet
        pass
    
    # Clear any existing paths and add the new one
    if self._mesh_watcher.directories():
        self._mesh_watcher.removePaths(self._mesh_watcher.directories())
    
    self._mesh_watcher.addPath(mesh_dir)
    
    # Create a polling timer to check queue status
    queue_check_timer = QTimer()
    queue_check_timer.setInterval(1000)  # Check every 1 second
    
    def cleanup():
        """Clean up timers and watchers"""
        try:
            self._mesh_watcher.directoryChanged.disconnect(on_directory_changed)
        except TypeError:
            pass
        if self._mesh_watcher.directories():
            self._mesh_watcher.removePath(mesh_dir)
        queue_check_timer.stop()
        ctx.update_item(ic.ICON_RENDER, "progress_bar", 0)
        remove_bbox_loading_animation(timer)
    
    def check_queue_status():
        """Periodically check if queue is empty (generation completed or skipped)"""
        if check_queue() == 0:
            # Queue is empty, check if new file was created
            current_files = set(os.listdir(mesh_dir))
            new_files = current_files - initial_files
            
            if new_files:
                # New file was created
                new_file = new_files.pop()
                print(f"New file detected: {new_file}")
                if add_mesh(self, os.path.join(mesh_dir, new_file), animated=False): cleanup()
                
            else:
                # Queue is empty but no new file = generation was skipped
                print("Generation skipped (likely duplicate prompt)")
                cleanup()
    
    def on_directory_changed(path):
        """Handle directory changes (fast detection when file is created)"""
        current_files = set(os.listdir(mesh_dir))
        new_files = current_files - initial_files
        
        if new_files:
            # New file detected
            new_file = new_files.pop()
            print(f"New file detected: {new_file}")
            cleanup()
            mesh = add_mesh(self, os.path.join(mesh_dir, new_file), animated=False)
            mesh.set_scale((2,2,2))
    # Connect signals
    self._mesh_watcher.directoryChanged.connect(on_directory_changed)
    queue_check_timer.timeout.connect(check_queue_status)
    
    # Start polling timer
    queue_check_timer.start()