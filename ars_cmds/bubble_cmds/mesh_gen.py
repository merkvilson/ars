from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
import os
from prefs.pref_controller import get_path
from PyQt6.QtCore import QFileSystemWatcher
from ars_cmds.core_cmds.load_object import add_mesh

def BBL_4(self, position):
    run_ext(__file__, self)

def main(self):

    self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "mesh.json")),

    mesh_dir = get_path("mesh")

    config = ContextMenuConfig()
    config.auto_close = False
    config.close_on_outside = False
    options_list = [
        ["1", "2", "3",],
    ]

    def generate_mesh():
        ctx.update_item("1", "progress_bar", 1)
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
        
        def on_directory_changed(path):
            current_files = set(os.listdir(mesh_dir))
            new_files = current_files - initial_files
            
            if new_files:
                # New file detected
                new_file = new_files.pop()
                print(f"New file detected: {new_file}")
                ctx.update_item("1", "progress_bar", 0)
                add_mesh(self, os.path.join(mesh_dir, new_file), animated=True)
                
                # Stop watching after detecting new file
                self._mesh_watcher.directoryChanged.disconnect(on_directory_changed)
                self._mesh_watcher.removePath(mesh_dir)
        
        # Connect the signal to the handler
        self._mesh_watcher.directoryChanged.connect(on_directory_changed)

    config.callbackL = {"1": lambda: generate_mesh(),
                        "2": lambda: self.render_manager.set_userdata("seed", self.render_manager.get_userdata("seed")+1),
                        }
    
    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )

def execute_plugin(window):
    main(window)