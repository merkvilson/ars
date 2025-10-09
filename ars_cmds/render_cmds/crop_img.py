from PIL import Image

def crop_img(img_path, save_as, x, y):

    # Load the image
    img = Image.open(img_path)

    # Get current size
    width, height = img.size

    # Determine the size of the square crop (based on shorter side)
    new_side = min(width, height)

    # Calculate coordinates for center crop
    left = (width - new_side) // 2
    top = (height - new_side) // 2
    right = left + new_side
    bottom = top + new_side

    # Crop the image
    cropped_img = img.crop((left, top, right, bottom))

    # Resize to 512x512 using new resampling method
    final_img = cropped_img.resize((x, y), Image.Resampling.LANCZOS)


    # Save the final image
    final_img.save(save_as, optimize=True)
