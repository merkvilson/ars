import os

def delete_all_files_in_folder(folder_path):
    if not os.path.exists(folder_path): return
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path): os.remove(file_path)