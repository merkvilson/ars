import c4d
import os
import subprocess
import json
import shutil

from urllib import request, parse



from generate    import *
from airen_paths import *
from c4d_gui     import *
from plugin_ids  import *
from airen_cmds  import *
from airen_vars  import *

def set_default_renderer():
    doc = c4d.documents.GetActiveDocument()
    rdata = doc.GetActiveRenderData()
    rdata[c4d.RDATA_RENDERENGINE] = 0


def render_is_running():

    start_new_render = False
    
    req = request.Request("http://127.0.0.1:8188/queue")
    with request.urlopen(req) as response:
        data = json.load(response)
        if data['queue_running']: start_new_render = True

    #print("render_is_running")

    return start_new_render


def comfy_interrupt():
    request.urlopen(request.Request("http://127.0.0.1:8188/interrupt", method="POST"))


def render_simple_prompt(node, workflow_path, output_path):

    delete_all_files_in_folder(sd_steps_path)


    if render_is_running(): return

    json_fl = os.path.join(os.path.split(os.path.split(__file__)[0])[0], "res", "workflow", workflow_path)
    with open(json_fl, 'r') as read_file: prompt_text = read_file.read()

    prompt_prefix = ""

    #if node.CheckType(AI_BG): prompt_prefix = "Background. "


    prompt = json.loads(prompt_text)
    prompt["4"]  ["inputs"] ["ckpt_name"]       = models_list(False)[node[MODEL_LIST]]
    prompt["6"]  ["inputs"] ["text"]            = prompt_prefix + node[POSITIVE_PROMPT] 
    prompt["7"]  ["inputs"] ["text"]            = node[NEGATIVE_PROMPT]
    prompt["15"] ["inputs"] ["seed"]            = node[RANDOM_SEED]
    prompt["15"] ["inputs"] ["steps"]           = node[SAMPLING_STEPS]
    prompt["15"] ["inputs"] ["cfg"]             = node[CFG_SCALE]
    prompt["5"]  ["inputs"] ["width"]           = node[IMAGE_WIDTH]
    prompt["5"]  ["inputs"] ["height"]          = node[IMAGE_HEIGHT]
    prompt["5"]  ["inputs"] ["batch_size"]      = node[BATCH_SIZE]
    prompt["15"] ["inputs"] ["tileX"]           = node[TILING_MODE] in [0,1]
    prompt["15"] ["inputs"] ["tileY"]           = node[TILING_MODE] in [0,2]
    prompt["18"] ["inputs"] ["filename_prefix"] = output_path

    queue_prompt(prompt)



def apply_parametric_settings(name, p_type, influence, ico):

    doc = c4d.documents.GetActiveDocument()
    sel_objs = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)

    c4d.CallCommand(AI_PARAMETRIC_P)

    def check_obj(obj):
        if 'PROMPT_EFFECTOR_0' in obj.GetName(): 
            obj.SetName(name)
            obj[PARAMETRIC_TYPE] = p_type
            obj[PARAMETRIC_INFLUENCE] = influence
            obj[c4d.ID_BASELIST_ICON_FILE] = ico

            mode_tag = obj.MakeTag(AI_INTER_TAG)
            mode_tag[INTER_MODE] = 1

            slider_tag = obj.MakeTag(AI_INTER_TAG)
            slider_tag[INTER_MODE] = 0


            for sel_obj in sel_objs:
                if sel_obj.GetType() in gens_ids:
                    obj.InsertUnder(sel_obj)
                    obj.DelBit(c4d.BIT_ACTIVE)
                    sel_obj.SetBit(c4d.BIT_ACTIVE)
                    print("True")
                else:
                    print(sel_objs)


        if obj.GetDown():
            child = obj.GetDown()
            while child:
                check_obj(child)
                child = child.GetNext()

    
    all_objects = doc.GetObjects()
    
    # Iterate through each object and check if it's a spline
    for obj in all_objects:
        check_obj(obj)

    c4d.EventAdd()





