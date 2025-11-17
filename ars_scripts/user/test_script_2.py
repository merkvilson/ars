from ui.widgets.context_menu import ContextMenuConfig, open_context, find_all_open_context_menus

for ctw_widget in find_all_open_context_menus():
    print(ctw_widget.symbol)