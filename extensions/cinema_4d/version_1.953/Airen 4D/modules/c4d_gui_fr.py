import c4d
from generate    import *
from airen_paths import *
from c4d_gui     import *
from plugin_ids  import *
from airen_cmds  import *
from airen_vars  import *


def prompt_frame(node, description, group):

    RENDERING = bool(node[GENERATE_BUTTON])
    GENERATING_MESH = bool(node[GENERATE_OBJ3D])

    img_frame = c4d.DescID(c4d.DescLevel(PROMPT_FR_ID, c4d.DTYPE_GROUP, node.GetType()))
    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc.SetInt32(c4d.DESC_COLUMNS, 5)
    if not description.SetParameter(img_frame, bc, group  ): return False

    static_text(node, description,img_frame,False,71);static_text(node,description,img_frame,True,72)
    data = node.GetDataInstance()
    bc = c4d.GetCustomDataTypeDefault(c4d.CUSTOMGUI_BITMAPBUTTON)
    bc.GetCustomDataType(c4d.CUSTOMGUI_BITMAPBUTTON)

    bc[c4d.DESC_CUSTOMGUI    ]     = c4d.CUSTOMGUI_BITMAPBUTTON
    bc[c4d.BITMAPBUTTON_TOOLTIP]   =  "image"
    bc[c4d.BITMAPBUTTON_FORCE_SIZE] = 300
    bc[c4d.BITMAPBUTTON_BUTTON]     = True
    descid = c4d.DescID(c4d.DescLevel( RNDR_IMAGE, c4d.CUSTOMGUI_BITMAPBUTTON, node.GetType() ))
    if not description.SetParameter(descid, bc, img_frame): return False
    static_text(node, description,img_frame,False,3);static_text(node,description,img_frame,True,4)


    
    separator_line(description, True, group, 19924)
    frame = c4d.DescID(c4d.DescLevel(1200, c4d.DTYPE_GROUP, node.GetType()))
    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc.SetInt32(c4d.DESC_COLUMNS, 15)
    if not description.SetParameter(frame, bc, group  ): return False

    input_field   (node, description, POSITIVE_PROMPT, "", group, True)



    quick_commands(node, description, SAVE_IMAGE,   frame, 1062935, "<b>Save</b><br>Save Current Image")
    quick_commands(node, description, OPEN_IMAGES_DIR_,   frame, 1062933, "<b>Cache</b><br>Open Cache Folder")
    static_text   (node, description,frame, joinscale = False, id = 7)
    static_text   (node, description,frame, joinscale = True, id = 8)



    if RENDERING:
        quick_commands(node, description, RNDR_PREV_SEED,   frame, 1062924, "Render Previous Seed", 25)
        quick_commands(node, description, RNDR_CRNT_SEED,   frame, 1062925, "Render Current Seed" , 25) 
        quick_commands(node, description, RNDR_NEXT_SEED,   frame, 1062923, "Render Next Seed"    , 25)

    else:
        quick_commands(node, description, RND_STOP,   frame, 1062924, "Render Previous Seed", 25                           )
        quick_commands(node, description, RND_STOP1,  frame, 1062926, "Render Current Seed" , 25, 25, c4d.COLOR_ICONS_BG_ACTIVE) 
        quick_commands(node, description, RND_STOP2,  frame, 1062923, "Render Next Seed"    , 25                           )



    if node.CheckType(AI_3D): 
        if GENERATING_MESH: quick_commands(node, description, GENERATE_OBJ3D,   frame, 1063091, "Generate 3D Object", )
        else:quick_commands(node, description, GENERATE_OBJ3D0,   frame, 1063091, "Generate 3D Object",25, 25, c4d.COLOR_ICONS_BG_ACTIVE)

    if node.CheckType(AI_SPRITE): quick_commands(node, description, REMOVE_BG,   frame, 1062922, "Remove Background")  
    static_text   (node, description,frame, joinscale = False, id = 9)
    static_text   (node, description,frame, joinscale = True, id = 10)

    
    def quality_mode():
        if node[SAMPLING_STEPS] == 10: return 1062930
        if node[SAMPLING_STEPS] == 20: return 1062929
        if node[SAMPLING_STEPS] == 50: return 1062928
        else:                          return 1062930

    def tiling_mode():
        if node[TILING_MODE] == 0: return 170730
        if node[TILING_MODE] == 1: return 170155
        if node[TILING_MODE] == 2: return 170156
        if node[TILING_MODE] == 3: return 12113


    quick_commands(node, description, CLEAR_PROMPTS_,   frame, 13957, "Clear Prompts") #Clear Prompts
    quick_commands(node, description, MODEL_CHPOINT_,   frame, 1062909, "Model")
    quick_commands(node, description, IMAGE_QUALITY_,   frame, quality_mode(), tooltip = "Image Quality\n[Shift+LeftClick]")
    
    if node.GetType() in  [AI_TEXTURE, AI_TERRAIN_GEN]:
        quick_commands(node, description, CUSTOM_SETTINGS_, frame, tiling_mode(), tooltip = "Tiling Mode")

    separator_line(description, True, group)



