"""
p_text.py

- Walks a project folder (default: "ARS")
- Builds a directory tree (only showing files that will be saved, honoring extensions and exclusions)
- Reads file contents (honoring MAX_FILE_LENGTH and EXCLUDE_FILES)
- Deletes any old 'project_files.txt' within the project tree
- Writes a new 'project_files.txt' containing the directory tree at the top, then the file contents

Usage:
    python p_text.py
    python p_text.py --dir /path/to/project --output my_project_snapshot.txt --extensions .py .txt
"""

import os
import argparse
from typing import List, Tuple, Dict, Optional


DEFAULT_FOLDER = os.path.join(".",)  # default project folder
DEFAULT_EXTENSIONS = [".py", ".txt", ".qss", ".json", ".md", ".gsls", ".arsp", ".arsl", ".bat"]   # set to None to include all files
EXCLUDE_FILES = []  # filenames to exclude from saved output
#EXCLUDE_FILES = ["p_text.py", "project_files.txt", "InfiniteGrid.py", "bg.py", ]  # filenames to exclude from saved output
MAX_FILE_LENGTH = 50_000_000  # bytes; set None to include everything
DEFAULT_SKIP_DIRS = ["__pycache__",]
# DEFAULT_SKIP_DIRS = ["__pycache__", "cinema_4d"]
DEFAULT_OUTPUT = os.path.join("util_functions", "project_files.txt")  # output file
SAVE_OUTPUT = True  # set to False to skip saving (for testing)
SAVE_OUTPUT = False
# ---------------------------


def build_directory_tree(
    path: str,
    prefix: str = "",
    skip_dirs: Optional[List[str]] = None,
    extensions: Optional[List[str]] = None,
    exclude_files: Optional[List[str]] = None,
) -> str:
    """
    Build a directory tree string for files that will be saved.

    Only directories and files that meet the extensions/exclude_files filter are included.
    Returns a formatted string using ├── and └── lines (like tree).
    """

    if skip_dirs is None:
        skip_dirs = []
    if exclude_files is None:
        exclude_files = []

    def _helper(current_path: str, current_prefix: str) -> Tuple[str, bool]:
        """
        Returns (tree_string_for_this_dir, contains_included_items_flag)
        The contains_included_items_flag indicates whether this directory or its subtree has
        any files that pass the filters (so we can decide whether to show the directory).
        """
        try:
            entries = sorted(
                os.listdir(current_path),
                key=lambda x: (not os.path.isdir(os.path.join(current_path, x)), x.lower()),
            )
        except PermissionError:
            return f"{current_prefix}└── [ACCESS DENIED]\n", False

        # Remove skipped dirs from the listing
        entries = [e for e in entries if e not in skip_dirs]

        tree_parts = []
        has_any = False
        total = len(entries)
        for idx, name in enumerate(entries):
            full = os.path.join(current_path, name)
            last = (idx == total - 1)
            connector = "└── " if last else "├── "
            next_prefix = "    " if last else "│   "

            if os.path.isdir(full):
                subtree_str, subtree_has = _helper(full, current_prefix + next_prefix)
                if subtree_has:
                    # include directory only if subtree contains included files
                    tree_parts.append(f"{current_prefix}{connector}{name}/\n")
                    tree_parts.append(subtree_str)
                    has_any = True
                else:
                    # directory had no included files -> skip showing it
                    continue
            else:
                # file - check filters
                if exclude_files and name in exclude_files:
                    continue
                if extensions:
                    # only include if file matches any extension
                    if not any(name.endswith(ext) for ext in extensions):
                        continue
                # file passed filters - include it
                tree_parts.append(f"{current_prefix}{connector}{name}\n")
                has_any = True

        return "".join(tree_parts), has_any

    if not os.path.exists(path):
        return f"[PATH NOT FOUND: {path}]\n"

    tree_str, had_any = _helper(path, prefix)
    if not had_any:
        # No files matched filters in entire tree
        return "[NO FILES MATCHING FILTERS FOUND]\n"
    return tree_str


def cleanup_old_project_files(directory: str, filename: str = DEFAULT_OUTPUT) -> None:
    """
    Recursively finds and deletes all files named `filename` inside `directory` and its subdirectories.
    """
    removed_files = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f == filename:
                file_path = os.path.join(root, f)
                try:
                    os.remove(file_path)
                    removed_files.append(file_path)
                except Exception as e:
                    print(f"Could not delete {file_path}: {e}")
    if removed_files:
        print("Deleted old project_files.txt files:")
        for p in removed_files:
            print(" -", p)
    else:
        print("No old project_files.txt found to delete.")


