"""
Example usage of the find_all_open_context_menus function.

This demonstrates how to find and work with all open context menus in the application.
"""

from ui.widgets.context_menu import find_all_open_context_menus


def example_usage():
    """Examples of how to use find_all_open_context_menus"""
    
    # Example 1: Find all open context menus globally
    open_menus = find_all_open_context_menus()
    print(f"Found {len(open_menus)} open context menus")
    
    # Example 2: Find all open context menus from a specific widget (e.g., main_window)
    # open_menus = find_all_open_context_menus(main_window)
    
    # Example 3: Check if any menus are open
    if find_all_open_context_menus():
        print("At least one context menu is currently open")
    else:
        print("No context menus are currently open")
    
    # Example 4: Close all open context menus
    for menu in find_all_open_context_menus():
        menu.close_animated()
    
    # Example 5: Get information about each open menu
    for i, menu in enumerate(find_all_open_context_menus()):
        print(f"Menu {i+1}:")
        print(f"  - Position: {menu.pos()}")
        print(f"  - Size: {menu.size()}")
        print(f"  - Distribution mode: {menu.config.distribution_mode}")
        print(f"  - Number of items: {len(menu.processed_items)}")
    
    # Example 6: Find menus with specific configurations
    radial_menus = [
        menu for menu in find_all_open_context_menus() 
        if menu.config.distribution_mode == 'radial'
    ]
    print(f"Found {len(radial_menus)} radial menus")
    
    # Example 7: Find menus that have hotkey items
    menus_with_hotkeys = [
        menu for menu in find_all_open_context_menus()
        if menu.config.hotkey_items
    ]
    print(f"Found {len(menus_with_hotkeys)} menus with hotkeys")
    
    # Example 8: Get specific item values from all open menus
    for menu in find_all_open_context_menus():
        for item in menu.processed_items:
            value = menu.get_value(item.symbol)
            if value is not None:
                print(f"Item '{item.symbol}' has value: {value}")


if __name__ == "__main__":
    example_usage()
