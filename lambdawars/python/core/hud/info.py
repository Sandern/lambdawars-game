""" Maps an hud name to a class. The hud class must register itself here by creating an info object """
import srcmgr
srcmgr.VerifyIsClient()

import gamemgr

# Hud db
dbid = 'hud'
dbhuds = gamemgr.dblist[dbid]

# Hud info entry
class HudInfo(gamemgr.BaseInfo):
    donotregister = False
    id = dbid
    #: Reference to VGUI class
    cls = None 
    #: Reference to CEF class
    cefcls = None 