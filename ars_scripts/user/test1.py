def view_selected():
    obj = get_selected()
    if not obj: return
    xyz=obj.get_position()
    ars_window.viewport.cam.move_to(center=tuple(xyz), offset=5, animate=True)
    
    
view_selected()
