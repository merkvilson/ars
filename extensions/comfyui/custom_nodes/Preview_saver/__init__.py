"""
Custom Preview Saver Node for ComfyUI
Saves preview images at each step of the diffusion process to a specified folder.
"""

from pathlib import Path
import shutil
import folder_paths
import comfy.utils
import logging
from comfy.cli_args import LatentPreviewMethod, args
from nodes import latent_preview

args.preview_method = LatentPreviewMethod.Latent2RGB  # <-- Force previewing mode early


def prepare_callback2(model, steps, x0_output_dict=None):
    preview_format = "JPEG"
    if preview_format not in ["JPEG", "PNG"]:
        preview_format = "JPEG"

    previewer = latent_preview.get_previewer(model.load_device, model.model.latent_format)
    pbar = comfy.utils.ProgressBar(steps)

    output_dir = Path(folder_paths.get_output_directory()) / "steps"
    if output_dir.exists():
        for item in output_dir.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    def callback(step, x0, x, total_steps):
        if x0_output_dict is not None:
            x0_output_dict["x0"] = x0

        preview_bytes = None
        if previewer:
            preview_bytes = previewer.decode_latent_to_preview_image(preview_format, x0)

            # Save preview to custom folder
            output_dir.mkdir(parents=True, exist_ok=True)

            output_path = output_dir / f"{step:04d}.{preview_format.lower()}"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                preview_bytes[1].save(output_path, preview_format)
                #print(f"[Preview Saver] Saved preview at step {step} → {output_path}")
            except Exception as e:
                logging.warning(f"[Preview Saver] Failed to save preview: {e}")

        pbar.update_absolute(step + 1, total_steps, preview_bytes)

    return callback


# Replace the original function
latent_preview.prepare_callback = prepare_callback2
