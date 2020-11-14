from core.gamerules import GamerulesInfo, WarsBaseGameRules
from collections import defaultdict
from gamerules import GameRules

from core.usermessages import usermessage
from playermgr import OWNER_LAST
if isserver:
    from entities import CServerOnlyPointEntity, gEntList
    
@usermessage()
def UpdateFlagTimer(playercapturing, savedtime, curstartcapturetime, **kwargs):
    """ Processes updates for the capture flag timer """
    hud = GameRules().hudrefs['HudCaptureTheFlag'].Get()
    hud.playercapturing = playercapturing
    hud.savedtime = savedtime
    hud.curstartcapturetime = curstartcapturetime

# Gamerules
class CaptureTheFlag(WarsBaseGameRules):
    def __init__(self):
        super().__init__()
        
        self.capturepoint = None
        
    def CheckGameOver(self):
        if self.gameover:   # someone else quit the game already
            # check to see if we should change levels now
            if self.intermissionendtime < gpGlobals.curtime:
                self.ChangeToGamelobby()  # intermission is over
            return True
        return False
        
    def InitGamerules(self):
        super().InitGamerules()
        
        self.savedownertime = defaultdict( lambda : 0.0 )
        self.curstartownertime = None

        if isserver:
            self.capturepoint = gEntList.FindEntityByClassname(None, 'capturetheflag_point')
            if not self.capturepoint:
                PrintWarning("No capturetheflag_point entity found!")
                return
            self.capturepoint.Enable()

    def ShutdownGamerules(self):
        super().ShutdownGamerules()
        
        if isserver:
            if self.capturepoint:
                self.capturepoint.Disable()
                self.capturepoint = None

    def OnFlagOwnerChanged(self, newowner, oldowner):
        if self.curstartownertime and self.SAVEOLDTIME:
            self.savedownertime[oldowner] += gpGlobals.curtime - self.curstartownertime
        self.curstartownertime = gpGlobals.curtime
        
        UpdateFlagTimer(self.capturepoint.GetOwnerNumber(), 
                self.savedownertime[self.capturepoint.GetOwnerNumber()], self.curstartownertime)
        
    def MainThink(self):
        super().MainThink()
        if self.gameover:
            return
            
        if self.capturepoint:
            if self.curstartownertime and self.capturepoint.GetOwnerNumber() >= OWNER_LAST:
                ownertime = (gpGlobals.curtime - self.curstartownertime) + self.savedownertime[self.capturepoint.GetOwnerNumber()]
                if ownertime > self.CAPTURE_TIME and not self.capturepoint.playercapturing:
                    # We got a winner!
                    self.GoToIntermission()
        
    CAPTURE_TIME = 2.0 * 60.0
    SAVEOLDTIME = False
    
'''
class CaptureTheFlagInfo(GamerulesInfo):
    name = 'capturetheflag'
    displayname = '#CaptureTheFlag_Name'
    description = '#CaptureTheFlag_Description'
    cls = CaptureTheFlag
    mappattern = '^wmp_.*$'
    factionpattern = '^antlions$'
    huds = [
        'core.hud.HudCaptureTheFlag',
        'core.hud.HudPlayerNames',
    ]
'''
    