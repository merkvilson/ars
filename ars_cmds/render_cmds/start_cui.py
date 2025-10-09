import os
from os.path import join as opj
from prefs.pref_controller import read_pref
import subprocess

cui_root = read_pref(key = "cui_root")

def start_bat(NVIDIA_GPU = True, NO_WINDOW = False):
    # Change directory to the script location
    #os.chdir(os.path.join(airen_root_path, "CUI", user_comfy_ui))

    # Path to the Python interpreter
    python_interpreter = r".\python_embeded\python.exe"
    python_interpreter = opj(cui_root, "python_embeded","python.exe")

    # Path to the main.py script
    script_path = opj(cui_root, "ComfyUI", "main.py")

    if NVIDIA_GPU: command = [python_interpreter, "-s", script_path, "--windows-standalone-build"]
    else:          command = [python_interpreter, "-s", script_path, "--cpu", "--windows-standalone-build"]

    # Execute the command asynchronously and hide the window
    if NO_WINDOW: subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
    else: subprocess.Popen(command)



