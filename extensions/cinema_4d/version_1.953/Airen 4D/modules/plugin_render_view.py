import c4d
from generate import *
from airen_paths import *
from c4d_gui import *
from plugin_ids import *
from airen_cmds import *
from airen_vars import *
from c4d_gui_fr import *
from c4d_gui_cmd import *
from datetime import datetime
import time
import os
import subprocess

def bitmap_btn(id, size, sizey="None", icon_id=0, icon_id2=0, tooltip="", win=None, color=None):
    if sizey == "None": sizey = size
    bc = c4d.BaseContainer()
    bc[c4d.BITMAPBUTTON_BUTTON] = True
    bc[c4d.BITMAPBUTTON_FORCE_SIZE] = size
    bc[c4d.BITMAPBUTTON_TOGGLE] = True
    bc[c4d.BITMAPBUTTON_NOBORDERDRAW] = True
    if color: bc[c4d.BITMAPBUTTON_BACKCOLOR] = color
    bc[c4d.BITMAPBUTTON_DISABLE_FADING] = False
    bc[c4d.BITMAPBUTTON_ICONID1] = icon_id
    bc[c4d.BITMAPBUTTON_ICONID2] = icon_id2 if icon_id2 else None 
    bc[c4d.BITMAPBUTTON_TOOLTIP] = tooltip
    return win.AddCustomGui(id, c4d.CUSTOMGUI_BITMAPBUTTON, "", c4d.BFV_CENTER, 0, 0, bc)
def filler_space(win): win.AddStaticText(0, flags=c4d.BFH_SCALEFIT, initw=0, inith=0, name='', borderstyle=0)

def top_menu(bitmap_btn, win):
    win.LayoutFlushGroup(55)
    RENDERING = bool(win.stage_object()[GENERATE_BUTTON])
    def   __(): win.AddStaticText(0, flags=c4d.BFH_CENTER, initw=0, inith=0, name='  ', borderstyle=0)
    __()
    win.save_img   = bitmap_btn(win=win, id=100005, size=28, icon_id=1062935, tooltip="<b>Save</b><br>Save Current Frame")
    win.open_cache = bitmap_btn(win=win, id=OPEN_IMAGES_DIR_, size=28, icon_id=1062933, tooltip="<b>Cache</b><br>Open Cache Folder")
    win.send_to_pv = bitmap_btn(win=win, id=100004, size=28, icon_id=1062907, tooltip="<b>Picture Viewer</b><br>Send frame to Picture Viewer")
    filler_space(win)

    if RENDERING:
        win.reload_seed  = bitmap_btn(win=win, id=RNDR_PREV_SEED, size=28, icon_id=1062924, tooltip="<b>Render New Seed</b><br>Render with a new seed")
        win.start_render = bitmap_btn(win=win, id=GENERATE_BUTTON, size=28, icon_id=1062925, tooltip="<b>Render</b><br>Render with the same seed")
        win.reload_seed  = bitmap_btn(win=win, id=RNDR_NEXT_SEED, size=28, icon_id=1062923, tooltip="<b>Render New Seed</b><br>Render with a new seed")

    else:
        win.reload_seed  = bitmap_btn(win=win, id=RND_STOP, size=28, icon_id=1062924, tooltip="<b>Render New Seed</b><br>Render with a new seed")
        win.start_render = bitmap_btn(win=win, id=RND_STOP, size=28, icon_id=1062926, tooltip="<b>Render</b><br>Render with the same seed", color=c4d.COLOR_ICONS_BG_ACTIVE)
        win.reload_seed  = bitmap_btn(win=win, id=RND_STOP, size=28, icon_id=1062923, tooltip="<b>Render New Seed</b><br>Render with a new seed")
    filler_space(win)
    win.model_chpoint = bitmap_btn(win=win, id=MODEL_CHPOINT_, size=25, icon_id=1062909, tooltip="<b>Model</b><br>Change Model/Checkpoint")

    def QUALITY_CMD():
        if win.stage_object()[SAMPLING_STEPS] == 10: return 1062930
        if win.stage_object()[SAMPLING_STEPS] == 20: return 1062929
        if win.stage_object()[SAMPLING_STEPS] == 50: return 1062928

    def RESOLUTION_CMD():
        if win.stage_object()[IMAGE_WIDTH] == 256: return 100004706
        if win.stage_object()[IMAGE_WIDTH] == 512: return 100004707
        if win.stage_object()[IMAGE_WIDTH] == 1024: return 100004708

    win.image_quality = bitmap_btn(win=win, id=IMAGE_QUALITY_, size=25, icon_id=QUALITY_CMD(), tooltip="<b>Quality</b><br>Change Image Sampling Steps")
    win.image_res = bitmap_btn(win=win, id=IMAGE_RES_, size=25, icon_id=RESOLUTION_CMD(), tooltip="<b>Resolution</b><br>Change Image Dimensions")
    win.airen_settings = bitmap_btn(win=win, id=100010, size=25, icon_id=1062906, tooltip="<b>Settings</b><br>Additional Render Settings")
    __()
    win.LayoutChanged(55)

