from ui.widgets.context_menu import ContextMenuConfig, open_context
from ui.ars_code import PromptEditor
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QColor

def BBL_P(*args):
    run_ext(__file__)

def execute_cmd(ars_window):
    config = ContextMenuConfig()
    config.use_extended_shape = False
    config.auto_close = False
    config.close_on_outside = False
    config.distribution_mode = "x"
    
    # Use existing preferences or defaults
    height = getattr(ars_window.prefs, 'code_editor_height', 500)
    font_size = getattr(ars_window.prefs, 'code_editor_font_size', 14)
    alpha = getattr(ars_window.prefs, 'code_editor_alpha', 0.85)

    config.custom_height = height
    config.custom_width = ars_window.width()
    config.extra_distance = [0, 99999]

    options_list = [
        [
            "   ",
            ic.ICON_TXT_SIZE,
            ic.ICON_SHADER_SMOOTH,
            ic.ICON_ARROW_BARS_V,
        ],
        ["   ", "PromptEditorWidget", "   "],
        "   ",
    ]

    editor = PromptEditor()
    editor.setFixedSize(int(ars_window.width() - 10), int(config.custom_height - int(44 * 1.5)))
    editor.setPlainText("# Prompt Editor\n# Type colors like red, blue, or #FF00AA to see them highlighted.\n# Use Alt + +/- to change font size of selected text.")
    
    editor.set_font_size(font_size)
    editor.set_alpha(alpha)

    config.custom_widget_items = {"PromptEditorWidget": editor}
    
    config.slider_values = {
        ic.ICON_SHADER_SMOOTH: (0, 100, alpha * 100),
        ic.ICON_ARROW_BARS_V: (int(44 * 1.5), ars_window.height() - int(44 * 1.5) - 20, height),
        ic.ICON_TXT_SIZE: (10, 48, font_size),
    }
    
    config.incremental_values = {
        ic.ICON_SHADER_SMOOTH: 3, 
        ic.ICON_ARROW_BARS_V: (-20, "y"),
        ic.ICON_TXT_SIZE: 1, 
    }
    
    config.slider_color = {ic.ICON_ARROW_BARS_V: QColor(0, 0, 0, 0)}

    config.callbackL = {
        ic.ICON_TXT_SIZE: lambda value: editor.set_font_size(value),
        ic.ICON_SHADER_SMOOTH: lambda value: (
            ctx.set_alpha(value / 2550.0),
            editor.set_alpha(value / 100.0), 
        ),
        ic.ICON_ARROW_BARS_V: lambda value: (
            ctx.resize_top(value),
            editor.setFixedHeight(int(value - int(44 * 1.5))),
        ),
    }

    ctx = open_context(
        items=options_list,
        config=config
    )
    return ctx, editor
