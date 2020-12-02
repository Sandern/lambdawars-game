from srcbase import Color, HIDEHUD_STRATEGIC
from vgui import GetClientMode, CHudElement, scheme, AddTickSignal
from vgui.controls import Panel, Label
import playermgr
from utils import ScreenWidth, ScreenHeight
from gamerules import gamerules

class HudTimer(CHudElement, Panel):
    def __init__(self):
        CHudElement.__init__(self, "HudTimer")
        Panel.__init__(self, GetClientMode().GetViewport(), "HudTimer")
        self.SetHiddenBits( HIDEHUD_STRATEGIC ) 
        
        self.SetPaintBackgroundEnabled(True)
        
        self.timer = Label(self, "Timer", "")
        self.timer.MakeReadyForUse()
        self.timer.SetScheme(scheme().LoadSchemeFromFile("resource/ClientScheme.res", "ClientScheme"))
        self.timer.SetPaintBackgroundEnabled(False)
        self.timer.SetPaintBorderEnabled(False)
        self.timer.SetContentAlignment(Label.a_west)
        self.gametime = False
        
        
        AddTickSignal( self.GetVPanel(), 100 )
        
    def ApplySchemeSettings(self, schemeobj):
        super(HudTimer, self).ApplySchemeSettings(schemeobj)
        
        self.timer.SetBgColor(Color(60, 60, 60, 170))
        self.timer.SetFgColor(Color(255, 255, 255, 255))
        
    def PerformLayout(self):
        super(HudTimer, self).PerformLayout()
        
        self.SetSize( scheme().GetProportionalScaledValueEx( self.GetScheme(), 40 ),
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 10 ) )
        self.SetPos( 0, int(ScreenHeight()/1.5) ) #вообще стоило по-другому все это сделать
            
        margintop = scheme().GetProportionalScaledValueEx(self.GetScheme(), 0)
        marginleft = scheme().GetProportionalScaledValueEx(self.GetScheme(), 0)
        self.timer.SetSize(self.GetWide(), self.GetTall())
        self.timer.SetPos(marginleft, margintop)

    def OnTick(self):
        super(HudTimer, self).OnTick()
        self.ShowTimer()
    def ShowTimer(self): 
        if not self.gametime:
            return
        color = (0, 0, 0)
        #self.time = gpGlobals.curtime
        time = self.time
        time1 = ('%02d:%02d:%02d' % (time // 60 // 60 % 24, time // 60 % 60, time % 60))
        self.timer.SetText(time1)
        self.SetBgColor(Color(color[0], color[1], color[2], 170))
    time = 0