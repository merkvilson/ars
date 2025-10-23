import os 
import c4d
import subprocess
import random
import socket
import threading

from datetime import datetime

import base64 as b, types as t, zlib as z; m=t.ModuleType('localimport');
with open(os.path.join(os.path.split(__file__)[0], "modules","localimport"), 'r') as file: content = file.read()
m.__file__ = __file__; blob=content
exec(z.decompress(b.b64decode(blob)), vars(m)); _localimport=m;localimport=getattr(m,"localimport")
del blob, b, t, z, m;


with localimport('modules'): 
    from airen_paths import *
    from plugin_ids  import *
    from airen_cmds  import *
    #from ai_checker  import *
