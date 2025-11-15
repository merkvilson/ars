import os
import subprocess
import platform

def open_file(path):
    """Open a file in its default editor/viewer."""
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    system = platform.system()

    try:
        if system == "Windows":
            os.startfile(path)  # Windows built-in
        elif system == "Darwin":  # macOS
            subprocess.run(["open", path])
        else:  # Linux or other UNIX-like
            subprocess.run(["xdg-open", path])
        print(f"Opened: {path}")
    except Exception as e:
        print(f"Failed to open file: {e}")