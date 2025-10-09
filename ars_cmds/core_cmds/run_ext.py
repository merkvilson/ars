import os
import uuid
import traceback
from importlib.machinery import SourceFileLoader
import importlib.util

def run_ext(path, ars_window):
    """Load & execute a Python source file at `path` (works with any extension)."""
    if not os.path.isfile(path):
        print("File not found:", path)
        return

    # make module name unique so repeated loads don't clash
    module_name = f"ext_{uuid.uuid4().hex}"

    try:
        loader = SourceFileLoader(module_name, path)
        spec = importlib.util.spec_from_loader(module_name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)   # executes the file as a module

        # call the plugin entrypoint if it exists
        if hasattr(module, "execute_plugin"):
            module.execute_plugin(ars_window)
        else:
            print("execute_plugin() not found in", path)

    except Exception:
        print("Failed to load with SourceFileLoader:")
        traceback.print_exc()



"""
#runs py scripts
import importlib

def run_ext(path, self):

    # Load module dynamically each time
    spec = importlib.util.spec_from_file_location("ext", path)
    ext = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ext)

    # Call the function from the external file
    ext.execute_plugin(self)
"""