def read_files(
    directory: str,
    extensions: Optional[List[str]] = None,
    exclude_files: Optional[List[str]] = None,
    skip_dirs: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Walks the directory and reads files into a dict {relative_path: content_or_message}
    Honors 'extensions', 'exclude_files', 'skip_dirs', and 'MAX_FILE_LENGTH'.
    """
    if exclude_files is None:
        exclude_files = []
    if skip_dirs is None:
        skip_dirs = []

    project_files: Dict[str, str] = {}

    for root, dirs, files in os.walk(directory):
        # mutate dirs in-place so os.walk won’t even descend into skipped ones
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for fname in files:
            # skip excluded filenames
            if fname in exclude_files:
                continue

            # filter by extension if requested
            if extensions and not any(fname.endswith(ext) for ext in extensions):
                continue

            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, directory)

            try:
                size = os.path.getsize(full_path)
                if MAX_FILE_LENGTH and (size > MAX_FILE_LENGTH):
                    project_files[rel_path] = "[CONTENT TOO LONG OR EXCLUDED]"
                    continue

                with open(full_path, "r", encoding="utf-8") as fh:
                    content = fh.read()

                if MAX_FILE_LENGTH and len(content) > MAX_FILE_LENGTH:
                    project_files[rel_path] = "[CONTENT TOO LONG OR EXCLUDED]"
                else:
                    project_files[rel_path] = content

            except UnicodeDecodeError:
                project_files[rel_path] = "[SKIPPED: BINARY OR NON-UTF8 FILE]"
            except Exception as e:
                project_files[rel_path] = f"[SKIPPED: {e}]"

    return project_files


def save_project_files(project_files: Dict[str, str], directory_tree: str, output_file: str = DEFAULT_OUTPUT) -> None:
    """
    Save the directory tree and project files to output_file (overwrites if exists).
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("=== DIRECTORY TREE ===\n")
            f.write(directory_tree)
            f.write("\n\n=== PROJECT FILES ===\n")
            for path, content in project_files.items():
                f.write(f"\n\n--- FILE: {path} ---\n")
                f.write(content)
                f.write("\n--- END OF FILE ---\n")
        print(f"Project files (with directory tree) saved to: {output_file}")
    except Exception as e:
        print(f"Could not write to {output_file}: {e}")


def print_summary(project_files: Dict[str, str]) -> None:
    """
    Prints a short summary to console.
    """
    total = len(project_files)

    total_lines = 0
    for c in project_files.values():
        if not (c.startswith("[SKIPPED") or c.startswith("[CONTENT TOO LONG")):
            total_lines += len(c.splitlines())

    print("\nSummary:")
    print(f"  Files included: {total}")
    print(f"  Total lines of code: {total_lines}")

    skipped = [p for p, c in project_files.items() if c.startswith("[SKIPPED") or c.startswith("[CONTENT TOO LONG")]
    if skipped:
        print(f"  Skipped / special entries: {len(skipped)}")
        for s in skipped:
            print("   -", s)


def main():
    parser = argparse.ArgumentParser(description="Save project files and directory tree to a single text file.")
    parser.add_argument("--dir", "-d", default=DEFAULT_FOLDER, help="Project folder to scan (default: %(default)s)")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help="Output text file (default: %(default)s)")
    parser.add_argument("--extensions", "-e", nargs="*", help="File extensions to include (e.g. .py .txt). Default is configured in script.")
    parser.add_argument("--no-cleanup", action="store_true", help="Do NOT delete old project_files.txt files inside the project tree.")
    parser.add_argument("--skip", nargs="*", help="Directory names to skip (default: __pycache__)")
    args = parser.parse_args()

    folder = args.dir
    output = args.output
    extensions = args.extensions if args.extensions is not None else DEFAULT_EXTENSIONS
    skip_dirs = args.skip if args.skip is not None else DEFAULT_SKIP_DIRS

    # Validate folder
    if not os.path.exists(folder):
        print(f"ERROR: folder does not exist: {folder}")
        return

    # Step 1: cleanup old project_files.txt if requested
    if not args.no_cleanup:
        cleanup_old_project_files(folder, filename=os.path.basename(output))

    # Step 2: build directory tree string (shows files that will be saved)
    directory_tree = build_directory_tree(
        folder,
        prefix=" ",
        skip_dirs=skip_dirs,
        extensions=extensions,
        exclude_files=EXCLUDE_FILES,
    )

    # Step 3: read files
    files_content = read_files(
        folder,
        extensions=extensions,
        exclude_files=EXCLUDE_FILES,
        skip_dirs=skip_dirs
    )
    # Step 4: save everything into the output file (tree + files)
    if SAVE_OUTPUT:
        save_project_files(files_content, directory_tree, output_file=output)
    else:
        print("SAVE_OUTPUT is False - skipping file save.")

    # Optional console printing
    print_summary(files_content)

if __name__ == "__main__":
    main()
