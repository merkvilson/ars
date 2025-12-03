import c4d
import os

PLUGIN_ID = 1063060


class SizeArea(c4d.gui.GeUserArea):
    def Sized(self, w, h):
        self.Redraw()
        
    def DrawMsg(self, x1, y1, x2, y2, msg):
        w, h = self.GetWidth(), self.GetHeight()
        pos = self.Local2Screen()
        
        self.DrawSetPen(c4d.Vector(0.2, 0.2, 0.2))
        self.DrawRectangle(x1, y1, x2, y2)
        self.DrawSetTextCol(c4d.Vector(1, 1, 1), c4d.Vector(0, 0, 0))
        self.DrawText(f"Size: {w} x {h}", 10, 10)
        self.DrawText(f"Position: {pos}", 10, 30)


class WindowInfoDialog(c4d.gui.GeDialog):
    def CreateLayout(self):
        self.SetTitle("Window Info")
        self.area = SizeArea()
        self.AddUserArea(1000, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, initw=200, inith=100)
        self.AttachUserArea(self.area, 1000)
        return True
    
    def InitValues(self):
        self.SetTimer(100)  # Update every 100ms
        return True
    
    def Timer(self, msg):
        self.area.Redraw()


class WindowInfoCommand(c4d.plugins.CommandData):
    dialog = None
    
    def Execute(self, doc):
        if self.dialog is None:
            self.dialog = WindowInfoDialog()
        self.dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC, pluginid=PLUGIN_ID, defaultw=300, defaulth=150)
        return True
    
    def RestoreLayout(self, sec_ref):
        if self.dialog is None:
            self.dialog = WindowInfoDialog()
        return self.dialog.Restore(pluginid=PLUGIN_ID, secret=sec_ref)


if __name__ == "__main__":
    dir, file = os.path.split(__file__)
    bmp = c4d.bitmaps.BaseBitmap()
    bmp.InitWith(os.path.join(dir, "res", "render.png"))

    c4d.plugins.RegisterCommandPlugin(PLUGIN_ID, "Window Info", 0, bmp, "Shows window size", WindowInfoCommand())
