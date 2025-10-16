# Custom nodes for user data input in ComfyUI.
# No input sockets, only outputs. Widgets for user entry.
# Note for AI: Every node must have a ud_name input.

import os
import folder_paths
from PIL import Image
import numpy as np
import torch
import hashlib

class Airen_Str:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ud_name": ("STRING", {"default": "", "multiline": False}),
                "output": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "execute"
    CATEGORY = "Airen_Studio"
    OUTPUT_NODE = True

    def execute(self, ud_name, output):
        return (output,)

class Airen_Int:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ud_name": ("STRING", {"default": "", "multiline": False}),
                "output": ("INT", {"default": 0, "min": -999999, "max": 999999, "step": 1}),
            }
        }

    RETURN_TYPES = ("INT",)
    FUNCTION = "execute"
    CATEGORY = "Airen_Studio"
    OUTPUT_NODE = True

    def execute(self, ud_name, output):
        return (output,)

class Airen_Checkpoint_String:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ud_name": ("STRING", {"default": "", "multiline": False}),
                "output": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = (folder_paths.get_filename_list("checkpoints"),)
    RETURN_NAMES = ("output",)
    FUNCTION = "execute"
    CATEGORY = "Airen_Studio"

    def execute(self, ud_name, output):
        return (output,)

class Airen_VAE_String:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ud_name": ("STRING", {"default": "", "multiline": False}),
                "vae_name": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = (folder_paths.get_filename_list("vae"),)
    RETURN_NAMES = ("vae_name",)
    FUNCTION = "execute"
    CATEGORY = "Airen_Studio"

    def execute(self, ud_name, vae_name):
        return (vae_name,)

class Airen_Lora_String:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ud_name": ("STRING", {"default": "", "multiline": False}),
                "lora_name": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = (folder_paths.get_filename_list("loras"),)
    RETURN_NAMES = ("lora_name",)
    FUNCTION = "execute"
    CATEGORY = "Airen_Studio"

    def execute(self, ud_name, lora_name):
        return (lora_name,)

class Airen_SaveImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ud_name": ("STRING", {"default": "", "multiline": False}),
                "images": ("IMAGE", ),
                "category": (["2d", "3d", "bg", "dome", "mesh", "sprite", "steps", "texture"], ),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "Airen_Studio"

    def save_images(self, ud_name, images, category):
        output_dir = folder_paths.get_output_directory()
        filename_prefix = f"{category}/Airen"
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, output_dir, images[0].shape[1], images[0].shape[0])
        results = []
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            file = f"{filename}_{counter:05}_.png"
            img.save(os.path.join(full_output_folder, file), compress_level=4)
            results.append({"filename": file, "subfolder": subfolder, "type": "output"})
            counter += 1
        return {"ui": {"images": results}}


class Airen_InfoGetter:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ud_name": ("STRING", {"default": "", "multiline": False}),
                "weight": ("INT", {"default": 10, "min": 1, "max": 100, "step": 1}),      
                "output": ("*", ),
            }
        }

    RETURN_TYPES = ()
    CATEGORY = "Airen_Studio"
    OUTPUT_NODE = False


class Airen_RenderPass:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ud_name": ("STRING", {"default": "", "multiline": False}),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("render", "depth")
    FUNCTION = "load_passes"
    CATEGORY = "Airen_Studio"

    @classmethod
    def IS_CHANGED(cls, ud_name):
        input_dir = folder_paths.get_input_directory()
        render_path = os.path.join(input_dir, "render.png")
        depth_path = os.path.join(input_dir, "depth.png")
        
        # Calculate hash of file contents
        def get_file_hash(filepath):
            if not os.path.exists(filepath):
                return "0"
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        
        render_hash = get_file_hash(render_path)
        depth_hash = get_file_hash(depth_path)
        
        return f"{render_hash}_{depth_hash}"

    def load_passes(self, ud_name):
        input_dir = folder_paths.get_input_directory()
        
        # Load render pass
        render_path = os.path.join(input_dir, "render.png")
        render_img = Image.open(render_path)
        render_img = render_img.convert("RGB")
        render_tensor = torch.from_numpy(np.array(render_img).astype(np.float32) / 255.0)[None,]
        
        # Load depth pass
        depth_path = os.path.join(input_dir, "depth.png")
        depth_img = Image.open(depth_path)
        depth_img = depth_img.convert("RGB")
        depth_tensor = torch.from_numpy(np.array(depth_img).astype(np.float32) / 255.0)[None,]
        
        return (render_tensor, depth_tensor)


NODE_CLASS_MAPPINGS = {
    "Airen_Str": Airen_Str,
    "Airen_Int": Airen_Int,
    "Airen_Checkpoint_String": Airen_Checkpoint_String,
    "Airen_VAE_String": Airen_VAE_String,
    "Airen_Lora_String": Airen_Lora_String,
    "Airen_SaveImage": Airen_SaveImage,
    "Airen_InfoGetter": Airen_InfoGetter,
    "Airen_RenderPass": Airen_RenderPass,
}