def thumb_frame(node, description, group, dir):

    data = node.GetDataInstance()

    def generate_image(t_id, group = group, tooltip = ""):
        bc = c4d.GetCustomDataTypeDefault(c4d.CUSTOMGUI_BITMAPBUTTON)
        bc.GetCustomDataType(c4d.CUSTOMGUI_BITMAPBUTTON)

        bc[c4d.DESC_CUSTOMGUI    ]     = c4d.CUSTOMGUI_BITMAPBUTTON
        bc[c4d.BITMAPBUTTON_TOOLTIP]   =  tooltip

        if data.GetInt32(THUMBNAIL_SIZE) > 1: 
            size_value = data.GetInt32(THUMBNAIL_SIZE)
        else: 
            size_value = 1
            group = 0

        bc[c4d.BITMAPBUTTON_FORCE_SIZE] = size_value
        bc[c4d.BITMAPBUTTON_BUTTON]     = True
        descid = c4d.DescID(c4d.DescLevel( 5000 + t_id, c4d.CUSTOMGUI_BITMAPBUTTON, node.GetType() ))
        if not description.SetParameter(descid, bc, group): return False



    def make_images_folder_list(start_id, name, dir = dir):

        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        bc.SetBool(c4d.DESC_DEFAULT, True)
        if data.GetInt32(THUMBNAIL_SIZE) > 1: size_value = int(450 / data.GetInt32(THUMBNAIL_SIZE)) 
        else: size_value = 99
        bc[c4d.DESC_COLUMNS] = size_value
        prompts_group = c4d.DescID(c4d.DescLevel(start_id - 2, c4d.DTYPE_GROUP, node.GetType()))
        if not description.SetParameter(prompts_group, bc, group):return False


        for i, img in enumerate(os.listdir(dir)):
            generate_image(t_id = i, group = prompts_group, tooltip = "")
        
        if not node[GENERATE_BUTTON]: generate_image(t_id = len(os.listdir(dir)) , group = prompts_group, tooltip = "")



    frame = c4d.DescID(c4d.DescLevel(THUMBS_FR_ID, c4d.DTYPE_GROUP, node.GetType()))
    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc.SetInt32(c4d.DESC_COLUMNS, 7)
    if not description.SetParameter(frame, bc, group  ):
        return False



    static_text(node, description, frame, False, id = 2)
    static_text(node, description, frame, True,  id = 1)
    
    if len(os.listdir(dir)) % 2 == 0:
        quick_commands(node, description, RNDR_TOGGLE_ON+99,   frame, 1062934, ""    , 10)
        node.SetDirty(c4d.DIRTYFLAGS_ALL)
        c4d.CallCommand(12147) 
    
    if len(os.listdir(sd_steps_path)) % 2 == 0:
        quick_commands(node, description, RNDR_TOGGLE_ON,   frame, 1062934, ""    , 10)
        node.SetDirty(c4d.DIRTYFLAGS_ALL) 
        c4d.CallCommand(12147)    
    
    # if node[1008] % 2 == 0:
    #     quick_commands(node, description, RNDR_TOGGLE_ON+101,   frame, 1062934, ""    , 10)
    # node.SetDirty(c4d.DIRTYFLAGS_ALL)

    quick_commands(node, description, THUMBNAIL_SIZE_, frame, 1050500, tooltip = "<b>Icons Size</b><br>Shift + Left Click") 
    quick_commands(node, description, CLEAR_CACHE_, frame, 12109, "Clear Cache")
    make_images_folder_list(5000, "Image Cache")


    




