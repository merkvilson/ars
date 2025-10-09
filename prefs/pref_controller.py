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

    if key == "input": res = opj(cui,"input")
    if key == "steps": res = opj(output,"steps")
    if key == "output": res = output

    return res



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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    update_cui_root()
