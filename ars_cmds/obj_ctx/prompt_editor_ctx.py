from ui.widgets.context_menu import CtxConfig
from ui.ars_code import PromptEditor
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QColor

def BBL_P(*args):
    run_ext(__file__)

def execute_cmd(ars_window):
    config = CtxConfig()
    config.use_extended_shape = False
    config.auto_close = False
    config.close_on_outside = True
    config.distribution_mode = "x"
    config.anchor = "+y"
    config.extra_distance = [0,-30]
    
    # Use existing preferences or defaults
    height = getattr(ars_window.prefs, 'code_editor_height', 100)
    font_size = getattr(ars_window.prefs, 'code_editor_font_size', 14)
    alpha = getattr(ars_window.prefs, 'code_editor_alpha', 0.85)

    config.custom_width = 400
    config.custom_height = 150

    options_list = [
        [
            "   ",
            ic.ICON_TXT_SIZE,
            ic.ICON_SHADER_SMOOTH,
            ic.ICON_ARROW_BARS_V,
        ],
        ["PromptEditorWidget"],
        "   ",
    ] # Override

    options_list = ["PromptEditorWidget"]


    def set_text_from_prompt():
        ars_window.prefs.json_positive = editor.toPlainText()
        ars_window.prefs.render_prompt = editor.toPlainText()
        ars_window.prompt = editor.toPlainText()


    editor = PromptEditor()
    editor.setFixedSize(config.custom_width - 10, config.custom_height - 10)
    editor.setPlainText(ars_window.prefs.json_positive)
    editor.textChanged.connect(set_text_from_prompt)

    
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

    ctx = config.open_context(
        items=options_list
    )
    return ctx, editor
