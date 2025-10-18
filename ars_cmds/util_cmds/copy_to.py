import os
import shutil

def copy_file_to_dir(file_path, destination_dir, copy_as=None, incremental=False):
    """
    Copies a file from file_path to destination_dir.

    Args:
        file_path (str): Path to the source file.
        destination_dir (str): Directory where the file will be copied.
        copy_as (str or None): If provided, use this name (extension preserved).
        incremental (bool): If True, appends the number of files in the directory to the filename.
    """
    if not os.path.isfile(file_path):
        print(f"Error: '{file_path}' is not a valid file.")
        return None

    os.makedirs(destination_dir, exist_ok=True)

    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)

    # Determine filename
    if copy_as is not None:
        name = copy_as  # use provided name

    if incremental:
        file_count = len([f for f in os.listdir(destination_dir) if os.path.isfile(os.path.join(destination_dir, f))])
        name = f"{name}_{file_count}"

    new_filename = name + ext
    destination_path = os.path.join(destination_dir, new_filename)

    try:
        shutil.copy2(file_path, destination_path)
        print(f"File copied to: {destination_path}")
        return destination_path
    except Exception as e:
        print(f"Error copying file: {e}")
        return None