class ai_render_window(c4d.gui.GeDialog):
    def __init__(self):
        super().__init__()
        self.is_rendering = False  # Flag to control periodic rendering
        self.last_render_time = 0  # Track last render start time
        self.render_interval = 1.0  # Minimum interval between renders (1 second)
        self.last_image_check = 0  # Track last image check time
        self.image_check_interval = 0.5  # Check for new images every 0.5 seconds

    def InitValues(self):
        self.doc = c4d.documents.GetActiveDocument()
        self.rd = self.doc.GetActiveRenderData()
        self.new_ren_len = 0
        self.time_start = time.time()
        return True

    def CreateLayout(self):
        self.SetTitle("Airen Render View")
        self.SetBool(c4d.DESC_TITLEBAR, False)
        self.GroupBegin(id=0, flags=c4d.BFH_SCALEFIT, rows=1, title=" ", cols=2, groupflags=0)
        self.GroupBegin(id=1, flags=c4d.BFH_SCALEFIT, rows=1, title=" ", cols=1, groupflags=0)
        self.GroupBegin(id=55, flags=c4d.BFH_SCALEFIT, rows=1, title=" ", cols=20, groupflags=0)
        top_menu(bitmap_btn, self)
        self.GroupSpace(0, 0)
        self.GroupEnd()
        self.main_render_image = bitmap_btn(win=self, id=100001, size=512, icon_id=0, tooltip="")
        self.AddCustomGui(MODEL_LIST, c4d.CUSTOMGUI_PROGRESSBAR, "", c4d.BFH_SCALEFIT, 0, 0)

        # Add timeline group under the main render image
        self.GroupBegin(id=100, flags=c4d.BFH_SCALEFIT, rows=1, title="Timeline", cols=5, groupflags=0)
        self.rw_frame = self.AddSlider(102, c4d.BFH_SCALEFIT, initw=200, inith=20)
        self.SetLong(102, 0, min=0, max=100, step=1)  # Default range
        #self.AddButton(103, c4d.BFH_CENTER, name="Play")
        #self.AddButton(104, c4d.BFH_CENTER, name="Pause")
        #self.AddButton(105, c4d.BFH_CENTER, name="Next Frame")
        #self.AddButton(106, c4d.BFH_CENTER, name="Prev Frame")
        self.GroupEnd()

        self.TabGroupBegin(33, c4d.BFH_SCALEFIT, tabtype=c4d.TAB_VLTABS)
        self.GroupBegin(id=1222, flags=c4d.BFH_SCALEFIT, rows=1, title="Positive", cols=1, groupflags=0)
        self.prompt_input = self.AddMultiLineEditText(POSITIVE_PROMPT, c4d.BFH_SCALEFIT, 400, 80)
        self.SetString(POSITIVE_PROMPT, self.stage_object()[POSITIVE_PROMPT])
        self.GroupEnd()
        self.GroupBegin(id=2, flags=c4d.BFH_SCALEFIT, rows=1, title="Negative", cols=1, groupflags=0)
        self.neg_prompt_input = self.AddMultiLineEditText(NEGATIVE_PROMPT, c4d.BFH_SCALEFIT, 400, 90)
        self.GroupEnd()
        self.GroupEnd()
        return True

    def stage_object(self):
        doc = c4d.documents.GetActiveDocument()
        stage = None
        for obj in doc.GetObjects():
            if obj.CheckType(AI_SCENE_PROMPT):
                stage = obj
                break
        if not stage:
            stage = c4d.BaseObject(AI_SCENE_PROMPT)
            doc.InsertObject(stage)
            stage.ChangeNBit(c4d.NBIT_OM1_FOLD, c4d.NBITCONTROL_SET)
            c4d.EventAdd()
        return stage

    def queue_render(self):
        """Simplified to directly start a render without throttling (handled by Timer)."""
        self.start_airen_render()

    def start_airen_render(self):
        stage = self.stage_object()
        doc = c4d.documents.GetActiveDocument()
        rd = doc.GetActiveRenderData()
        render_frame()
        c4d.EventAdd()
        render_simple_prompt(stage, 'render.json', 'steps/img')
        self.last_render_time = time.time()  # Update last render time

    def update_image(self):
        current_time = time.time()
        if current_time - self.last_image_check < self.image_check_interval:
            return
        self.last_image_check = current_time
        try:
            if os.listdir(sd_steps_path):
                img = os.path.join(sd_steps_path, os.listdir(sd_steps_path)[-1])
                bmp = c4d.bitmaps.BaseBitmap()
                bmp.InitWith(img)
                self.main_render_image.SetImage(bmp, copybmp=True, secondstate=False)
        except:
            pass

    def Command(self, id, msg):
        stage = self.stage_object()
       
        if id == GENERATE_BUTTON:
            self.is_rendering = True
            if not render_is_running():
                self.start_airen_render()
            top_menu(bitmap_btn, self)
        
        elif id == RND_STOP:
            self.is_rendering = False
            top_menu(bitmap_btn, self)

        elif id == RNDR_PREV_SEED:
            stage[RANDOM_SEED] = stage[RANDOM_SEED] - 1

        elif id == RNDR_NEXT_SEED:
            stage[RANDOM_SEED] = stage[RANDOM_SEED] + 1

        elif id == 100004:
            if os.listdir(sd_steps_path):
                pic_dir = os.path.join(sd_steps_path, os.listdir(sd_steps_path)[-1])
                c4d.documents.LoadFile(pic_dir)

        elif id == 100005:
            save_current_image(sd_steps_path)

        elif id == 100001:
            print("clc")

        elif id == 102:
            print("clc")

        elif id == MODEL_CHPOINT_:
            def check_q(value):
                if stage[MODEL_LIST] == value: return "&c&"
                else: return ""
            n = c4d.FIRST_POPUP_ID
            bc = c4d.BaseContainer()
            for i, model in enumerate(models_list()):
                bc.InsData(n+i, f'{model}{check_q(i)}')
            result = c4d.gui.ShowPopupDialog(None, bc, 2147483647, 2147483647)
            if result:
                stage[MODEL_LIST] = result - n
                c4d.EventAdd()
        

        elif id == IMAGE_QUALITY_:
            def check_q(value):
                if stage[SAMPLING_STEPS] == value: return "&c&"
                else: return ""
            n = c4d.FIRST_POPUP_ID
            bc = c4d.BaseContainer()
            bc.InsData(n+5, f'Low Quality    &i{1062930}&{check_q(10)}')
            bc.InsData(n+6, f'Medium Quality &i{1062929}&{check_q(20)}')
            bc.InsData(n+7, f'High Quality   &i{1062928}&{check_q(50)}')
            result = c4d.gui.ShowPopupDialog(None, bc, 2147483647, 2147483647)
            if result == n+5:
                stage[SAMPLING_STEPS] = 10
                self.image_quality.SetImage(c4d.bitmaps.InitResourceBitmap(1062930))
            elif result == n+6:
                stage[SAMPLING_STEPS] = 20
                self.image_quality.SetImage(c4d.bitmaps.InitResourceBitmap(1062929))
            elif result == n+7:
                stage[SAMPLING_STEPS] = 50
                self.image_quality.SetImage(c4d.bitmaps.InitResourceBitmap(1062928))
            c4d.EventAdd()
        

        elif id == OPEN_IMAGES_DIR_:
            subprocess.Popen(['explorer', sd_saved_render])
        
       
        elif id == IMAGE_RES_:
            def check_r(value):
                if stage[IMAGE_WIDTH] == value: return "&c&"
                else: return ""
            n = c4d.FIRST_POPUP_ID
            bc = c4d.BaseContainer()
            bc.InsData(n+2, f'256x256    &i{100004706}&{check_r(256)}')
            bc.InsData(n+3, f'512x512    &i{100004707}&{check_r(512)}')
            bc.InsData(n+4, f'1024x1024  &i{100004708}&{check_r(1024)}')
            result = c4d.gui.ShowPopupDialog(None, bc, 2147483647, 2147483647)

            if result == n+2:
                stage[IMAGE_WIDTH] = 256
                stage[IMAGE_HEIGHT] = 256
                self.image_res.SetImage(c4d.bitmaps.InitResourceBitmap(100004706))

            elif result == n+3:
                stage[IMAGE_WIDTH] = 512
                stage[IMAGE_HEIGHT] = 512
                self.image_res.SetImage(c4d.bitmaps.InitResourceBitmap(100004707))

            elif result == n+4:
                stage[IMAGE_WIDTH] = 1024
                stage[IMAGE_HEIGHT] = 1024
                self.image_res.SetImage(c4d.bitmaps.InitResourceBitmap(100004708))
            self.rd[c4d.RDATA_XRES], self.rd[c4d.RDATA_YRES] = stage[IMAGE_WIDTH], stage[IMAGE_HEIGHT]

            c4d.EventAdd()

        elif id == 100010:
            def check_r(value):
                if value: return "&c&"
                else: return ""
            n = c4d.FIRST_POPUP_ID
            bc = c4d.BaseContainer()
            bc.InsData(n+2, f'Scene Prompt &i{14082}&{check_r(self.GetBool(SCENE_PROMPTS))}')
            mod_bc = c4d.BaseContainer()
            mod_bc.InsData(1, 'Modifiers')
            mod_bc.InsData(c4d.Ocube, "CMD")
            bc.SetContainer(2, mod_bc)
            bc.InsData(n+3, f'Option One   &i{100004707}&{check_r(False)}')
            bc.InsData(n+4, f'Option Two   &i{100004708}&{check_r(False)}')
            result = c4d.gui.ShowPopupDialog(None, bc, 2147483647, 2147483647)
            if result == n+2:
                self.SetBool(SCENE_PROMPTS, not self.GetBool(SCENE_PROMPTS))
        
        elif id in [IMAGE_WIDTH, IMAGE_HEIGHT]:
            self.rd[c4d.RDATA_XRES], self.rd[c4d.RDATA_YRES] = stage[IMAGE_WIDTH], stage[IMAGE_HEIGHT]
            c4d.EventAdd()

        return True

    def CoreMessage(self, id, msg):
        return c4d.gui.GeDialog.CoreMessage(self, id, msg)

    def Message(self, msg, result):
        self.update_image()
        if msg.GetId() == c4d.BFM_INTERACTEND:
            stage = self.stage_object()
            new_positive_prompt = self.GetString(POSITIVE_PROMPT)
            new_negative_prompt = self.GetString(NEGATIVE_PROMPT)
            if new_positive_prompt != stage[POSITIVE_PROMPT] or new_negative_prompt != stage[NEGATIVE_PROMPT]:
                stage[POSITIVE_PROMPT] = new_positive_prompt
                stage[NEGATIVE_PROMPT] = new_negative_prompt

        return c4d.gui.GeDialog.Message(self, msg, result)

    def AskClose(self):
        close = False
        not_close = True
        return close

    def Timer(self, msg):
        """Periodically trigger renders and update image."""
        current_time = time.time()
        if self.is_rendering and not render_is_running():
            if current_time - self.last_render_time >= self.render_interval:
                self.start_airen_render()
        self.update_image()
        return True



class Airen_Window(c4d.plugins.CommandData):
    dialog = None

    def Execute(self, doc):
        delete_all_files_in_folder(sd_steps_path)
        rdata = doc.GetActiveRenderData()
        rdata[c4d.RDATA_XRES], rdata[c4d.RDATA_YRES] = 512, 512
        rdata[c4d.RDATA_FILMASPECT] = 1
        rdata[c4d.RDATA_PIXELASPECT] = 1
        rdata[c4d.RDATA_RENDERENGINE] = 0
        c4d.EventAdd()
        if self.dialog is None:
            self.dialog = ai_render_window()
        self.dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC, pluginid=AI_RENDER_WINDOW, defaulth=0, defaultw=0)
        self.dialog.SetTimer(500)  # Set timer to call Timer every 500ms
        return True

    def RestoreLayout(self, sec_ref):
        if self.dialog is None:
            self.dialog = ai_render_window()
        self.dialog.SetTimer(500)  # Re-enable timer on layout restore
        return self.dialog.Restore(pluginid=AI_RENDER_WINDOW, secret=sec_ref)