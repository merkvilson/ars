import os

from airen_paths import *


yaml = f"\nairen4d:\n    base_path: {airen_models_path}\n"

for new_path in os.listdir(airen_models_path):
	yaml += f"    {new_path}: {new_path}\n"


yaml +=  f"\nairen4d_nodes:\n    base_path: {os.path.dirname(airen_custom_nodes_path)}\n"
yaml += "    custom_nodes: airen_custom_nodes"

with open(extra_model_yaml, "w", encoding="utf-8") as file:
    file.write(yaml)