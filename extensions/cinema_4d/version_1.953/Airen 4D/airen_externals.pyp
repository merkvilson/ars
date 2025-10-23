import os 
import c4d
import subprocess

import base64 as b, types as t, zlib as z; m=t.ModuleType('localimport');
with open(os.path.join(os.path.split(__file__)[0], "modules","localimport"), 'r') as file: content = file.read()
m.__file__ = __file__; blob=content
exec(z.decompress(b.b64decode(blob)), vars(m)); _localimport=m;localimport=getattr(m,"localimport")
del blob, b, t, z, m;

with localimport('modules'): 
    from airen_paths import *
    from plugin_ids  import *
    from airen_cmds  import *
    from cst_paths   import *

try:
    vram_result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free", "--format=csv,noheader,nounits"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    vram_total, vram_used, vram_free = map(int, vram_result.stdout.strip().split(", "))
    print(f"Total VRAM: {vram_total} MB")
    print(f"Used VRAM: {vram_used} MB")
    print(f"Free VRAM: {vram_free} MB")
except FileNotFoundError:
    print("nvidia-smi not found. Make sure NVIDIA drivers are installed.")
    vram_total = 0


def start_bat(NVIDIA_GPU = True, NO_WINDOW = False):
    # Change directory to the script location
    os.chdir(os.path.join(airen_root_path, "CUI", user_comfy_ui))

    # Path to the Python interpreter
    python_interpreter = r".\python_embeded\python.exe"

    # Path to the main.py script
    script_path = "ComfyUI\main.py"

    if NVIDIA_GPU: command = [python_interpreter, "-s", script_path, "--windows-standalone-build"]
    else:          command = [python_interpreter, "-s", script_path, "--cpu", "--windows-standalone-build"]

    # Execute the command asynchronously and hide the window
    if NO_WINDOW: subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
    else: subprocess.Popen(command)





class C_AIREN_EXTERNAL(c4d.plugins.CommandData):
    server_started = False

    def Execute(self, doc):

        key_bc = c4d.BaseContainer()
        if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.BFM_INPUT_CHANNEL, key_bc):
            if key_bc[c4d.BFM_INPUT_QUALIFIER] & c4d.QSHIFT or vram_total < 6000: 
                start_bat(NVIDIA_GPU=False)
            else: start_bat(NVIDIA_GPU=True)

        print("start_bat")

        return True





if __name__ == "__main__":

    dir = os.path.split(__file__)[0]
    def ico(name):
        bmp = c4d.bitmaps.BaseBitmap()  
        bmp.InitWith(os.path.join(dir, "res", "icons", f"{name}.png") )
        return bmp

    c4d.plugins.RegisterCommandPlugin (AI_C_EXTERNAL , "external", 134217728, ico("folder"), "", C_AIREN_EXTERNAL())