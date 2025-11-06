import subprocess
import os

# Path to your ComfyUI folder
comfy_path = "C:\\Airen_Engine\\CUI\\ComfyUI_windows_portable"
python_path = os.path.join(comfy_path, "python_embeded", "python.exe")

base_dir = (os.path.split(__file__)[0])

# Option 1: Install from requirements.txt
# Set this to the path of your requirements.txt file, or None to use package list
requirements_file = r"C:\Airen_Engine\AIREN_MODELS\custom_nodes\ComfyUI_FlashVSR-main\requirements.txt"




# Option 2: Install individual packages
packages = [
    "",
]

# Install from requirements.txt if specified
if requirements_file and os.path.exists(requirements_file):
    print(f"Installing packages from {requirements_file}...")
    subprocess.run([python_path, "-m", "pip", "install", "-r", requirements_file], check=True)
    print("Installation from requirements.txt completed!")

# Install individual packages
else:
    print("Installing individual packages...")
    for pkg in packages:
        print(f"Installing {pkg}...")
        subprocess.run([python_path, "-m", "pip", "install", "-U", pkg], check=True)
    print("Installation completed!")



