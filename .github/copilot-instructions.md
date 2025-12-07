# ARS Project Instructions

## Project Overview
ARS is a Python-based 3D application built with **PyQt6** (UI) and **Vispy** (3D rendering). It features a unique "Floating Bubble" interface and integrates with **ComfyUI** for rendering workflows.

## Coding Philosophy
- **Avoid Overengineering**: Keep solutions simple, functional, and direct.
- **Minimalism**: Less code is better. Avoid unnecessary abstractions or complex patterns unless absolutely required.
- **Pragmatism**: Focus on working features over theoretical purity.

## Architecture
- **Entry Point**: `main.py` initializes `Application` and `MainWindow`.
- **UI Framework**: PyQt6. Main window logic in `ui/main_window.py`.
- **3D Engine**: Located in `ars_3d_engine/`.
  - `ViewportWidget` (`ars_3d_engine/viewport.py`): Core 3D view using `vispy.scene`.
  - `CObjectManager`: Manages 3D objects.
  - `GizmoController`: Handles object manipulation gizmos.
- **Command System**: Located in `ars_cmds/`. Implements a command pattern where features are modular "Bubbles".
- **Extensions**: `extensions/` folder (e.g., ComfyUI integration).

## Development Conventions

### Command / Bubble Pattern
New features are often added as "Bubbles" in `ars_cmds/bubble_cmds/`.
To add a new command:
1. Create a new `.py` file in `ars_cmds/bubble_cmds/`.
2. Define a configuration dictionary named `BBL_<NAME>_CONFIG`:
   ```python
   BBL_MYCMD_CONFIG = {
       "symbol": "icon_name", # from theme.fonts.font_icons
       "hotkey": "Ctrl+K"     # Optional default hotkey
   }
   ```
3. Define the entry function `BBL_<NAME>`:
   ```python
   def BBL_MYCMD(*args):
       run_ext(__file__) # Common pattern to delegate to execute_cmd
   ```
4. Define `execute_cmd(ars_window)` for the actual logic (often opens a context menu):
   ```python
   def execute_cmd(ars_window):
       # Logic here
       pass
   ```

### Hotkeys
Hotkeys are dynamically registered in `ars_cmds/core_cmds/define_hotkeys.py` by scanning `ars_cmds/bubble_cmds/` for `BBL_*_CONFIG` dictionaries.

### UI Components
- **Floating Bubbles**: Managed by `FloatingBubblesManager` in `ui/widgets/bubble_layout.py`.
- **Context Menus**: Use `ui.widgets.context_menu.ContextMenuConfig` to define radial/list menus.

## Workflows
- **Run Application**: `python main.py`
- **Environment**: Requires `PyQt6`, `vispy`, `pygame`, `numpy`, `scipy`.
- **Assets**: Resources are in `res/` (icons, sounds, meshes).

## Key Files
- `main.py`: Application bootstrap.
- `ui/main_window.py`: Main UI layout and initialization.
- `ars_3d_engine/viewport.py`: 3D scene setup.
- `ars_cmds/bubble_cmds/`: Directory for adding new application commands.
