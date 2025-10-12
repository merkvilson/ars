from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic


def BBL_EYE(self, position):
    # Compute visibility states
    grid = self.viewport.grid
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
        self.viewport._update_grid()

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
            update_xyz_toggle(ctx)  # Update self after toggling all axes
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
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
