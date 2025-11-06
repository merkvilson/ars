# ARS Preview Saver for ComfyUI
# Unified preview saver with two independent systems:
# 1. Step Preview Saver - Saves each sampling step to output/steps/
# 2. Animated Frame Saver - Saves video frames to output/frames/TIMESTAMP_NodeID/

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
import comfy.utils
import logging
from comfy.cli_args import LatentPreviewMethod, args

import latent_preview
import server

# Force latent preview mode
args.preview_method = LatentPreviewMethod.Latent2RGB

# Configuration
STEPS_DIR = os.path.join(folder_paths.get_output_directory(), "steps")
FRAMES_DIR = os.path.join(folder_paths.get_output_directory(), "frames")

# Video model frame rates
FRAME_RATES = {
    "Mochi": 24//6, 
    "LTXV": 24//8, 
    "HunyuanVideo": 24//4,
    "Cosmos1CV8x8x8": 24//8, 
    "Wan21": 16//4, 
    "Wan22": 24//4
}

serv = server.PromptServer.instance


# ============================================================================
# SYSTEM 1: ANIMATED FRAME SAVER
# Saves video preview frames to output/frames/TIMESTAMP_NodeID/
# ============================================================================

class AnimatedFrameSaver(latent_preview.LatentPreviewer):
    """Handles saving animated preview frames during video generation"""
    
    def __init__(self, base_previewer, frame_rate=8):
        self.base_previewer = base_previewer
        self.frame_rate = frame_rate
        self.first_preview = True
        self.last_time = 0
        self.current_index = 0
        self.session_dir = None
        
        # Copy preview method from base previewer
        if hasattr(base_previewer, "taesd"):
            self.taesd = base_previewer.taesd
        elif hasattr(base_previewer, "latent_rgb_factors"):
            self.latent_rgb_factors = base_previewer.latent_rgb_factors
            self.latent_rgb_factors_bias = base_previewer.latent_rgb_factors_bias
        else:
            raise Exception("Unsupported preview type for Animated Frame Saver")

    def decode_latent_to_preview_image(self, preview_format, x0):
        """Main entry point - routes to appropriate handler"""
        # Single image (step preview) - delegate to base previewer
        if x0.ndim == 4 and x0.size(0) == 1:
            return self.base_previewer.decode_latent_to_preview_image(preview_format, x0)
        
        # Multi-image (animated sequence) - handle frame saving
        return self._handle_animated_sequence(x0)
    
    def _handle_animated_sequence(self, x0):
        """Process and save animated frame sequence"""
        # Reshape 5D tensor to 4D if needed
        if x0.ndim == 5:
            x0 = x0.movedim(2, 1)
            x0 = x0.reshape((-1,) + x0.shape[-3:])
        
        num_frames = x0.size(0)
        current_time = time.time()
        num_previews = int((current_time - self.last_time) * self.frame_rate)
        self.last_time = self.last_time + num_previews / self.frame_rate
        
        if num_previews > num_frames:
            num_previews = num_frames
        elif num_previews <= 0:
            return None
        
        # First preview - initialize session
        if self.first_preview:
            self.first_preview = False
            self._initialize_session(num_frames)
            self.last_time = current_time + 1 / self.frame_rate
        
        # Extract frames to process
        if self.current_index + num_previews > num_frames:
            frames = x0.roll(-self.current_index, 0)[:num_previews]
        else:
            frames = x0[self.current_index:self.current_index + num_previews]
        
        # Process and save frames
        Thread(target=self._save_frames, args=(frames, self.current_index, num_frames)).start()
        self.current_index = (self.current_index + num_previews) % num_frames
        
        return None
    
    def _initialize_session(self, num_frames):
        """Create session directory and notify browser"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        node_id = (serv.last_node_id or "unknown").replace(":", "_")
        self.session_dir = os.path.join(FRAMES_DIR, f"{timestamp}_{node_id}")
        os.makedirs(self.session_dir, exist_ok=True)
        
        print(f"[ARS Preview Saver] Animated frames saved to: {self.session_dir}")
        
        # Notify browser
        serv.send_sync("ARS_PreviewSaver_latentpreview", {
            "length": num_frames,
            "rate": self.frame_rate,
            "id": serv.last_node_id or "unknown"
        })
    
    def _save_frames(self, latent_frames, start_index, total_frames):
        """Decode, resize, and save frames to disk + stream to browser"""
        # Decode latents to RGB
        decoded = self._decode_latent(latent_frames)
        
        # Resize if too large
        if decoded.size(1) > 512 or decoded.size(2) > 512:
            decoded = self._resize_frames(decoded)
        
        # Convert to uint8
        frames_uint8 = (((decoded + 1.0) / 2.0).clamp(0, 1).mul(0xFF)).to(device="cpu", dtype=torch.uint8)
        
        # Save each frame
        frame_index = start_index
        for frame in frames_uint8:
            img = Image.fromarray(frame.numpy())
            
            # Save to disk
            if self.session_dir:
                save_path = os.path.join(self.session_dir, f"frame_{frame_index:05d}.jpg")
                img.save(save_path, format="JPEG", quality=95)
            
            # Stream to browser
            self._stream_to_browser(img, frame_index)
            
            frame_index = (frame_index + 1) % total_frames
    
    def _decode_latent(self, x0):
        """Decode latent tensor to RGB"""
        if hasattr(self, "taesd"):
            return self.taesd.decode(x0).movedim(1, 3)
        else:
            self.latent_rgb_factors = self.latent_rgb_factors.to(dtype=x0.dtype, device=x0.device)
            if self.latent_rgb_factors_bias is not None:
                self.latent_rgb_factors_bias = self.latent_rgb_factors_bias.to(dtype=x0.dtype, device=x0.device)
            return F.linear(x0.movedim(1, -1), self.latent_rgb_factors, bias=self.latent_rgb_factors_bias)
    
    def _resize_frames(self, frames):
        """Resize frames to fit within 512x512"""
        frames = frames.movedim(-1, 0)
        if frames.size(2) < frames.size(3):
            height = (512 * frames.size(2)) // frames.size(3)
            frames = F.interpolate(frames, (height, 512), mode="bilinear")
        else:
            width = (512 * frames.size(3)) // frames.size(2)
            frames = F.interpolate(frames, (512, width), mode="bilinear")
        return frames.movedim(0, -1)
    
    def _stream_to_browser(self, image, index):
        """Send frame to browser via WebSocket"""
        message = io.BytesIO()
        message.write((1).to_bytes(length=4, byteorder="big") * 2)
        message.write(index.to_bytes(length=4, byteorder="big"))
        node_id_bytes = (serv.last_node_id or "unknown").encode("ascii")
        message.write(struct.pack("16p", node_id_bytes))
        image.save(message, format="JPEG", quality=95, compress_level=1)
        serv.send_sync(server.BinaryEventTypes.PREVIEW_IMAGE, message.getvalue(), serv.client_id)


# ============================================================================
# SYSTEM 2: STEP PREVIEW SAVER
# Saves each sampling step to output/steps/
# ============================================================================

def create_step_saver_callback(model, steps, x0_output_dict=None):
    """Create callback that saves preview at each sampling step"""
    preview_format = "JPEG"
    previewer = latent_preview.get_previewer(model.load_device, model.model.latent_format)
    pbar = comfy.utils.ProgressBar(steps)
    
    def callback(step, x0, x, total_steps):
        # Update output dict if provided
        if x0_output_dict is not None:
            x0_output_dict["x0"] = x0
        
        # Generate preview
        preview_bytes = None
        if previewer:
            preview_bytes = previewer.decode_latent_to_preview_image(preview_format, x0)
        
        # Save step preview to disk
        if preview_bytes:
            _save_step_preview(preview_bytes, step, preview_format)
        
        # Update progress bar
        pbar.update_absolute(step + 1, total_steps, preview_bytes)
    
    return callback


def _save_step_preview(preview_bytes, step, preview_format):
    """Save a single step preview to output/steps/"""
    try:
        os.makedirs(STEPS_DIR, exist_ok=True)
        output_path = os.path.join(STEPS_DIR, f"{step:04d}.{preview_format.lower()}")
        
        # Handle different preview_bytes formats
        if isinstance(preview_bytes, tuple) and len(preview_bytes) >= 2:
            # Tuple: (format, data)
            data = preview_bytes[1]
            if isinstance(data, bytes):
                with open(output_path, "wb") as f:
                    f.write(data)
            else:
                data.save(output_path, preview_format)
        elif isinstance(preview_bytes, bytes):
            # Raw bytes
            with open(output_path, "wb") as f:
                f.write(preview_bytes)
        elif hasattr(preview_bytes, "save"):
            # PIL Image
            preview_bytes.save(output_path, preview_format)
        else:
            print(f"[ARS Preview Saver] Unknown preview format: {type(preview_bytes)}")
            
    except Exception as e:
        print(f"[ARS Preview Saver] Failed to save step {step}: {e}")


# ============================================================================
# HOOK SYSTEM - Integrate with ComfyUI
# ============================================================================

def hook(obj, attr):
    """Decorator to wrap an existing function"""
    def decorator(f):
        f = functools.update_wrapper(f, getattr(obj, attr))
        setattr(obj, attr, f)
        return f
    return decorator


@hook(latent_preview, "get_previewer")
def get_previewer_with_frame_saver(device, latent_format, *args, **kwargs):
    """Wrap previewer to add animated frame saving"""
    base_previewer = get_previewer_with_frame_saver.__wrapped__(device, latent_format, *args, **kwargs)
    
    # Get settings from workflow
    try:
        workflow_extra = next(serv.prompt_queue.currently_running.values().__iter__())[3]["extra_pnginfo"]["workflow"]["extra"]
        enable_animated = workflow_extra.get("ARS_PreviewSaver_latentpreview", True)
        frame_rate = workflow_extra.get("ARS_PreviewSaver_latentpreviewrate", 0)
        
        if frame_rate == 0:
            # Auto-detect frame rate based on model
            frame_rate = FRAME_RATES.get(latent_format.__class__.__name__, 8)
    except:
        # Defaults
        enable_animated = True
        frame_rate = 8
    
    # Wrap with frame saver if enabled
    if enable_animated and hasattr(base_previewer, "decode_latent_to_preview"):
        return AnimatedFrameSaver(base_previewer, frame_rate)
    
    return base_previewer


# Replace the step callback to add saving
latent_preview.prepare_callback = create_step_saver_callback


# ============================================================================
# EXTENSION REGISTRATION
# ============================================================================

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
