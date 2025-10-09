import os
from prefs.pref_controller import get_path
from .crop_img import crop_img

def make_screenshot(widget, callback=None, x=512, y=512, name = "screenshot.png"):

    path = os.path.join(    os.path.join(  get_path('input'), name))
    if widget.viewport.isVisible(): widget.viewport._canvas.native.grab().save(path)
    crop_img(path, path, int(x), int(y))

    callback()