def apply_defaults(node, specific_settings):

    set_default_renderer()

    data = node.GetDataInstance()

    GENERATE_BUTTON_SETTING = True
    TILING_MODE_SETTING = 3

    IMAGE_WIDTH_SETTING    = 512
    IMAGE_HEIGHT_SETTING   = 512
    SAMPLING_STEPS_SETTING = 20

    CFG_SCALE_SETTING = 8

    LORA_HEIGHT_SETTING = False
    LORA_360_SETTING = False

    if specific_settings == "bg": 
        IMAGE_WIDTH_SETTING    = 512
        IMAGE_HEIGHT_SETTING   = 512
        SAMPLING_STEPS_SETTING = 25

    elif specific_settings == "tex": 
        TILING_MODE_SETTING = 0

    elif specific_settings == "dome": 
        TILING_MODE_SETTING = 1

    elif specific_settings == "terain": 
        LORA_HEIGHT_SETTING = True


    data.SetInt32(GENERATE_BUTTON, GENERATE_BUTTON_SETTING) #Button Generate
    data.SetBool(TILING_MODE, TILING_MODE_SETTING)

    data.SetInt32(MODEL_LIST, 0) #Model/Checkpoint

    data.SetString(POSITIVE_PROMPT, "")
    data.SetString(NEGATIVE_PROMPT, "")

    data.SetInt32(RANDOM_SEED, 1) #Seed
    data.SetInt32 (BATCH_SIZE,  1)
    data.SetInt32(SAMPLING_STEPS, SAMPLING_STEPS_SETTING) #Steps

    data.SetFloat(CFG_SCALE, CFG_SCALE_SETTING) 



    data.SetInt32(IMAGE_WIDTH, IMAGE_WIDTH_SETTING)
    data.SetInt32(IMAGE_HEIGHT, IMAGE_HEIGHT_SETTING) #Size

    data.SetInt32(THUMBNAIL_SIZE, 50) #Size

    data.SetString(1007, "Generate TXT")
    data[IMAGE_PATH] =  "NO File"

    data.SetBool(LORA_HEIGHT, LORA_HEIGHT_SETTING) #Lora Height
    data.SetBool(LORA_360,    LORA_360_SETTING) #Lora 360




    data.SetString(FULL_POSITIVE_PROMPT, "")
    data.SetString(FULL_NEGATIVE_PROMPT, "")


    data.SetInt32(1008, 0) #Size



    # Parametric Prompt


    data.SetString(PARAMETRIC_PROMPT, "")
    data.SetString(PARAMETRIC_OUTPUT, "")
    data.SetString(PARAMETRIC_PROMPT_A, "")
    data.SetString(PARAMETRIC_PROMPT_B, "")
    data.SetReal(PARAMETRIC_INFLUENCE, 0)
    data.SetInt32(PARAMETRIC_TYPE, 0)
    data.SetInt32(LORA_DROPDOWN, 0)
    data.SetString(LORA_KEYWORDS, "")

    data.SetBool(NEG_POS_BTN, True)
    data.SetBool(NEG_POS_CHK, True)



def render_frame():

    if c4d.CheckIsRunning(c4d.CHECKISRUNNING_EXTERNALRENDERING): return

    doc = c4d.documents.GetActiveDocument()
    rd = doc.GetActiveRenderData()

    rd = doc.GetActiveRenderData()
    rd[c4d.RDATA_GLOBALSAVE] = False
    rd[c4d.RDATA_MULTIPASS_ENABLE] = False

    rdata = rd.GetData()
    rdata[c4d.RDATA_XRES], rdata[c4d.RDATA_YRES] = 512, 512
    rdata[c4d.RDATA_FILMASPECT] = 1
    rdata[c4d.RDATA_PIXELASPECT] = 1

    xres, yres = int(rdata[c4d.RDATA_XRES]), int(rdata[c4d.RDATA_YRES])
    bmp = c4d.bitmaps.BaseBitmap()
    bmp.Init(x=xres, y=yres, depth=24, )

    c4d.documents.RenderDocument(doc, rdata, bmp, c4d.RENDERFLAGS_EXTERNAL)

    save_path = os.path.join(sd_render_path, "depth.jpg")

    bmp.Save(name = save_path, format=c4d.FILTER_JPG)




def queue_prompt(prompt):

    if not render_is_running():
        p = {"prompt": prompt}
        data = json.dumps(p).encode('utf-8')
        req =  request.Request("http://127.0.0.1:8188/prompt", data=data)
        request.urlopen(req)




def models_list(name = True):
    models = [model for model in os.listdir(ai_paths_cmd("checkpoints")) if model.endswith(".safetensors")]
    models_name = [model[:-len('.safetensors')].replace("_"," ").title() for model in models]
    if name: return models_name
    else:    return models




def find_spline():

    def check_spline(obj):
        # Check if the object is a spline
        if isinstance(obj.GetCache(), c4d.LineObject) or obj.CheckType(5101):
            obj.SetName(obj.GetName() + "_SPLINE")
        
        # Check if the object has any children
        if obj.GetDown():
            # If yes, recursively call this function for each child object
            child = obj.GetDown()
            while child:
                check_spline(child)
                child = child.GetNext()

    def main():
        # Get the active document
        doc = c4d.documents.GetActiveDocument()
        
        # Check if there's a document
        if doc is None:
            return
        
        # Get the list of all objects in the scene
        all_objects = doc.GetObjects()
        
        # Iterate through each object and check if it's a spline
        for obj in all_objects:
            check_spline(obj)



