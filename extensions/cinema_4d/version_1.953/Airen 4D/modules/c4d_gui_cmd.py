import c4d
import os
import subprocess


from airen_paths import *
from c4d_gui     import *
from plugin_ids  import *
from airen_cmds  import *
from airen_vars  import *

DEBUG_MODE = True



def thumbnail_dropdown_msg(desc_id, node, dir):

    if desc_id == CLEAR_CACHE_:
        if c4d.gui.QuestionDialog("Delete all images?"): 
            for img in os.listdir(dir):
                os.remove(os.path.join(dir, img))

    if desc_id == OPEN_IMAGES_DIR_:
        subprocess.Popen(['explorer', dir])

    if desc_id == SAVE_IMAGE:
        print("SAVE_IMAGE")
        save_current_image(sd_steps_path,None,dir)
        #subprocess.Popen(['explorer', dir])

    if desc_id >= 5000 and desc_id < 6000:

        pic = os.listdir(dir)[desc_id - 5000] 
        pic_dir = os.path.join(dir, pic) 

        def popup_menu():

            n = c4d.FIRST_POPUP_ID
            bc = c4d.BaseContainer()
            bc.InsData(n+4, f'Apply     &i{12169}&')
            bc.InsData(n+0, f'Remove    &i{12109}&')
            bc.InsData(n+3, f'Save      &i{12098}&')
            bc.InsData(n+1, f'Picture Viewer &i{430000700}&')

            result = c4d.gui.ShowPopupDialog(None, bc,2147483647,2147483647, )

            if result == n+4:  
                node[IMAGE_PATH] = pic_dir 
                node[1008] = node[1008] +1
                node.SetDirty(c4d.DIRTYFLAGS_ALL)
                c4d.EventAdd()

            if result == n+0:  os.remove(pic_dir)
            if result == n+1:  c4d.documents.LoadFile(pic_dir)
            if result == n+3: 
                save_current_image(dir)
                print("TODO: Save Function")



        popup_menu()
        return True






