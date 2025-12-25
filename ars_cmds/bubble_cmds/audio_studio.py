from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from ui.sound_player.audio_widget import AudioStudio
from ui.widgets.context_menu import CtxConfig


BBL_AUDIO_STUDIO_CONFIG = {"symbol": ic.ICON_VOLUME_2, "hotkey": "shift+A", "visible": False}
def BBL_AUDIO_STUDIO(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    config = CtxConfig()
    config.dock_area = "bottom"
    config.auto_close = False
    config.close_on_outside = False

    # Create Audio Studio Widget
    audio_studio = AudioStudio()

    config.custom_widget_items = {"audio_studio": audio_studio}
    options_list = ["audio_studio"]
    
    ctx = config.open_context(items=options_list, parent=ars_window.central_widget)