def find_obj(obj_type):
    obj_found = False
    doc = c4d.documents.GetActiveDocument()

    def check_spline(obj):
        nonlocal obj_found  # Declare obj_found as nonlocal

        if obj.CheckType(obj_type):
            obj_found = True
        
        if obj.GetDown():
            child = obj.GetDown()
            while child:
                check_spline(child)
                child = child.GetNext()

    for obj in doc.GetObjects():
        check_spline(obj)
        if obj_found:
            break
        
    return obj_found




def delete_all_files_in_folder(folder_path):
    if not os.path.exists(folder_path): return
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path): os.remove(file_path)



def rename_files_by_index(folder_path):
    # Get all files (exclude directories)
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    # Sort them alphabetically
    files.sort()

    # Determine zero-padding length based on file count
    padding = len(str(len(files)))

    for index, filename in enumerate(files, start=1):
        # Get file extension
        abc, ext = os.path.splitext(filename)
        
        # New name with zero padding
        new_name = f"{str(index).zfill(padding)}{ext}"
        
        # Paths for renaming
        old_path = os.path.join(folder_path, filename)
        new_path = os.path.join(folder_path, new_name)

        os.rename(old_path, new_path)






def save_current_image(image_dir, node = None, folder = sd_saved_render):

    if not os.listdir(image_dir):
        return True

    key_bc = c4d.BaseContainer()
    if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.BFM_INPUT_CHANNEL, key_bc):
        if not key_bc[c4d.BFM_INPUT_QUALIFIER] & c4d.QSHIFT:
            
            pic_dir = os.path.join(image_dir, os.listdir(image_dir)[-1])
            
            if not os.listdir(folder):
                new_pic_name = "0.png"
            
            else:
                rename_files_by_index(folder)
                new_pic_name = os.listdir(folder)[-1]
                new_pic_name = new_pic_name[ : -len(".png")]
                new_pic_name = int(new_pic_name) + 1
                new_pic_name = f"{new_pic_name}.png"
            
            new_pic_dir = os.path.join(folder,new_pic_name)

            shutil.copy(pic_dir, new_pic_dir )
        
        else: 
            folder = c4d.storage.LoadDialog(type=c4d.FILESELECTTYPE_IMAGES,title="Save Image", flags=c4d.FILESELECT_SAVE)
            pic_dir = os.path.join(image_dir, os.listdir(image_dir)[-1])
            shutil.copy(pic_dir, folder+"_image.png")



def apply_last_image(node, dir):

    img_list = os.listdir(dir)

    if len(img_list) > 0:
        full_path = os.path.join(dir, img_list[0])
        node[IMAGE_PATH] = full_path
        node.SetDirty(c4d.DIRTYFLAGS_ALL)
        c4d.EventAdd()
    else:
        print("No Images Detected!") 





def import_obj(selectedFile):
    doc = c4d.documents.GetActiveDocument()


    plug = c4d.plugins.FindPlugin(c4d.FORMAT_OBJ2IMPORT, c4d.PLUGINTYPE_SCENELOADER)
    if plug is None: raise RuntimeError("Failed to retrieve the obj importer.")

    data = dict()
    # Sends MSG_RETRIEVEPRIVATEDATA to OBJ import plugin
    if not plug.Message(c4d.MSG_RETRIEVEPRIVATEDATA, data):
        raise RuntimeError("Failed to retrieve private data.")

    # BaseList2D object stored in "imexporter" key hold the settings
    objImport = data.get("imexporter", None)
    if objImport is None:
        raise RuntimeError("Failed to retrieve BaseContainer private data.")

    # Defines the settings
    objImport[c4d.OBJIMPORTOPTIONS_POINTTRANSFORM_FLIPX]  = False
    objImport[c4d.OBJIMPORTOPTIONS_POINTTRANSFORM_FLIPY]  = False
    objImport[c4d.OBJIMPORTOPTIONS_POINTTRANSFORM_FLIPZ]  = False
    objImport[c4d.OBJIMPORTOPTIONS_POINTTRANSFORM_SWAPXY] = False
    objImport[c4d.OBJIMPORTOPTIONS_POINTTRANSFORM_SWAPXZ] = False
    objImport[c4d.OBJIMPORTOPTIONS_POINTTRANSFORM_SWAPYZ] = True
    objImport[c4d.OBJIMPORTOPTIONS_IMPORT_UVS] = c4d.OBJIMPORTOPTIONS_UV_ORIGINAL
    objImport[c4d.OBJIMPORTOPTIONS_SPLITBY] = c4d.OBJIMPORTOPTIONS_SPLITBY_OBJECT
    objImport[c4d.OBJIMPORTOPTIONS_MATERIAL] = c4d.OBJIMPORTOPTIONS_MATERIAL_MTLFILE

    # Finally imports without dialogs
    if not c4d.documents.MergeDocument(doc, selectedFile, c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MATERIALS, None):
        raise RuntimeError("Failed to load the document.")

    # Pushes an update event to Cinema 4D
    c4d.EventAdd()
