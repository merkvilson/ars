import os
import shutil


def copy_items(source_folder, destination_folder):
    """
    Copies files, folders, and other items from source_folder to destination_folder.

    :param source_folder: The folder containing the items to be copied.
    :param destination_folder: The folder where the items will be copied to.
    """
    # Check if source folder exists
    if not os.path.exists(source_folder):
        print(f"Source folder '{source_folder}' does not exist.")
        return

    # Create the destination folder if it does not exist
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # Iterate through items in the source folder
    for item_name in os.listdir(source_folder):
        source_item = os.path.join(source_folder, item_name)
        destination_item = os.path.join(destination_folder, item_name)

        # Copy files and directories
        if os.path.isdir(source_item):
            shutil.copytree(source_item, destination_item, dirs_exist_ok=True)
            print(f"Copied directory: {source_item} -> {destination_item}")
        elif os.path.isfile(source_item):
            shutil.copy2(source_item, destination_item)  # Copy file with metadata
            print(f"Copied file: {source_item} -> {destination_item}")
        else:
            print(f"Skipped unsupported item: {source_item}")


#plugin_path       = os.path.dirname(os.path.split(__file__)[0])
#airen_root_path   = os.path.dirname(os.path.dirname(os.path.dirname(plugin_path)))

#airen_nodes_path  = os.path.join((os.path.dirname(plugin_path)),"nodes")
#sd_cstnodes_path  = os.path.join(airen_root_path ,"ComfyUI","ComfyUI", "custom_nodes")



#copy_items(airen_nodes_path, sd_cstnodes_path)
