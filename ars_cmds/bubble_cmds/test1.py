from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor


def BBL_TEST(*args):
    run_ext(__file__)


def execute_plugin(ars_window):
    config = ContextMenuConfig()

    ctx = open_context(
        parent=ars_window.central_widget,
        items=["1", "2"],
        position=ars_window.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )
