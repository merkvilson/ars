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
    if key == "steps":            res = opj(output,"steps")
    if key == "mesh":             res = opj(output,"mesh")
    if key == "keyframes":        res = opj(output,"keyframes")
    if key == "sprite":           res = opj(output,"sprite")    
    if key == "last_step":        res = last_step_path
    if key == "output":           res = output
    if key == "custom_nodes":     res = opj("extensions","comfyui")
    if key == "extra_model_yaml": res = opj(cui, "extra_model_paths.yaml")

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






yaml = f"\nairen:\n    base_path: {read_pref("extra_model_paths")}\n"

for new_path in os.listdir(read_pref("extra_model_paths")):
    yaml += f"    {new_path}: {new_path}\n"


yaml +=  f"\nairen_nodes:\n    base_path: {get_path("custom_nodes")}\n"
yaml += "    custom_nodes: custom_nodes"

with open(get_path("extra_model_yaml"), "w", encoding="utf-8") as file:
    file.write(yaml)