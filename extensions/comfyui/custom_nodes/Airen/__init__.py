# Custom nodes for user data input in ComfyUI.
# No input sockets, only outputs. Widgets for user entry.
# Note for AI: Every node must have a ud_name input.

import os
import folder_paths
from PIL import Image
import numpy as np
import torch
import hashlib
from .convert_layer import save_images_as_layers


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
    CATEGORY = "Airen_Studio/User Data"
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
    CATEGORY = "Airen_Studio/User Data"
    OUTPUT_NODE = True

    def execute(self, ud_name, output):
        return (output,)

class Airen_Float:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ud_name": ("STRING", {"default": "", "multiline": False}),
                "output": ("FLOAT", {"default": 0, "min": -999999, "max": 999999, "step": 0.1}),
            }
        }

    RETURN_TYPES = ("FLOAT",)
    FUNCTION = "execute"
    CATEGORY = "Airen_Studio/User Data"
    OUTPUT_NODE = True

    def execute(self, ud_name, output):
        return (output,)
    
class Airen_Checkpoint:
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
    CATEGORY = "Airen_Studio/User Data"

    def execute(self, ud_name, output):
        return (output,)

class Airen_VAE:
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
    CATEGORY = "Airen_Studio/User Data"

    def execute(self, ud_name, vae_name):
        return (vae_name,)

class Airen_Lora:
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
    CATEGORY = "Airen_Studio/User Data"

    def execute(self, ud_name, lora_name):
        return (lora_name,)

class Airen_SaveImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ud_name": ("STRING", {"default": "", "multiline": False}),
                "images": ("IMAGE", ),
                "category": (["keyframes", "3d", "bg", "dome", "mesh", "sprite", "steps", "texture"], ),
                "save_layers": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "Airen_Studio/Image Processing"

    def save_images(self, ud_name, images, category, save_layers):
        if category in ["keyframes", "3d", "bg", "dome", "sprite", "steps", "texture"]:
            output_dir = folder_paths.get_output_directory()
            filename_prefix = f"{category}/0"
            full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
                filename_prefix, output_dir, images[0].shape[1], images[0].shape[0])
            results = []
            saved_files = []
            for image in images:
                i = 255. * image.cpu().numpy()
                img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                file = f"{filename}{len(os.listdir(full_output_folder)):03d}.png"
                full_path = os.path.join(full_output_folder, file)
                img.save(full_path, compress_level=4)
                saved_files.append(full_path)
                results.append({"filename": file, "subfolder": subfolder, "type": "output"})
            
            # After saving the last image in "steps" category, create layered TIFF
            if category == "steps" and saved_files and save_layers:
                try:
                    last_image_path = saved_files[-1]
                    steps_folder = full_output_folder
                    
                    # Create TIFF filename based on the last saved image
                    tiff_filename = f"{filename}{len(os.listdir(full_output_folder)):03d}.tiff"
                    tiff_path = os.path.join(full_output_folder, tiff_filename)
                    
                    # Call convert_layer to save all steps as layers
                    save_images_as_layers(last_image_path, steps_folder, tiff_path)
                    
                    # Add the TIFF to results
                    results.append({"filename": tiff_filename, "subfolder": subfolder, "type": "output"})
                except Exception as e:
                    print(f"Error creating layered TIFF: {e}")
            
            return {"ui": {"images": results}}
        elif category in ["mesh"]:
            output_dir = folder_paths.get_input_directory()
            filename_prefix = f"{category}"
            full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
                filename_prefix, output_dir, images[0].shape[1], images[0].shape[0])
            results = []
            for image in images:
                i = 255. * image.cpu().numpy()
                img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                file = f"{filename}.png"
                img.save(os.path.join(full_output_folder, file), compress_level=4)
                results.append({"filename": file, "subfolder": subfolder, "type": "output"})
            return {"ui": {"images": results}}


class Airen_Progress_Reader:
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
    CATEGORY = "Airen_Studio/Utility"
    OUTPUT_NODE = False



class Airen_RenderPass:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ud_name": ("STRING", {"default": "", "multiline": False}),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE")  # Render, Depth
    RETURN_NAMES = ("render", "depth")
    FUNCTION = "load_passes"
    CATEGORY = "Airen_Studio/Image Processing"

    @classmethod
    def IS_CHANGED(cls, ud_name):
        input_dir = folder_paths.get_input_directory()
        render_path = os.path.join(input_dir, "render.png")
        depth_path = os.path.join(input_dir, "depth.png")

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

    def load_image_as_tensor(self, path):
        if not os.path.exists(path):
            # Return an empty tensor if file not found
            return torch.zeros((1, 1, 1, 3), dtype=torch.float32)
        img = Image.open(path).convert("RGB")
        return torch.from_numpy(np.array(img).astype(np.float32) / 255.0)[None,]

    def load_passes(self, ud_name):
        input_dir = folder_paths.get_input_directory()

        render_tensor = self.load_image_as_tensor(os.path.join(input_dir, "render.png"))
        depth_tensor = self.load_image_as_tensor(os.path.join(input_dir, "depth.png"))
        return (render_tensor, depth_tensor)


class Airen_LoadKeyframe:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ud_name": ("STRING", {"default": "", "multiline": False}),
                "frame_number": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "load_keyframe"
    CATEGORY = "Airen_Studio/Image Processing"

    @classmethod
    def IS_CHANGED(cls, ud_name, frame_number):
        """ This forces ComfyUI to treat the node as non-deterministic 
        and re-execute it every time the workflow runs, ensuring that 
        the latest version of the TIFF file is always loaded, even if 
        the filename hasn't changed."""
        return float("NaN")

    def load_keyframe(self, ud_name, frame_number):
        input_dir = folder_paths.get_input_directory()
        image_path = os.path.join(input_dir, f"{frame_number}.tiff")
        
        if not os.path.exists(image_path):
            # Return empty black image if not found
            return (torch.zeros((1, 64, 64, 3), dtype=torch.float32),)
            
        img = Image.open(image_path)
        
        # Get the latest layer (last frame of TIFF)
        try:
            if hasattr(img, 'n_frames') and img.n_frames > 1:
                img.seek(img.n_frames - 1)
        except Exception as e:
            print(f"Error seeking TIFF frame: {e}")
            pass
            
        img = img.convert("RGB")
        image_tensor = torch.from_numpy(np.array(img).astype(np.float32) / 255.0)[None,]
        
        return (image_tensor,)


NODE_CLASS_MAPPINGS = {
    "Airen_Str": Airen_Str,
    "Airen_Int": Airen_Int,
    "Airen_Float": Airen_Float,
    "Airen_Checkpoint": Airen_Checkpoint,
    "Airen_VAE": Airen_VAE,
    "Airen_Lora": Airen_Lora,
    "Airen_SaveImage": Airen_SaveImage,
    "Airen_Progress_Reader": Airen_Progress_Reader,
    "Airen_RenderPass": Airen_RenderPass,
    "Airen_LoadKeyframe": Airen_LoadKeyframe,
}
