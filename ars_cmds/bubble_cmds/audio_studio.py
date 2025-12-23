from ui.widgets.context_menu import CtxConfig
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.util_cmds.open_file import open_file
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

    config = CtxConfig()
    config.use_extended_shape = False
    config.auto_close = False
    config.close_on_outside = False
    config.distribution_mode = "x"
    config.custom_height = getattr(ars_window.prefs, 'audio_studio_height', 600)
    config.custom_width = ars_window.width()
    config.extra_distance = [0, 99999]

    options_list = [
        [
            ic.ICON_ARROW_BARS_V,
            ic.ICON_SHADER_SMOOTH,
            "   ",
            ic.ICON_FOLDER_OPEN,
            "   ",
        ],
        ["   ", "AudioSplitter", "   "],
        "   ",
    ]

    available_height = int(config.custom_height - int(44 * 1.5))

    # Create Splitter (horizontal for player | modifier)
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.setFixedSize(int(ars_window.width() - 10), available_height)

    # Create Sound Player
    sound_player = SoundboardWidget()

    # Create Sound Modifier
    sound_modifier = AudioModifierWidget()

    # Add to Splitter
    splitter.addWidget(sound_player)
    splitter.addWidget(sound_modifier)

    # Set initial sizes (30% left, 70% right)
    splitter.setSizes([int((ars_window.width() - 10) * 0.3), int((ars_window.width() - 10) * 0.7)])

    # Connect signal: when sound selected in player, load in modifier
    sound_player.sound_selected.connect(sound_modifier.load_from_path)

    config.custom_widget_items = {
        "AudioSplitter": splitter
    }

    config.slider_values = {
        ic.ICON_SHADER_SMOOTH: (0, 100, getattr(ars_window.prefs, 'audio_studio_alpha', 1.0) * 100),
        ic.ICON_ARROW_BARS_V: (int(44 * 1.5), ars_window.height() - int(44 * 1.5) - 20, getattr(ars_window.prefs, 'audio_studio_height', 600)),
    }
    config.incremental_values = {
        ic.ICON_SHADER_SMOOTH: 3,
        ic.ICON_ARROW_BARS_V: (-20, "y"),
    }

    # Get sounds folder path
    sounds_dir = pref_controller.get_path("sounds")
    if not sounds_dir:
        sounds_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "res", "sounds")

    config.callbackL = {
        ic.ICON_FOLDER_OPEN: lambda: open_file(sounds_dir),
        ic.ICON_SHADER_SMOOTH: lambda value: (
            ctx.set_alpha(value / 2550.0),
            setattr(ars_window.prefs, 'audio_studio_alpha', value / 100.0),
        ),
        ic.ICON_ARROW_BARS_V: lambda value: (
            ctx.resize_top(value),
            splitter.setFixedHeight(int(value - int(44 * 1.5))),
            setattr(ars_window.prefs, 'audio_studio_height', int(value)),
        ),
    }

    ctx = config.open_context(items=options_list)
    return ctx, splitter
