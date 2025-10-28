from PIL import Image
import numpy as np

def png_to_obj(png_path, obj_path, scale=0.01):
    # Load image - use numpy directly for speed
    img = Image.open(png_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    pixels = np.asarray(img)  # Faster than np.array
    
    height, width = pixels.shape[:2]
    mask = pixels[:, :, 3] > 0
    
    # Early return if no pixels
    if not mask.any():
        return

    # Build index mapping
    indices = np.zeros((height, width), dtype=np.int32)
    indices[mask] = np.arange(1, mask.sum() + 1)  # 1-indexed for OBJ

    # Get coordinates of valid pixels
    ys, xs = np.nonzero(mask)
    
    # Compute vertices and UVs
    vx = (xs - width * 0.5) * scale
    vy = -(ys - height * 0.5) * scale
    u = xs / (width - 1.0)
    v = 1.0 - ys / (height - 1.0)

    # Find valid quads efficiently
    mask_down = mask[1:, :]
    mask_right = mask[:, 1:]
    mask_diag = mask[1:, 1:]
    mask_tl = mask[:-1, :-1]
    
    valid_quads = mask_tl & mask_right[:-1, :] & mask_down[:, :-1] & mask_diag
    qy, qx = np.nonzero(valid_quads)
    
    # Get vertex indices for quads
    idx = indices
    v1 = idx[qy, qx]
    v2 = idx[qy, qx + 1]
    v3 = idx[qy + 1, qx + 1]
    v4 = idx[qy + 1, qx]

    # Write file with buffer
    with open(obj_path, 'wb') as f:  # Binary mode is faster
        # Header
        f.write(b"# Generated from PNG\n")
        
        # Vertices - use bytes formatting
        for i in range(len(vx)):
            f.write(f"v {vx[i]:.6g} {vy[i]:.6g} 0\n".encode())
        
        # UVs
        for i in range(len(u)):
            f.write(f"vt {u[i]:.6g} {v[i]:.6g}\n".encode())
        
        # Material and faces
        f.write(b"usemtl material_0\n")
        for i in range(len(v1)):
            i1, i2, i3, i4 = v1[i], v2[i], v3[i], v4[i]
            f.write(f"f {i1}/{i1} {i2}/{i2} {i3}/{i3}\n".encode())
            f.write(f"f {i1}/{i1} {i3}/{i3} {i4}/{i4}\n".encode())


# Example usage:
png_to_obj("mask.png", "mask_mesh.obj", scale=0.01)