from vmath import Vector
from vgui import surface, GetClientMode, CHudElement, CHudElementHelper, scheme, FontDrawType_t
from vgui.controls import Panel
from gameinterface import engine, PlayerInfo
from utils import GetVectorInScreenSpace, ScreenWidth, ScreenHeight
from entities import PlayerResource
from core.units import unitlist
from core.signals import playercontrolunit, playerleftcontrolunit
import playermgr

class HudPlayerNames(CHudElement, Panel):
    def __init__(self):
        CHudElement.__init__(self, "HudPlayerNames")
        Panel.__init__(self, GetClientMode().GetViewport(), "HudPlayerNames")
        #self.SetHiddenBits( HIDEHUD_STRATEGIC ) 
        
        self.SetPaintEnabled(False)
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(False)
        self.SetPaintBackgroundEnabled(False)
        
        schemeobj = scheme().LoadSchemeFromFile("resource/GameLobbyScheme.res", "GameLobbyScheme")
        self.SetScheme(schemeobj)
        
        self.controlledunits = []
        
        playercontrolunit.connect(self.OnPlayerControlUnit)
        playerleftcontrolunit.connect(self.OnPlayerLeftControlUnit)
        
    def UpdateOnDelete(self):
        playercontrolunit.disconnect(self.OnPlayerControlUnit)
        playerleftcontrolunit.disconnect(self.OnPlayerLeftControlUnit)
        
    def PerformLayout(self):
        super().PerformLayout()
        
        self.SetSize(ScreenWidth(), ScreenHeight())
        
    def ApplySchemeSettings(self, schemeobj):
        super().ApplySchemeSettings(schemeobj)
        
        self.hfontsmall = schemeobj.GetFont('FriendsMedium')
        
    def OnPlayerControlUnit(self, player, unit, **kwargs):
        self.controlledunits.append(unit)
        self.SetPaintEnabled(True)
        
    def OnPlayerLeftControlUnit(self, player, unit, **kwargs):
        self.controlledunits.remove(unit)
        if not self.controlledunits:
            self.SetPaintEnabled(False)
        
    def Paint(self):
        for unit in self.controlledunits:
            # Valid unit? Unit controlled by player?
            if not unit or unit.controlledbyplayer is None or unit.IsDormant():
                continue

            # In screen?
            maxs = unit.WorldAlignMaxs()
            result, temp_x, temp_y = GetVectorInScreenSpace(unit.GetAbsOrigin()+Vector(0,0,maxs.z+24.0)) 
            if not result:
                continue

            # Get player info 
            info = PlayerInfo()
            if not engine.GetPlayerInfo(unit.controlledbyplayer, info):
                continue  
                
            ownernumber = PlayerResource().GetOwnerNumber(unit.controlledbyplayer)
                    
            # Draw name
            wide, tall = surface().GetTextSize(self.hfontsmall, info.name)
            surface().DrawSetTextFont(self.hfontsmall)
            surface().DrawSetTextColor(playermgr.dbplayers[ownernumber].color)
            surface().DrawSetTextPos(int(temp_x-wide/2.0), temp_y)
            surface().DrawUnicodeString(info.name, FontDrawType_t.FONT_DRAW_DEFAULT)
