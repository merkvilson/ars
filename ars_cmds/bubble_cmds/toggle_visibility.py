from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor


def BBL_EYE(*arg):
    run_ext(__file__)


def execute_plugin(ars_window):

    # Compute visibility states
    grid = ars_window.viewport.grid
    is_grid = grid._grid_visible
    is_x = grid._x_axis_visible
    is_y = grid._y_axis_visible
    is_z = grid._z_axis_visible
    is_xyz = is_x and is_y and is_z

    config = ContextMenuConfig()
    config.show_value = True
    config.auto_close = False

    options_list = [
        ic.ICON_GRID,
        ic.ICON_AXIS_X,
        ic.ICON_AXIS_Y,
        ic.ICON_AXIS_Z,
        ic.ICON_GIZMO_AXIS_3D,
    ]

    def update_xyz_toggle(ctx):
        new_is_xyz = grid._x_axis_visible and grid._y_axis_visible and grid._z_axis_visible
        ctx.update_item(ic.ICON_GIZMO_AXIS_3D, "toggle_values", (0, 1, new_is_xyz))
        ars_window.viewport._update_grid()

    config.callbackL = {
        ic.ICON_GRID: lambda: grid.set_grid_visible(),

        ic.ICON_AXIS_X: lambda: (
            grid.set_x_axis_visible(),
            update_xyz_toggle(ctx)
        ),

        ic.ICON_AXIS_Y: lambda: (
            grid.set_y_axis_visible(),
            update_xyz_toggle(ctx)
        ),

        ic.ICON_AXIS_Z: lambda: (
            grid.set_z_axis_visible(),
            update_xyz_toggle(ctx)
        ),

        ic.ICON_GIZMO_AXIS_3D: lambda: (
            grid.set_xyz_visible(),
            ctx.update_item(ic.ICON_AXIS_X, "toggle_values", (0, 1, grid._x_axis_visible)),
            ctx.update_item(ic.ICON_AXIS_Y, "toggle_values", (0, 1, grid._y_axis_visible)),
            ctx.update_item(ic.ICON_AXIS_Z, "toggle_values", (0, 1, grid._z_axis_visible)),
            update_xyz_toggle(ctx)  # Update ars_window after toggling all axes
        ),
    }

    config.additional_texts = {
        ic.ICON_AXIS_X: "X",
        ic.ICON_AXIS_Y: "Y",
        ic.ICON_AXIS_Z: "Z",
        ic.ICON_GRID: "grid",
        ic.ICON_GIZMO_AXIS_3D: "xyz",
    }

    config.toggle_values = {
        ic.ICON_GRID: is_grid,
        ic.ICON_AXIS_X: is_x,
        ic.ICON_AXIS_Y: is_y,
        ic.ICON_AXIS_Z: is_z,
        ic.ICON_GIZMO_AXIS_3D: is_xyz,
    }

    ctx = open_context(
        items=options_list,
        config=config
    )
    ctx.symbol = ic.ICON_EYE