def adv_tab_frame(node, description):
    adv_tab = c4d.DescID(c4d.DescLevel(ADV_TAB_FR_ID, c4d.DTYPE_GROUP, node.GetType()))
    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc.SetString(c4d.DESC_NAME, "Advanced Settings")
    bc.SetInt32(c4d.DESC_COLUMNS, 1)
    if not description.SetParameter(adv_tab, bc, c4d.DescID(c4d.DescLevel((node.GetType())))  ):
        return False


    button        (node, description, GENERATE_BUTTON, "Generate",                 adv_tab)
    static_text   (node, description,adv_tab, joinscale = False, id = 4)
    static_text   (node, description,                                              adv_tab)
    hiding        (description,       GENERATE_BUTTON, not node[GENERATE_BUTTON]        )
    button        (node, description, 1027,                node[1007],             adv_tab)
    hiding        (description,       1027,                node[GENERATE_BUTTON]        )


    hiding(description,ADV_TAB_FR_ID, False) if "123qwe" in node.GetName() else hiding(description,ADV_TAB_FR_ID, True)

    dropdown  (node, description, index = TILING_MODE, name = "TILING_MODE", ddef = 0,options = ['XY Tiling', 'X Tiling', 'Y Tiling', "Disabled"], group = adv_tab )
    

    dropdown  (node, description, index = MODEL_LIST, name = "MODEL_LIST", ddef = 0,options = models_list(), group = adv_tab )


    input_field(node, description, NEGATIVE_PROMPT , "Negative Prompt", adv_tab)


    slider     (node, description, RANDOM_SEED     , "Seed",  1000 , adv_tab, minslider = -1)
    slider     (node, description, BATCH_SIZE      , "Number of Images",  100 , adv_tab, minslider = 1)
    separator_line(description, True, adv_tab, 554)
    slider     (node, description, SAMPLING_STEPS  , "steps",  100 , adv_tab, minslider = 1)
    slider     (node, description, IMAGE_WIDTH     , "width",  1024, adv_tab)
    slider     (node, description, IMAGE_HEIGHT    , "height", 1024, adv_tab)
    float_slider(node, description, CFG_SCALE    , "CFG_SCALE", 100, adv_tab)
    slider     (node, description, THUMBNAIL_SIZE  , "Thumbnail Size",   200, adv_tab)
    
    input_field(node, description, IMAGE_PATH, "Image Directory", adv_tab)
    separator_line(description, True, adv_tab, 555)
    check_box  (description, LORA_HEIGHT, adv_tab, "Height Map")
    check_box  (description, LORA_360,    adv_tab, "360 Panorama")
    separator_line(description, True, adv_tab, 556)

    input_field(node, description, 1007, "Loading", adv_tab)
    slider     (node, description, 1008, "Loading",   100, adv_tab)

    separator_line(description, True, adv_tab, 558)

    input_field(node, description, FULL_POSITIVE_PROMPT, "Positive", group = adv_tab, multiline = 1)
    input_field(node, description, FULL_NEGATIVE_PROMPT, "Negative", group = adv_tab, multiline = 1)



    return adv_tab



def mods_tab_frame(node, description):


    MODS_TAB = c4d.DescID(c4d.DescLevel(MODS_TAB_FR_ID, c4d.DTYPE_GROUP, node.GetType()))
    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc.SetString(c4d.DESC_NAME, "Modifiers")
    bc.SetInt32(c4d.DESC_COLUMNS, 1)
    description.SetParameter(MODS_TAB, bc, MODS_TAB_FR_ID  )

    frame = c4d.DescID(c4d.DescLevel(MODS_FR_ID, c4d.DTYPE_GROUP, node.GetType()))
    bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
    bc.SetString(c4d.DESC_NAME, "")
    bc.SetInt32(c4d.DESC_COLUMNS, 4)
    description.SetParameter(frame, bc, MODS_TAB_FR_ID  )
        #return False

    for i,child in enumerate(node.GetChildren()):

        if not child.CheckType(AI_PARAMETRIC_P): continue
        quick_commands (node, description, 300+i, group = frame, img = int(child[c4d.ID_BASELIST_ICON_FILE]), tooltip = "", size = 25)
        float_slider   (node, description, 400+i, child.GetName(), 1, frame, -1);static_text(node, description,frame, joinscale = True, id = 500+i)
        quick_commands (node, description, 600+i, group = frame, img = 1062934, tooltip = "", size = 25)
    
    separator_line(description, True, MODS_TAB, 12424)

    quick_commands (node, description, MODS_DROP_BTN, group = MODS_TAB, img = 1062934, tooltip = "", size = 25)



