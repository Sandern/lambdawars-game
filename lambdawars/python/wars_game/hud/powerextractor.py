from srcbase import Color
from entities import C_HL2WarsPlayer
from core.hud import BaseHudSingleUnit
from vgui.controls import Label

class HudBuildPowerExtractor(BaseHudSingleUnit):
    def __init__(self, parent, config={}):    
        super().__init__(parent, config)
        
        self.powerleft = Label(self, "PowerLeft", "")
        
    def ApplySchemeSettings(self, schemeobj):
        super().ApplySchemeSettings(schemeobj)
        
        self.powerleft.SetFgColor(Color(255,255,255,255))
        self.powerleft.SetBgColor(Color(200,200,200,0))
        
    def PerformLayout(self):
        super().PerformLayout()
        
        x, y = self.GetPos()
        w, h = self.GetSize()
        self.powerleft.SetPos(int(w*0.01), int(h*0.45))
        self.powerleft.SetSize(int(w*1.0), int(h*0.1))
        
    def Update(self):
        super().Update()
        
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player or player.CountUnits() != 1:
            return
            
        unit = player.GetUnit(0)
        
        powerleft = unit.resourcesleft['power']
        if powerleft != -1:
            self.powerleft.SetText('Power Left: %d' % (powerleft))
        else:
            self.powerleft.SetText('Power Left: infinite')