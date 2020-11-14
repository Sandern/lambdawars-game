from srcbase import Color, HIDEHUD_STRATEGIC
from vgui import GetClientMode, CHudElement, scheme, AddTickSignal
from vgui.controls import Panel, Label
import playermgr
from utils import ScreenWidth
from gamerules import GameRules

class HudCaptureTheFlag(CHudElement, Panel):
    def __init__(self):
        CHudElement.__init__(self, "HudCaptureTheFlag")
        Panel.__init__(self, GetClientMode().GetViewport(), "HudCaptureTheFlag")
        self.SetHiddenBits( HIDEHUD_STRATEGIC ) 
        
        self.SetPaintBackgroundEnabled(True)
        
        self.timer = Label(self, "Timer", "-")
        self.timer.SetContentAlignment(Label.a_center)
        
        self.playercapturing = None
        
        AddTickSignal( self.GetVPanel(), 100 )
        
    def ApplySchemeSettings(self, schemeobj):
        super(HudCaptureTheFlag, self).ApplySchemeSettings(schemeobj)
        
        self.timer.SetBgColor(Color(60, 60, 60, 170))
        self.timer.SetFgColor(Color(255, 255, 255, 255))
        
    def PerformLayout(self):
        super(HudCaptureTheFlag, self).PerformLayout()
        
        self.SetSize( scheme().GetProportionalScaledValueEx( self.GetScheme(), 80 ),
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 30 ) )
        self.SetPos( int(ScreenWidth()/2)-int(self.GetWide()/2), 0 ) 
            
        self.timer.SetSize( self.GetWide(), self.GetTall() )

    def OnTick(self):
        super(HudCaptureTheFlag, self).OnTick()
        
        if self.playercapturing:
             color = playermgr.dbplayers[self.playercapturing].color
             ownertime = (gpGlobals.curtime - self.curstartcapturetime) + self.savedtime
             self.timer.SetText( str(max(0, int(GameRules().CAPTURE_TIME - ownertime))) )
             self.SetBgColor(Color(color[0], color[1], color[2], 170))