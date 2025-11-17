import os
import uuid
import traceback
import importlib.util
from util_functions.ars_window import ars_window
from ars_cmds.core_cmds.load_object import selected_object, add_primitive

#finds and runs execute_plugin in the given file
def run_ext(path, window = None, edit_func=None):
    """Load & execute a Python source file at `path` (works with any extension).
    
    Args:
        path: File path to the Python script.
        ars_window: Object passed to the plugin's entrypoint.
        edit_func: Optional callable that takes raw file content (str) and returns edited content (str).
                   If None, no edits are applied.
    """
    if not os.path.isfile(path):
        print("File not found:", path)
        return

    # Make module name unique to avoid clashes
    module_name = f"ext_{uuid.uuid4().hex}"

    try:
        # Read raw content
        with open(path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        # Apply edits if provided
        content = edit_func(raw_content) if edit_func else raw_content

        # Create module
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        module = importlib.util.module_from_spec(spec)

        # Compile and execute the (edited) content in the module's namespace
        code_obj = compile(content, path, 'exec')
        exec(code_obj, module.__dict__)

        # Call the plugin entrypoint if it exists
        if hasattr(module, "execute_plugin"):
            module.execute_plugin(ars_window())
        else:
            print("execute_plugin() not found in", path)

    except SyntaxError as e:
        print(f"Syntax error in {path} (after edits): {e}")
        traceback.print_exc()
    except Exception:
        print("Failed to load/execute:")
        traceback.print_exc()


def run_string_code(code_string: str, namespace_injection: dict=None):
    """Execute raw Python code from a string.
    
    Args:
        code_string: The Python code to execute.
        ars_window: Object passed to the code's namespace.
    """
    try:

        # Create a unique module name
        module_name = f"ext_{uuid.uuid4().hex}"

        # Create module
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        module = importlib.util.module_from_spec(spec)

        # Inject useful objects into the module's namespace
        if namespace_injection:
            for key, value in namespace_injection.items():
                module.__dict__[key] = value

        # Compile and execute the code in the module's namespace
        code_obj = compile(code_string, '<string>', 'exec')
        exec(code_obj, module.__dict__)

    except SyntaxError as e:
        print(f"Syntax error in provided code string: {e}")
        traceback.print_exc()
    except Exception:
        print("Failed to execute code string:")
        traceback.print_exc()   