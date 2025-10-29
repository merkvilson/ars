from rembg import remove
from PIL import Image
import torch
import numpy as np

# Tensor to PIL
def tensor2pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))

# Convert PIL to Tensor
def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

class Airen_REMBG:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "IMAGE")
    RETURN_NAMES = ("IMAGE", "MASK", "IMAGE (MASKED)")
    FUNCTION = "remove_background"
    CATEGORY = "Airen_Studio/Image Processing"

    def remove_background(self, image):
        # Convert tensor to PIL image
        pil_image = tensor2pil(image)
        
        # Remove background, result is RGBA
        output_pil = remove(pil_image)
        
        # Get the mask from the alpha channel
        mask_pil = output_pil.split()[3]
        
        # Create an RGB image with a black background
        rgb_image = Image.new("RGB", output_pil.size, (0, 0, 0))
        rgb_image.paste(output_pil, mask=mask_pil)
        
        # 1. IMAGE (black background)
        image_tensor = pil2tensor(rgb_image)
        
        # 2. MASK
        mask_np = np.array(mask_pil).astype(np.float32) / 255.0
        mask_tensor = torch.from_numpy(mask_np).unsqueeze(0)

        # 3. IMAGE (MASKED) (transparent background)
        image_masked_tensor = pil2tensor(output_pil)
        
        return (image_tensor, mask_tensor, image_masked_tensor)


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "Airen_REMBG": Airen_REMBG
}
