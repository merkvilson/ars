"""
Bubble Commands Package.

This package automatically discovers and imports all modules within the
`ars_cmds/bubble_cmds` directory. It exposes all callable functions
from these modules directly under the `ars_cmds.bubble_cmds` namespace.

Usage:
    from ars_cmds.bubble_cmds import *
    # All functions defined in the modules of this folder are now available.
"""
import os
import importlib


# Dynamically import all .py files in this folder (except __init__.py)
package_dir = os.path.dirname(__file__)
for filename in os.listdir(package_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        module_name = filename[:-3]
        module = importlib.import_module(f"{__name__}.{module_name}")
        # Only import callable functions
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr):
                globals()[attr_name] = attr
