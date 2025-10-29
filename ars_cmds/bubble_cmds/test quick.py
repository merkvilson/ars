from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.core_cmds.load_object import selected_object
from ui.widgets.multi_line_input import MultiLineInputWidget
from PyQt6.QtCore import QPoint



def BBL_5(self, position):
    run_ext(__file__, self)

    
def main(self, position):
    
    if not selected_object(self):
        return
    else: default_object = selected_object(self)



    config = ContextMenuConfig()
    config.auto_close = False
    config.custom_height = 150
    config.custom_width = 410

    options_list = [ "text_widget" ]

    def set_text_from_prompt():
        default_object.set_text(text_widget.text_edit.toPlainText())

    text_widget = MultiLineInputWidget()
    text_widget.text_edit.setPlainText(default_object.prompt)
    text_widget.text_edit.textChanged.connect(set_text_from_prompt)

    text_widget.setFixedSize(400, 140)

    config.custom_widget_items = {"text_widget": text_widget}



    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )



def execute_plugin(window):
    main(window, QPoint(0, 0))













