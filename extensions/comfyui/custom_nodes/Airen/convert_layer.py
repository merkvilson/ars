from PIL import Image, ImageSequence
from pathlib import Path

def save_images_as_layers(base_image_path, steps_folder, output_path="image.tiff"):
    """
    Saves all images in `steps_folder` + base image (on top) into one TIFF file with layers (frames).
    Layer 0 = first step, last layer = final image (base).
    """
    base = Image.open(base_image_path).convert("RGBA")
    base_path = Path(base_image_path)
    steps = sorted(Path(steps_folder).glob("*.*"))
    layers = []

    for step in steps:
        # Skip the base image itself to avoid duplication
        if step.resolve() == base_path.resolve():
            continue
        # Skip non-image files (like .tiff outputs)
        if step.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.bmp']:
            continue
        try:
            img = Image.open(step).convert("RGBA")
            layers.append(img)
        except Exception as e:
            print(f"Skipping {step}: {e}")
    
    # Add base image as the last layer (top layer)
    layers.append(base)

    # Save as multi-layer TIFF
    if layers:
        layers[0].save(
            output_path,
            save_all=True,
            append_images=layers[1:],
            compression="tiff_deflate"
        )
        print(f"✅ Saved {len(layers)} layers to {output_path}")
    else:
        print("⚠️ No layers to save")

def extract_layers(tiff_path, output_folder="extracted_layers"):
    """
    Extracts each layer from a multi-layer TIFF and saves as separate PNGs.
    Layers are named 0, 1, 2, ...
    """
    im = Image.open(tiff_path)
    outdir = Path(output_folder)
    outdir.mkdir(exist_ok=True)

    for i, page in enumerate(ImageSequence.Iterator(im)):
        out_path = outdir / f"{i}.png"
        page.save(out_path)
        print(f"🖼️ Extracted layer {i} -> {out_path}")

"""
# Example usage:
save_images_as_layers("image.png", "steps", "image.tiff")

# Optional: extract later
extract_layers("image_with_layers.tiff")
"""
