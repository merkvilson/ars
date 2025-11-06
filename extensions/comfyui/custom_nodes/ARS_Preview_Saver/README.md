# ARS Preview Saver for ComfyUI

Unified preview saver that automatically saves both step-by-step previews and animated latent frames during sampling.

## What It Does

This custom node **automatically**:
- ✅ **Saves step previews** to `output/steps/` folder (0000.jpg, 0001.jpg, etc.)
- ✅ **Saves animated frames** to `output/frames/YYYYMMDD_HHMMSS_NodeID/` folders
- ✅ **Displays animated previews** in real-time on canvas widgets
- ✅ Works with all latent-generating nodes automatically

## Installation

Already installed. **Restart ComfyUI** to activate.

## Features

- 🎯 **Dual saving** - Both step previews AND animated frames
- 📁 **Organized storage** - Steps in one folder, frames in timestamped sessions
- 🎨 **Real-time display** - Animated canvas preview during generation
- ⚙️ **Configurable** - Enable/disable each feature independently
- 🎬 **Video model support** - Auto frame rates for Mochi, LTXV, HunyuanVideo, etc.
- 🚀 **No setup required** - Works immediately after restart

## Storage Structure

```
ComfyUI/output/
├── steps/                    # Step-by-step previews (from Image_Preview_saver)
│   ├── 0000.jpg
│   ├── 0001.jpg
│   ├── 0002.jpg
│   └── ...
│
└── frames/                   # Animated frame sequences (from Video_Preview_Saver)
    ├── 20251106_143052_NodeID_123/
    │   ├── frame_00000.jpg
    │   ├── frame_00001.jpg
    │   ├── frame_00002.jpg
    │   └── ...
    └── 20251106_145230_NodeID_456/
        ├── frame_00000.jpg
        └── ...
```

## Configuration

Edit `latent_preview_node.py` to customize (lines 23-26):

```python
SAVE_STEP_PREVIEWS = True    # Save to "steps" folder
SAVE_ANIMATED_FRAMES = True  # Save to "frames" folder
STEPS_DIR = os.path.join(folder_paths.get_output_directory(), "steps")
FRAMES_DIR = os.path.join(folder_paths.get_output_directory(), "frames")
```

## Settings (Optional)

Customize behavior in ComfyUI Settings:

1. Open **Settings** (gear icon)
2. Navigate to: **🎨 ARS Preview Saver → Sampling → Latent Previews**
3. Options:
   - **Display animated previews**: Toggle canvas display on/off (default: ON)
   - **Playback rate override**: 0-60 FPS (0 = auto, default: 8)

## Usage

### Quick Start
1. **Restart ComfyUI**
2. **Run any workflow** - previews are saved automatically!
3. **Check output folders**:
   - `output/steps/` for step-by-step previews
   - `output/frames/` for animated sequences

### What Gets Saved

**Step Previews** (`steps/`):
- One image per sampling step
- Sequential numbering: 0000.jpg, 0001.jpg, etc.
- Overwrites on each new generation
- Perfect for seeing progression

**Animated Frames** (`frames/`):
- Complete frame sequences in timestamped folders
- Each generation gets its own folder
- Never overwrites previous sessions
- Perfect for making videos

## Migrating from Old Extensions

If you were using:
- **Image_Preview_saver**: Disable it (rename folder to `Image_Preview_saver.disabled`)
- **Video_Preview_Saver**: Already renamed to ARS_Preview_Saver

This extension replaces both with a unified, more polished solution.

## Technical Details

- Hooks into ComfyUI's latent preview system
- Replaces `latent_preview.prepare_callback` for step saving
- Wraps `latent_preview.get_previewer` for animated frames
- Uses JPEG format with 95% quality
- Previews limited to 512px max dimension for performance
- Real-time WebSocket streaming to browser

## File Structure

```
ARS_Preview_Saver/
├── __init__.py                 # Plugin entry point
├── latent_preview_node.py      # Unified implementation
├── README.md                   # This file
└── web/
    └── js/
        └── latent_preview.js   # Frontend canvas display
```

## Credits

Combines and improves upon:
- Image_Preview_saver (step-by-step saving)
- Video_Preview_Saver (animated frame saving, based on VideoHelperSuite)

## License

Same as original projects.
