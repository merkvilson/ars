import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QFileDialog
import os
from os.path import join as opj

json_file = Path(os.path.join("prefs", "paths.json"))

def read_pref(key = "cui_root"):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        res = data.get(key)
        if res:
            return res






def get_path(key = "image"):

    cui_root = read_pref(key = "cui_root")
    cui      = opj(cui_root, "ComfyUI")
    output   = opj(cui,  "output")

    last_step_path = ""
    if os.path.exists(opj(output,"steps")):
        files = [f for f in os.listdir(opj(output,"steps"))]
        if files:
            full_paths = [opj(opj(output,"steps"), f) for f in files]
            last_step_path = max(full_paths, key=os.path.getmtime)

    if key == "image": res = opj(output,"images")

    if key == "input":            res = opj(cui,"input")
    if key == "mesh":             res = opj(output,"mesh")
    if key == "steps":            res = opj(output,"steps")
    if key == "frames":           res = opj(output,"frames")
    if key == "video_frames":     res = opj(output,"video_frames")
    if key == "keyframes":        res = opj(output,"keyframes")
    if key == "sprite":           res = opj(output,"sprite")
    if key == "last_step":        
        if last_step_path:
            return last_step_path  # Return the file path directly without abspath
        else:
            return ""  # Return empty string if no file exists
    if key == "output":           res = output
    if key == "custom_nodes":     res = opj("extensions","comfyui")
    if key == "extra_model_yaml": 
        return os.path.abspath(opj(cui, "extra_model_paths.yaml"))  # Just return the file path, don't create directories

    if not os.path.exists(res):
        os.makedirs(res, exist_ok=True)

    return os.path.abspath(res)





def edit_pref(key = "cui_root", value = ""):

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Open folder selection dialog
    folder = QFileDialog.getExistingDirectory(None, "Select Comfy UI Root Folder")

    if folder:  # User didn't cancel
        data[key] = folder.replace("/", "\\")  # Keep Windows-style backslashes

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        print(f"Updated {key}:\n{folder}")




yaml = ""
if read_pref("extra_model_paths") and os.path.exists(read_pref("extra_model_paths")):
    yaml = f"airen:\n    base_path: {read_pref('extra_model_paths')}\n"
    for new_path in os.listdir(read_pref("extra_model_paths")):
        yaml += f"    {new_path}: {new_path}\n"

yaml += f"\nairen_nodes:\n    base_path: {get_path('custom_nodes')}\n"
yaml += "    custom_nodes: custom_nodes"

try:
    with open(get_path("extra_model_yaml"), "w", encoding="utf-8") as file:
        file.write(yaml)
except PermissionError:
    # Force create the file by trying alternative methods
    import subprocess
    yaml_path = get_path("extra_model_yaml")
    temp_file = yaml_path + ".tmp"
    
    try:
        # Write to temp file first
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(yaml)
        
        # Use Windows commands to force move
        subprocess.run(f'move "{temp_file}" "{yaml_path}"', shell=True, check=False)
        
        # If that fails, try copy and delete
        if not os.path.exists(yaml_path):
            subprocess.run(f'copy "{temp_file}" "{yaml_path}"', shell=True, check=False)
            os.remove(temp_file)
            
    except:
        # Last resort - write to desktop and show message
        desktop_file = os.path.join(os.path.expanduser("~"), "Desktop", "extra_model_paths.yaml")
        with open(desktop_file, "w", encoding="utf-8") as f:
            f.write(yaml)
        print(f"File created on desktop: {desktop_file}")
        print(f"Copy it to: {yaml_path}")