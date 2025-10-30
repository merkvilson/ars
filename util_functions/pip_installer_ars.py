import subprocess
import os

# Path to your ComfyUI folder
comfy_path = "C:\\Airen_Engine\\CUI\\ComfyUI_windows_portable"
python_path = os.path.join(comfy_path, "python_embeded", "python.exe")


base_dir = (os.path.split(__file__)[0])

packages = [
"pynanoinstantmeshes",

]


for pkg in packages:
    subprocess.run([python_path, "-m", "pip", "install", pkg], check=True)


