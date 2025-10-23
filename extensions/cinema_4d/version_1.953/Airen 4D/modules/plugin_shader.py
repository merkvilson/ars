import c4d
from generate    import *
from airen_paths import *
from c4d_gui     import *
from plugin_ids  import *
from airen_cmds  import *
from airen_vars  import *
from c4d_gui_fr  import *
from c4d_gui_cmd import *


class AI0(c4d.plugins.ShaderData):


    def __init__(self) :
        self.bmp = c4d.bitmaps.BaseBitmap()
        return          


    def Init(self, node):

        apply_defaults(node, "tex")

        apply_last_image(node,sd_tex_dir)

        return True

    def GetDDescription(self, node, description, flags):
        if not description.LoadDescription(node.GetType()): return False

        settings_tab = c4d.DescID(c4d.DescLevel(1100, c4d.DTYPE_GROUP, node.GetType()))
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        bc.SetString(c4d.DESC_NAME, "Settings")
        bc.SetInt32(c4d.DESC_COLUMNS, 1)
        if not description.SetParameter(settings_tab, bc, c4d.DescID(c4d.DescLevel((node.GetType())))  ):
            return False

        prompt_frame(node, description, c4d.ID_SHADERPROPERTIES)
        thumb_frame(node, description, c4d.ID_SHADERPROPERTIES, sd_tex_dir)
        adv_tab_frame(node, description)


        return (True, flags | c4d.DESCFLAGS_DESC_LOADED)



    def GetDEnabling(self, node, id, t_data, flags, itemdesc):
        if id[0].id == GENERATE_BUTTON: return bool(node[GENERATE_BUTTON])
        return True

    def GetDParameter(self, node, id, flags):
        return GetDParameter_thumbs_MSG(id[0].id, self.bmp, flags, node, id, sd_tex_dir)


    def Message(self, node, type, data):



        if type == c4d.MSG_DESCRIPTION_COMMAND:

            desc_id = data['id'][0].id

            if desc_id == 1027:
                click_generate_button(node, "", sd_airen_exe_path, "", True)

        if type == c4d.MSG_DESCRIPTION_CHECKUPDATE:

            desc_id = data["descid"][0].id
            prompt_frame_msg(desc_id, node)
            thumbnail_dropdown_msg(desc_id, node, sd_tex_dir)

            if desc_id in [RNDR_PREV_SEED,RNDR_CRNT_SEED,RNDR_NEXT_SEED,]:

                render_simple_prompt(node, 'default.json', 'textures/tex_')

                return True


        if type == c4d.MSG_DESCRIPTION_GETBITMAP:
            return MSG_DESCRIPTION_GETBITMAP_msg(data, sd_tex_dir, node)


        return True


    def InitRender(self, sh, irs) :

        bmp = c4d.bitmaps.BaseBitmap()
        dir, file = os.path.split(__file__)
        
        bmp.InitWith(sh[IMAGE_PATH])

        self.bitmap = bmp
        return c4d.INITRENDERRESULT_OK


    def FreeRender(self, sh) :

        self.bitmap = None

    def Output(self, sh, cd) :
        x = int(cd.p.x * self.bitmap.GetBw())
        y = int(cd.p.y * self.bitmap.GetBh())
        col = self.bitmap.GetPixel(x, y)
        result = c4d.Vector(float(col[0]/256.0) , float(col[1]/256.0), float(col[2]/256.0))

        return result

