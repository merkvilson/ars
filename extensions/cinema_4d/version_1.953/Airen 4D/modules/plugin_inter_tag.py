import c4d
from generate    import *
from airen_paths import *
from c4d_gui     import *
from plugin_ids  import *
from airen_cmds  import *
from airen_vars  import *
from c4d_gui_fr  import *

from c4d_gui_cmd import *





class Tbg_inter(c4d.plugins.TagData):

    def Init(self, node):

        data = node.GetDataInstance()

        data.SetInt32(INTER_MODE, 1)

        return True



    def GetDDescription(self, node, description, flags):
        data = node.GetDataInstance()
        node_tp = node.GetType()

        if not description.LoadDescription(node_tp): return False

        settings_tab = c4d.DescID(c4d.DescLevel(1101, c4d.DTYPE_GROUP, node.GetType()))
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        bc.SetString(c4d.DESC_NAME, "")
        bc.SetInt32(c4d.DESC_COLUMNS, 1)
        if not description.SetParameter(settings_tab, bc, c4d.DescID(c4d.DescLevel((node.GetType())))  ):
            return False

        dropdown  (node, description, index = INTER_MODE, name = "Mode", ddef = 0,options = ['Slider', 'Negative/Positive', 'Dropdown', "Disabled"], group = settings_tab )
        
        #hiding         (description, INTER_MODE, True)
    
        hiding         (description, 110050, True)
        

        return (True, flags | c4d.DESCFLAGS_DESC_LOADED)



    def Message(self, node, type, data):

        if node.GetBit(c4d.BIT_ACTIVE):

            node.DelBit(c4d.BIT_ACTIVE)
            c4d.EventAdd()
            #node.SetDirty(c4d.DIRTYFLAGS_ALL)

            obj = node.GetObject()
            obj.Edit() #Set Att Manager
            if node[INTER_MODE] == 1: obj[NEG_POS_CHK] = not obj[NEG_POS_CHK]

            elif node[INTER_MODE] == 2:
            
                bc = c4d.BaseContainer()
                bc.InsData(1, 'Modifiers')
                for mod_id in mods_ids: bc.InsData(mod_id, "CMD")

                key_bc = c4d.BaseContainer()
                if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.BFM_INPUT_CHANNEL, key_bc):
                    result = c4d.gui.ShowPopupDialog(None, bc,2147483647,2147483647, )


            return True
  



        if type == c4d.MSG_MENUPREPARE:  # Created
            node[c4d.ID_BASELIST_ICON_FILE] = 12427
            print(node)
            print ("Created Tag")

        if type == c4d.MSG_EDIT:
            print("Doit")
        return True



    def Execute(self, tag, doc, op, bt, priority, flags):


        if not op.CheckType(1062672): return c4d.EXECUTIONRESULT_OK

        if tag[INTER_MODE] == 0:

            obj_value = op[PARAMETRIC_INFLUENCE]

            value = int(c4d.utils.RangeMap(value=obj_value, mininput=-1, maxinput=1, minoutput=0, maxoutput=100, clampval=False))

            if obj_value == 1: img = "100.png"
            elif obj_value > 1: img = "100-0000.png"
            elif obj_value < -1: img = "0000-000.png"
            elif value < 10:  img = f'00{value}.png'
            else: img = f'0{value}.png'
            icons_path = os.path.join(plugin_path, 'res', 'Icons', 'slider', img)

        elif tag[INTER_MODE] == 1:
            img = 'pos.png' if op[NEG_POS_CHK] else 'neg.png'
            icons_path = os.path.join(plugin_path, 'res', 'Icons', img)

        else: icons_path = ""

        tag[c4d.ID_BASELIST_ICON_FILE] = icons_path

        return c4d.EXECUTIONRESULT_OK


class Cbg_inter(c4d.plugins.CommandData):
    def Execute(self, doc):

        objs = doc.GetActiveObjects(2)

        for obj in objs:
            obj.MakeTag(AI_INTER_TAG)

        c4d.EventAdd()

        return True
