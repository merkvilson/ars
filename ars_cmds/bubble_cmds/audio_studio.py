from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter
from prefs import pref_controller
import os


BBL_AUDIO_STUDIO_CONFIG = {"symbol": ic.ICON_VOLUME_2, "hotkey": "shift+A", "visible": False}


def BBL_AUDIO_STUDIO(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    from ui.sound_player.sound_player import SoundboardWidget
    from ui.sound_player.sound_modifier import AudioModifierWidget

    # Create Splitter (horizontal for player | modifier)
    splitter = QSplitter(Qt.Orientation.Horizontal)
    
    # Create Sound Player
    sound_player = SoundboardWidget()

    # Create Sound Modifier
    sound_modifier = AudioModifierWidget()

    # Add to Splitter
    splitter.addWidget(sound_player)
    splitter.addWidget(sound_modifier)

    # Set initial sizes (30% left, 70% right)
    width = ars_window.width()
    splitter.setSizes([int(width * 0.3), int(width * 0.7)])

    # Connect signal: when sound selected in player, load in modifier
    sound_player.sound_selected.connect(sound_modifier.load_from_path)

    # Integrate with SplitterOverlay
    if hasattr(ars_window, 'splitter_overlay'):
        overlay = ars_window.splitter_overlay
        
        # Set height
        height = getattr(ars_window.prefs, 'audio_studio_height', 300)
        overlay.bottom_height = height
        
        overlay.set_widget("bottom", splitter)
        
        # Force update to apply height and layout
        overlay._update_mask()
        overlay._update_geometries()
        overlay.update()
