import c4d


def separator_line(description, line, group, t_id = 1111111):
    bc                         = c4d.BaseContainer()
    bc[c4d.DESC_CUSTOMGUI    ] = c4d.CUSTOMGUI_SEPARATOR
    bc[c4d.DESC_SEPARATORLINE] = line
    descid                     = c4d.DescID(c4d.DescLevel(t_id))
    if not description.SetParameter(descid, bc, group):  return False



def quick_commands (node, description, t_id, group = c4d.ID_SHADERPROPERTIES, img = 0, tooltip = " ", size = 25 , sizey = None, color = None, img2 = None):

    dtype = c4d.DTYPE_BOOL

    bc = c4d.GetCustomDataTypeDefault(dtype)
    #bc.GetCustomDataType(c4d.CUSTOMGUI_BITMAPBUTTON)

    if color: bc[c4d.BITMAPBUTTON_BACKCOLOR] = color
    bc[c4d.DESC_CUSTOMGUI    ]          = c4d.CUSTOMGUI_BITMAPBUTTON
    bc[c4d.BITMAPBUTTON_TOOLTIP]        = tooltip
    bc[c4d.BITMAPBUTTON_FORCE_SIZE]     = size
    if sizey: bc[c4d.BITMAPBUTTON_FORCE_SIZE_Y]   = sizey
    bc[c4d.BITMAPBUTTON_BUTTON]         = True
    bc[c4d.BITMAPBUTTON_ICONID1]        = img
    if img2: bc[c4d.BITMAPBUTTON_ICONID2] = img2
    bc[c4d.BITMAPBUTTON_TOGGLE]         = True

    descid = c4d.DescID(c4d.DescLevel(t_id, dtype ))
    if not description.SetParameter(descid, bc, group): return False




def input_field(node, description, t_id, name, group, multiline = False): 
    dtype = c4d.DTYPE_STRING
    bc = c4d.GetCustomDataTypeDefault(dtype)
    if multiline: bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_STRINGMULTI
    bc[c4d.DESC_NAME] = name
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF
    descid = c4d.DescID(c4d.DescLevel(t_id, c4d.CUSTOMGUI_STRINGMULTI, ))
    if not description.SetParameter(descid, bc, group): return False


def dropdown(node, description, index, name, options, ddef, group):
    bc                     = c4d.GetCustomDataTypeDefault(c4d.DTYPE_LONG)
    bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_CYCLE
    bc[c4d.DESC_DEFAULT  ] = ddef
    bc[c4d.DESC_NAME     ] = name
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF

    opt = c4d.BaseContainer()
    for i, option in enumerate(options): opt[i] = option
    bc.SetContainer(c4d.DESC_CYCLE, opt)
    descid = c4d.DescID(c4d.DescLevel(index, c4d.DTYPE_LONG, node.GetType()))
    if not description.SetParameter(descid, bc, group): return False




def hiding(description, t_id = 0, hide = True):
    paramID = c4d.DescID(c4d.DescLevel(t_id))
    if description.GetSingleDescID() is None or paramID.IsPartOf(description.GetSingleDescID())[0]:
        bc = description.GetParameterI(paramID, None) 
        bc[c4d.DESC_HIDE] = hide







def slider(node, description, t_id, name, max_val, group , minslider = 0):
    dtype                  = c4d.DTYPE_LONG
    bc                     = c4d.GetCustomDataTypeDefault(dtype)
    bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_LONGSLIDER
    bc[c4d.DESC_MINSLIDER] = minslider
    bc[c4d.DESC_MAXSLIDER] = max_val
    bc[c4d.DESC_MAX      ] = 2048
    bc[c4d.DESC_STEP     ] = 1
    bc[c4d.DESC_DEFAULT  ] = 50
    bc[c4d.DESC_NAME     ] = name
    bc[c4d.DESC_ANIMATE  ] = c4d.DESC_ANIMATE_OFF
    descid = c4d.DescID(c4d.DescLevel(t_id, dtype, ))
    if not description.SetParameter(descid, bc, group): return False




def float_slider(node, description, t_id, name, max_val, group , minslider = 0):
    dtype                  = c4d.DTYPE_REAL
    bc                     = c4d.GetCustomDataTypeDefault(dtype)
    bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_REALSLIDER
    # bc[c4d.DESC_UNIT]      = c4d.DESC_UNIT_PERCENT
    bc[c4d.DESC_MINSLIDER] = minslider
    bc[c4d.DESC_MAXSLIDER] = max_val
    bc[c4d.DESC_STEP     ] = 0.01
    bc[c4d.DESC_DEFAULT  ] = 0.0
    bc[c4d.DESC_NAME     ] = name
    bc[c4d.DESC_ANIMATE  ] = c4d.DESC_ANIMATE_OFF
    descid = c4d.DescID(c4d.DescLevel(t_id, dtype, ))
    if not description.SetParameter(descid, bc, group): return False




def button(node, description, t_id, name, group):
    bc                     = c4d.GetCustomDataTypeDefault(c4d.CUSTOMGUI_BUTTON)
    bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_BUTTON
    bc[c4d.DESC_NAME     ] = name
    descid                 = c4d.DescID(c4d.DescLevel(t_id))
    if not description.SetParameter(descid, bc, group): return False




def check_box( description, t_id, group, name):
    bc                     = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL)
    bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_BOOL
    bc[c4d.DESC_NAME     ] = name
    descid                 = c4d.DescID(c4d.DescLevel(t_id, c4d.DTYPE_BOOL))
    if not description.SetParameter(descid, bc, group):  return False






def date_time_clock( description, t_id, group, name, time_ctrl, date_ctrl):
    bc = c4d.BaseContainer()
    bc[c4d.DATETIME_TIME_CONTROL] = time_ctrl
    bc[c4d.DATETIME_DATE_CONTROL] = date_ctrl
    bc[c4d.DESC_CUSTOMGUI] = c4d.DATETIME_GUI
    bc[c4d.DESC_NAME     ] = name
    descid                 = c4d.DescID(c4d.DescLevel(t_id, c4d.DTYPE_BOOL))
    if not description.SetParameter(descid, bc, group):  return False






def static_text( node, description, group, joinscale = True, id = 3,):
    #return
    bc                     = c4d.GetCustomDatatypeDefault(c4d.DTYPE_STATICTEXT)
    bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_STATICTEXT
    bc[2403              ] = joinscale

    descid = c4d.DescID(c4d.DescLevel(id, c4d.DTYPE_STATICTEXT, node.GetType()))
    if not description.SetParameter(descid, bc, group): return False