def prompt_frame_msg(desc_id, node):

    if desc_id == RNDR_IMAGE:
        c4d.documents.LoadFile(node[IMAGE_PATH])

    elif desc_id == GENERATE_BUTTON: 

        comfy_interrupt()
        print("GENERATE_BUTTON")


    elif desc_id in [RND_STOP, RND_STOP1, RND_STOP2]:
        comfy_interrupt()

        


    elif desc_id in [RNDR_PREV_SEED,RNDR_CRNT_SEED,RNDR_NEXT_SEED,]:
        if desc_id == RNDR_PREV_SEED: node[RANDOM_SEED] = node[RANDOM_SEED] - 1
        if desc_id == RNDR_CRNT_SEED: node[RANDOM_SEED] = node[RANDOM_SEED]
        if desc_id == RNDR_NEXT_SEED: node[RANDOM_SEED] = node[RANDOM_SEED] + 1
        node[IMAGE_PATH] = ''

    elif desc_id == CLEAR_PROMPTS_: #Clean Prompts
        node[NEGATIVE_PROMPT]=""
        node[POSITIVE_PROMPT]=""

    elif desc_id == MODEL_CHPOINT_:

        def check_q(value):
            if node[MODEL_LIST] == value: return "&c&"
            else: return ""

        n = c4d.FIRST_POPUP_ID
        bc = c4d.BaseContainer()

        for i, model in enumerate(models_list()):bc.InsData(n+i, f'{model}{check_q(i)}')
        #bc.InsData(0, '') 
        #bc.InsData(n+1000, f'Install Checkpoint &i{1063092}&')
        result = c4d.gui.ShowPopupDialog(None, bc,2147483647,2147483647, )
        if result: 
            node[MODEL_LIST] = result - n
            model = models_list(False)[node[MODEL_LIST]][:-len(".safetensors")]
           
            c4d.EventAdd()


    elif desc_id == IMAGE_QUALITY_:

        def check_r(value):
            if node[IMAGE_WIDTH] == value: return "&c&"
            else: return ""

        def check_q(value):
            if node[SAMPLING_STEPS] == value: return "&c&"
            else: return ""

        n = c4d.FIRST_POPUP_ID
        bc = c4d.BaseContainer()

        bc.InsData(n+5, f'Low Quality    &i{1062930}&{check_q(10)}')
        bc.InsData(n+6, f'Medium Quality &i{1062929}&{check_q(20)}')
        bc.InsData(n+7, f'High Quality   &i{1062928}&{check_q(50)}')

        bc.InsData(0, '')

        bc.InsData(n+2, f'256x256    &i{100004706}&{check_r(256)}')
        bc.InsData(n+3, f'512x512    &i{100004707}&{check_r(512)}')
        bc.InsData(n+4, f'1024x1024  &i{100004708}&{check_r(1024)}')

        key_bc = c4d.BaseContainer()
        if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.BFM_INPUT_CHANNEL, key_bc):
            if key_bc[c4d.BFM_INPUT_QUALIFIER] & c4d.QSHIFT:
                if DEBUG_MODE:print("Shift key is pressed")
                if   node[SAMPLING_STEPS] == 10: node[SAMPLING_STEPS] = 20
                elif node[SAMPLING_STEPS] == 20: node[SAMPLING_STEPS] = 50
                elif node[SAMPLING_STEPS] == 50: node[SAMPLING_STEPS] = 10
            else:
                result = c4d.gui.ShowPopupDialog(None, bc,2147483647,2147483647, )

                if result == n+2: node[IMAGE_WIDTH], node[IMAGE_HEIGHT] = 256, 256
                if result == n+3: node[IMAGE_WIDTH], node[IMAGE_HEIGHT] = 512, 512
                if result == n+4: node[IMAGE_WIDTH], node[IMAGE_HEIGHT] = 1024, 1024

                if result == n+5: node[SAMPLING_STEPS] = 10
                if result == n+6: node[SAMPLING_STEPS] = 20
                if result == n+7: node[SAMPLING_STEPS] = 50

        return True


    elif desc_id == THUMBNAIL_SIZE_:
        def check_mode(value):
            if node[THUMBNAIL_SIZE] == value: return "&c&"
            else: return ""

        n = c4d.FIRST_POPUP_ID
        bc = c4d.BaseContainer()
        bc.InsData(n+1, f'Small Icons  &i{100004706}& {check_mode(50)}')
        bc.InsData(n+2, f'Medium Icons &i{100004707}& {check_mode(100)}')
        bc.InsData(n+3, f'Large Icons  &i{100004708}& {check_mode(150)}')
        bc.InsData(0, '')
        bc.InsData(n+4, f'No Icons &i{170036}&{check_mode(1)}')

        key_bc = c4d.BaseContainer()
        if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.BFM_INPUT_CHANNEL, key_bc):
            if key_bc[c4d.BFM_INPUT_QUALIFIER] & c4d.QSHIFT:
                if DEBUG_MODE:print("Shift key is pressed")
                if   node[THUMBNAIL_SIZE] ==  50: node[THUMBNAIL_SIZE] = 100
                elif node[THUMBNAIL_SIZE] == 100: node[THUMBNAIL_SIZE] = 150
                elif node[THUMBNAIL_SIZE] == 150: node[THUMBNAIL_SIZE] = 50
            else:
                result = c4d.gui.ShowPopupDialog(None, bc,2147483647,2147483647, )

                if result == n+1: node[THUMBNAIL_SIZE] = 50
                if result == n+2: node[THUMBNAIL_SIZE] = 100
                if result == n+3: node[THUMBNAIL_SIZE] = 150
                if result == n+4: node[THUMBNAIL_SIZE] = 1
        return True

    elif desc_id == CUSTOM_SETTINGS_:

        def check_mode(value):
            if node[TILING_MODE] == value: return "&c&"
            else: return ""

        n = c4d.FIRST_POPUP_ID
        bc = c4d.BaseContainer()
        bc.InsData(n+1, f'XY Tiling  &i{170730}& {check_mode(0)}')
        bc.InsData(n+2, f'X Tiling   &i{170155}& {check_mode(1)}')
        bc.InsData(n+3, f'Y Tiling   &i{170156}& {check_mode(2)}')
        bc.InsData(0, '')
        bc.InsData(n+4, f'Disabled &i{12113}&{check_mode(3)}')

        key_bc = c4d.BaseContainer()

        result = c4d.gui.ShowPopupDialog(None, bc,2147483647,2147483647, )

        if result == n+1: node[TILING_MODE] = 0
        if result == n+2: node[TILING_MODE] = 1
        if result == n+3: node[TILING_MODE] = 2
        if result == n+4: node[TILING_MODE] = 3

        return True




