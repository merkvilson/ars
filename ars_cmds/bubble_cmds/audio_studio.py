from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from prefs import pref_controller
import os


BBL_AUDIO_STUDIO_CONFIG = {"symbol": ic.ICON_VOLUME_2, "hotkey": "shift+A", "visible": False}


def BBL_AUDIO_STUDIO(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    from ui.sound_player.audio_widget import AudioStudio

    # Create Audio Studio Widget
    audio_studio = AudioStudio()

    # Set initial sizes (30% left, 70% right)
    width = ars_window.width()
    audio_studio.splitter.setSizes([int(width * 0.3), int(width * 0.7)])

    # Integrate with SplitterOverlay
    if hasattr(ars_window, 'splitter_overlay'):
        overlay = ars_window.splitter_overlay
        
        # Set height
        height = getattr(ars_window.prefs, 'audio_studio_height', 300)
        overlay.bottom_height = height
        
        overlay.set_widget("bottom", audio_studio)
        
        # Force update to apply height and layout
        overlay._update_mask()
        overlay._update_geometries()
        overlay.update()
