# Single-file Latent Preview for ComfyUI
# Automatically enables animated latent previews during sampling
# WITH PREVIEW SAVING

from PIL import Image
import time
import io
import struct
from threading import Thread
import functools
import torch.nn.functional as F
import torch
import os
import folder_paths

import latent_preview
import server

# Configuration
SAVE_PREVIEWS = True  # Set to False to disable saving
PREVIEW_DIR = os.path.join(folder_paths.get_output_directory(), "latent_previews")

# Video model frame rates
rates_table = {
    'Mochi': 24//6, 
    'LTXV': 24//8, 
    'HunyuanVideo': 24//4,
    'Cosmos1CV8x8x8': 24//8, 
    'Wan21': 16//4, 
    'Wan22': 24//4
}

serv = server.PromptServer.instance

class WrappedPreviewer(latent_preview.LatentPreviewer):
    def __init__(self, previewer, rate=8):
        self.first_preview = True
        self.last_time = 0
        self.c_index = 0
        self.rate = rate
        self.session_dir = None  # Will be set on first preview
        
        if hasattr(previewer, 'taesd'):
            self.taesd = previewer.taesd
        elif hasattr(previewer, 'latent_rgb_factors'):
            self.latent_rgb_factors = previewer.latent_rgb_factors
            self.latent_rgb_factors_bias = previewer.latent_rgb_factors_bias
        else:
            raise Exception('Unsupported preview type for Video Preview Saver animated previews')

    def decode_latent_to_preview_image(self, preview_format, x0):
        if x0.ndim == 5:
            # Keep batch major
            x0 = x0.movedim(2,1)
            x0 = x0.reshape((-1,)+x0.shape[-3:])
        num_images = x0.size(0)
        new_time = time.time()
        num_previews = int((new_time - self.last_time) * self.rate)
        self.last_time = self.last_time + num_previews/self.rate
        if num_previews > num_images:
            num_previews = num_images
        elif num_previews <= 0:
            return None
        if self.first_preview:
            self.first_preview = False
            
            # Create session directory for saving previews
            if SAVE_PREVIEWS:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                node_name = serv.last_node_id.replace(':', '_')
                self.session_dir = os.path.join(PREVIEW_DIR, f"{timestamp}_{node_name}")
                os.makedirs(self.session_dir, exist_ok=True)
                print(f"[Latent Preview] Saving previews to: {self.session_dir}")
            
            serv.send_sync('VideoPreviewSaver_latentpreview', {
                'length': num_images, 
                'rate': self.rate, 
                'id': serv.last_node_id
            })
            self.last_time = new_time + 1/self.rate
        if self.c_index + num_previews > num_images:
            x0 = x0.roll(-self.c_index, 0)[:num_previews]
        else:
            x0 = x0[self.c_index:self.c_index + num_previews]
        Thread(target=self.process_previews, args=(x0, self.c_index, num_images)).run()
        self.c_index = (self.c_index + num_previews) % num_images
        return None
        
    def process_previews(self, image_tensor, ind, leng):
        image_tensor = self.decode_latent_to_preview(image_tensor)
        if image_tensor.size(1) > 512 or image_tensor.size(2) > 512:
            image_tensor = image_tensor.movedim(-1,0)
            if image_tensor.size(2) < image_tensor.size(3):
                height = (512 * image_tensor.size(2)) // image_tensor.size(3)
                image_tensor = F.interpolate(image_tensor, (height,512), mode='bilinear')
            else:
                width = (512 * image_tensor.size(3)) // image_tensor.size(2)
                image_tensor = F.interpolate(image_tensor, (512, width), mode='bilinear')
            image_tensor = image_tensor.movedim(0,-1)
        previews_ubyte = (((image_tensor + 1.0) / 2.0).clamp(0, 1)
                         .mul(0xFF)
                         ).to(device="cpu", dtype=torch.uint8)
        for preview in previews_ubyte:
            i = Image.fromarray(preview.numpy())
            
            # Save preview to disk if enabled
            if SAVE_PREVIEWS and self.session_dir:
                save_path = os.path.join(self.session_dir, f"preview_{ind:05d}.jpg")
                i.save(save_path, format="JPEG", quality=95)
            
            # Send to browser
            message = io.BytesIO()
            message.write((1).to_bytes(length=4, byteorder='big')*2)
            message.write(ind.to_bytes(length=4, byteorder='big'))
            message.write(struct.pack('16p', serv.last_node_id.encode('ascii')))
            i.save(message, format="JPEG", quality=95, compress_level=1)
            serv.send_sync(server.BinaryEventTypes.PREVIEW_IMAGE,
                           message.getvalue(), serv.client_id)
            ind = (ind + 1) % leng
            
    def decode_latent_to_preview(self, x0):
        if hasattr(self, 'taesd'):
            x_sample = self.taesd.decode(x0).movedim(1, 3)
            return x_sample
        else:
            self.latent_rgb_factors = self.latent_rgb_factors.to(dtype=x0.dtype, device=x0.device)
            if self.latent_rgb_factors_bias is not None:
                self.latent_rgb_factors_bias = self.latent_rgb_factors_bias.to(dtype=x0.dtype, device=x0.device)
            latent_image = F.linear(x0.movedim(1, -1), self.latent_rgb_factors,
                                    bias=self.latent_rgb_factors_bias)
            return latent_image

# Hook into ComfyUI's latent preview system
def hook(obj, attr):
    """Decorator to hook/wrap an existing function"""
    def dec(f):
        f = functools.update_wrapper(f, getattr(obj, attr))
        setattr(obj, attr, f)
        return f
    return dec

@hook(latent_preview, 'get_previewer')
def get_latent_video_previewer(device, latent_format, *args, **kwargs):
    node_id = serv.last_node_id
    previewer = get_latent_video_previewer.__wrapped__(device, latent_format, *args, **kwargs)
    
    # Always enabled - try to get settings from workflow
    try:
        extra_info = next(serv.prompt_queue.currently_running.values().__iter__()) \
                [3]['extra_pnginfo']['workflow']['extra']
        prev_setting = extra_info.get('VideoPreviewSaver_latentpreview', True)
        if extra_info.get('VideoPreviewSaver_latentpreviewrate', 0) != 0:
            rate_setting = extra_info['VideoPreviewSaver_latentpreviewrate']
        else:
            rate_setting = rates_table.get(latent_format.__class__.__name__, 8)
    except:
        # Default to enabled with 8 FPS
        prev_setting = True
        rate_setting = 8
    
    if not prev_setting or not hasattr(previewer, "decode_latent_to_preview"):
        return previewer
    return WrappedPreviewer(previewer, rate_setting)

# No nodes - automatically enabled
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