def mods_tab_msg(desc_id, node):

 
    if desc_id in [MODS_DROP_BTN, 0]:
        node.SetBit(c4d.BIT_ACTIVE)


        bc = c4d.BaseContainer()
        bc.InsData(1, 'Modifiers')
        for mod_id in mods_ids: bc.InsData(mod_id, "CMD")

        key_bc = c4d.BaseContainer()
        if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.BFM_INPUT_CHANNEL, key_bc):
            result = c4d.gui.ShowPopupDialog(None, bc,2147483647,2147483647, )
            

        return True



def name_to_msg(desc_id, node):
    pass
    '''
    if node[PARAMETRIC_TYPE] == 0:
        
        if desc_id == PARAMETRIC_PROMPT:
            node.SetName(node[PARAMETRIC_PROMPT])
        else: 
            node[PARAMETRIC_PROMPT] = node.GetName()
    '''




def final_ptompt_update(node):
    return

    parametric_prompts_pos = []
    parametric_prompts_neg = []
    for obj in node.GetChildren():
        if obj.CheckType(AI_PARAMETRIC_P) and obj[c4d.ID_BASEOBJECT_GENERATOR_FLAG]:
            prompt = obj[PARAMETRIC_OUTPUT]
            if obj[NEG_POS_CHK]: parametric_prompts_pos.append(prompt)
            else: parametric_prompts_neg.append(prompt)


    parametric_prompts_pos = "\n".join(parametric_prompts_pos) if parametric_prompts_pos else ""
    parametric_prompts_neg = "\n".join(parametric_prompts_neg) if parametric_prompts_neg else ""

    FULL_POSITIVE_VALUE = node[POSITIVE_PROMPT] + ". " + parametric_prompts_pos
    FULL_NEGATIVE_VALUE = node[NEGATIVE_PROMPT] + ". " + parametric_prompts_neg

    node[FULL_POSITIVE_PROMPT] = FULL_POSITIVE_VALUE
    node[FULL_NEGATIVE_PROMPT] = FULL_NEGATIVE_VALUE

    if not True in [tag.CheckType(AI_INTER_TAG) for tag in node.GetTags()]:
        tag = node.MakeTag(AI_INTER_TAG)
        tag[INTER_MODE] = 2
    





def MSG_DESCRIPTION_GETBITMAP_msg(data, dir, node):

    bmp = c4d.bitmaps.BaseBitmap()

    def bmp_init(fullpath):
        bmp.InitWith(fullpath)
        data["bmp"] = bmp
        data["w"] = bmp.GetBw()
        data["h"] = bmp.GetBh()
        data["filled"] = True

    thumbnails = os.listdir( dir ); n = 0

    for thum in thumbnails:
        deid = 5000 + n; n += 1
        if data['id'][0].id == deid:
            fullpath = os.path.join( dir, thum )
            bmp_init(fullpath)

    # if data['id'][0].id == len(os.listdir(dir)) + 5000:
    #     if os.listdir( sd_steps_path ):
    #         fullpath = os.path.join( sd_steps_path, os.listdir( sd_steps_path )[-1] )
    #         bmp_init(fullpath)


    if data['id'][0].id == RNDR_IMAGE:
        if node[IMAGE_PATH]: bmp_init(node[IMAGE_PATH])
        elif os.listdir( sd_steps_path ):
                fullpath = os.path.join( sd_steps_path, os.listdir( sd_steps_path )[-1] )
                bmp_init(fullpath)


    else: return True

    return True



def GetDParameter_thumbs_MSG(id_0, bmp, flags, node, id, dir):

    if id_0 == RNDR_IMAGE:
        flags = flags | c4d.DESCFLAGS_DESC_LOADED
        data = c4d.BitmapButtonStruct(node, id, bmp.GetDirty())
        return True, data, flags | c4d.DESCFLAGS_GET_PARAM_GET        

    for i in range(len(os.listdir(dir))):
        if id_0 == 5000 + i:
            flags = flags | c4d.DESCFLAGS_DESC_LOADED
            data = c4d.BitmapButtonStruct(node, id, bmp.GetDirty())
            return True, data, flags | c4d.DESCFLAGS_GET_PARAM_GET

    else: return True