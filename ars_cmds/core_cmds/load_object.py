from PyQt6.QtWidgets import QFileDialog
import os
from ars_3d_engine.logic.scene_objects import CMesh
import trimesh 
import tempfile
from core.sound_manager import play_sound
from PyQt6.QtCore import QTimer
import time
from prefs.pref_controller import get_path

mesh_files = "(*.obj *.stl *.ply *.off *.dae *.glb *.gltf *.3mf)"

def process_mesh_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    needs_conversion = True
    if ext in ['.obj', '.stl', '.ply']:
        if ext != '.obj': needs_conversion = False
        else:
            # Check if OBJ needs triangulation
            needs_tri = False
            with open(file_path, 'r') as f:
                for line in f:
                    if line.startswith('f '):
                        parts = line.split()
                        if len(parts) > 4:
                            needs_tri = True
                            break
            needs_conversion = needs_tri
    
    if not needs_conversion:
        return file_path
    
    # Load with trimesh (which handles triangulation) and export to temp OBJ
    mesh = trimesh.load(file_path)
    temp_fd, temp_path = tempfile.mkstemp(suffix='.obj')
    os.close(temp_fd)
    mesh.export(temp_path)
    return temp_path

def add_mesh(self, file_path=None, animated=False):
    # Open file dialog for mesh selection
    if file_path is None:
        file_path, _ = QFileDialog.getOpenFileName(None, "Select Mesh", get_path("output"), f"Mesh Files {mesh_files}")
    
    # Exit if no file is selected
    if not file_path:
        print("No file selected.")
        return
    try:
        # Process the file (triangulate or convert if needed)
        processed_path = process_mesh_file(file_path)
        
        # Use file name (without extension) as mesh name
        name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Determine initial position
        initial_y = 2 if animated else 0
        
        # Create mesh object
        obj = CMesh.create(translate=(0, initial_y, 0), name=name, file_path=processed_path)

        # Add to viewport
        self.viewport._objectManager.add_object(obj)
        self.viewport._view.camera.view_changed()

        if animated:
            # Start the animation sequence after adding the object
            def start_animation():
                start_time = time.time()
                duration = 0.150
                
                timer = QTimer()
                
                def update_position():
                    elapsed = time.time() - start_time
                    if elapsed >= duration:
                        timer.stop()
                        obj.set_position(0, 0, 0)
                        play_sound("obj-drop-deep")
                        self.viewport._view.camera.view_changed()
                        return
                    
                    t = elapsed / duration
                    ease = t ** 2  # Ease-in quadratic
                    y = 2 - 2 * ease
                    obj.set_position(0, y, 0)
                    self.viewport._view.camera.view_changed()
                
                timer.timeout.connect(update_position)
                timer.start(10)  # Update every 10 ms for smooth animation
            
            # Wait 50 ms before starting the movement
            QTimer.singleShot(50, start_animation)

        print(f"Added mesh: {name}")
        return obj
    except Exception as e:
        print(f"Failed to add mesh: {e}")