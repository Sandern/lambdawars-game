from srcbase import HIDEHUD_STRATEGIC
from vgui import surface, GetClientMode, CHudElement, CHudElementHelper, scheme, FontDrawType_t
from vgui.controls import Panel
from utils import GetVectorInScreenSpace, ScreenWidth, ScreenHeight
from core.resources import GetResourceInfo


class HudResourceIndicator(CHudElement, Panel):
    def __init__(self):
        CHudElement.__init__(self, "HudResourceIndicator")
        Panel.__init__(self, GetClientMode().GetViewport(), "HudResourceIndicator")
        self.SetHiddenBits(HIDEHUD_STRATEGIC) 
        
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(False)
        self.SetPaintBackgroundEnabled(False)
        
        schemeobj = scheme().LoadSchemeFromFile("resource/GameLobbyScheme.res", "GameLobbyScheme")
        self.SetScheme(schemeobj)
        
        self.displaying = []
        
    def LevelInit(self):
        # Reset
        self.displaying = []
        
    def ApplySchemeSettings(self, schemeobj):
        super().ApplySchemeSettings(schemeobj)
        
        self.hfontsmall = schemeobj.GetFont( "HeadlineLarge" )
        self.moverely = scheme().GetProportionalScaledValueEx(self.GetScheme(), 22)
        self.iconsize = scheme().GetProportionalScaledValueEx(self.GetScheme(), 10)
        
    def PerformLayout(self):
        super().PerformLayout()
        
        self.SetSize(ScreenWidth(), ScreenHeight())
            
    def Add(self, origin, num=1, resourcetype=None):
        resinfo = GetResourceInfo(resourcetype)
        self.displaying.append( (gpGlobals.curtime, origin, num, resinfo) )

    def Paint(self):
        if not self.displaying:
            return
        for k in list(self.displaying):
            lifetime = gpGlobals.curtime - k[0]
            weight = max(0.0, 1.0 - lifetime/self.LIFE_TIME)
            
            result, x, y = GetVectorInScreenSpace(k[1])
            
            y = int(y-(1.0-weight)*self.moverely)
            
            alpha = int(weight*255)
            
            resinfo = k[3]
            if resinfo:
                icon = resinfo.icon
                if icon:
                    icon.DoPaint(x, y, self.iconsize, self.iconsize, 0, 255 - alpha)
                    x += self.iconsize
        
            s = surface()
            s.DrawSetTextFont(self.hfontsmall)
            s.DrawSetTextColor(255, 255, 255, alpha)
            s.DrawSetTextPos(x, y)
            s.DrawUnicodeString('%s' % (k[2]), FontDrawType_t.FONT_DRAW_DEFAULT)
            
            if lifetime > self.LIFE_TIME:
                self.displaying.remove(k)
                
    LIFE_TIME = 2.5

hudresourceindicator = CHudElementHelper(HudResourceIndicator())
