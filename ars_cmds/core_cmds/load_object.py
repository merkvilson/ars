from PyQt6.QtWidgets import QFileDialog
import os
from ars_3d_engine.mesh_objects.obj_mesh_loader import CMesh
from ars_3d_engine.mesh_objects.obj_sprite import CSprite
from ars_3d_engine.mesh_objects.obj_text import CText3D
from ars_3d_engine.mesh_objects.obj_primitive import CPrimitive
import trimesh 
import tempfile
from core.sound_manager import play_sound
from PyQt6.QtCore import QTimer
import time
from prefs.pref_controller import get_path
from ars_cmds.mesh_gen.animated_bbox import plane_fill_animation, delete_bbox_animations
from ars_3d_engine.mesh_objects.obj_point import CPoint
from util_functions.ars_window import ars_window

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

def add_mesh(file_path=None, animated=False):
    window = ars_window()
    # Open file dialog for mesh selection
    if file_path is None:
        file_path, _ = QFileDialog.getOpenFileName(None, "Select Mesh", get_path("output"), f"Mesh Files {mesh_files}")
    
    initial_y = 2 if animated else 0
    if file_path is None:
        print("No file path provided.")
        return
    
    elif isinstance(file_path, str):
        # Process the file (triangulate or convert if needed)
        processed_path = process_mesh_file(file_path)
        name = os.path.splitext(os.path.basename(file_path))[0]
        obj = CMesh.create(translate=(0, initial_y, 0), name=name, file_path=processed_path)
    else:
        obj = file_path
        name = obj.name
        
    # Add to viewport
    window.viewport._objectManager.add_object(obj)
    window.viewport._view.camera.view_changed()

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
                    window.viewport._view.camera.view_changed()
                    return
                
                t = elapsed / duration
                ease = t ** 2  # Ease-in quadratic
                y = 2 - 2 * ease
                obj.set_position(0, y, 0)
                window.viewport._view.camera.view_changed()
            
            timer.timeout.connect(update_position)
            timer.start(10)  # Update every 10 ms for smooth animation
        
        # Wait 50 ms before starting the movement
        QTimer.singleShot(50, start_animation)

    print(f"Added mesh: {name}")
    return obj



def add_sprite(size=(4.0, 4.0), color=(1.0, 1.0, 1.0, 0.3), name="Sprite", animated=False):
    window = ars_window()
    if animated:
        play_sound("bbox-in")

        grow_duration = 0.3
        plane_fill_animation(window.viewport._view.scene, grow_duration=grow_duration, count=4)
    else:
        grow_duration = 0

    obj = CSprite.create(size=size, color=color, name=name)
    def add_to_scene():
        delete_bbox_animations(window.viewport._view.scene)
        window.viewport._objectManager.add_object(obj)
        window.viewport._view.camera.view_changed()
        print(f"Added CSprite: {name}")

    QTimer.singleShot(int(grow_duration * 2000), add_to_scene)
    obj.set_shading(None)
    return obj

def add_text3d():
    window = ars_window()
    obj = CText3D.create()
    window.viewport._objectManager.add_object(obj)
    window.viewport._view.camera.view_changed()
    return obj

def add_point():
    window = ars_window()
    obj = CPoint.create()
    window.viewport._objectManager.add_object(obj)
    window.viewport._view.camera.view_changed()
    return obj

def add_primitive(primitive_type = "cube", **params, ):
    obj = CPrimitive.create(primitive_type,**params)
    animated = params.get("animated")
    obj.set_position(0, 2 if animated else 0, 0)
    return add_mesh(file_path=obj, animated=animated)

def selected_object():
    window = ars_window()
    selected = window.viewport._objectManager.get_selected_objects()
    if selected:
        return selected[0]
    return None