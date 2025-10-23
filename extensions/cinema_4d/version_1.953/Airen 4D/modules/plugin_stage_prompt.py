import c4d
from generate    import *
from airen_paths import *
from c4d_gui     import *
from plugin_ids  import *
from airen_cmds  import *
from airen_vars  import *
from c4d_gui_fr  import *
from c4d_gui_cmd import *


class Ostage_prompt(c4d.plugins.ObjectData): 

    def Init(self, node):

        apply_defaults(node, "stage")

        self.dir = sd_dome_dir if node.CheckType(AI_SKY) else sd_bg_dir

        apply_last_image(node, self.dir)


        return True


    def GetDDescription(self, node, description, flags):
        data = node.GetDataInstance()
        node_tp = node.GetType()

        if not description.LoadDescription(node_tp): return False

        settings_tab = c4d.DescID(c4d.DescLevel(1101, c4d.DTYPE_GROUP, node.GetType()))
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        bc.SetString(c4d.DESC_NAME, "Prompt")
        bc.SetInt32(c4d.DESC_COLUMNS, 1)
        if not description.SetParameter(settings_tab, bc, c4d.DescID(c4d.DescLevel((node.GetType())))  ):
            return False


        input_field(node, description, POSITIVE_PROMPT, "Positive", group = settings_tab, multiline = 1)
        input_field(node, description, NEGATIVE_PROMPT, "Negative", group = settings_tab, multiline = 1)
        
        adv_tab = adv_tab_frame(node, description)


        mods_tab = mods_tab_frame(node, description)

        return (True, flags | c4d.DESCFLAGS_DESC_LOADED)



    def Message(self, node, type, data):

        if type == c4d.MSG_MENUPREPARE:
            print("Stage Created")

        if type == c4d.MSG_BASECONTAINER:
            print("c4d.MSG_BASECONTAINER")

        if type == c4d.MSG_DESCRIPTION_CHECKUPDATE:

            desc_id = data["descid"][0].id

            mods_tab_msg(desc_id, node)

        if type == c4d.MSG_EDIT:
            pass
            #mods_tab_msg(0, node)


        return True




    def GetVirtualObjects(self, op, hh):

        final_ptompt_update(op)

        orig = op.GetDown()
        doc = op.GetDocument()
        if orig is None: 
            op.SetDirty(c4d.DIRTYFLAGS_ALL) 
            return None

        gch      = op.GetAndCheckHierarchyClone(hh=hh, op=orig, allchildren=True, flags = c4d.HIERARCHYCLONEFLAGS_ASPOLY, )
        dirty    = gch['dirty']
        clone    = gch['clone']

        if not dirty: return clone
        else: op.SetDirty(c4d.DIRTYFLAGS_ALL) 

        if clone is None: return None


        return None

