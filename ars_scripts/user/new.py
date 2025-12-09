from ars_cmds.core_cmds.cursor_to_xyz import get_xyz
p = get_xyz(ars_window)
add_primitive('cube', position=(p[0],p[1]+1,p[2]),animated=0 )
