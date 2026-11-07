"""HUD overlays for displaying health and control state of the player's unit.

Adds panels that react to control events and render health bars or other
status information for the unit currently being directly controlled by the
player.
"""
from srcbase import Color, HIDEHUD_UNIT
from vgui import CHudElement, scheme, GetClientMode, CHudElementHelper, surface
from vgui.controls import Panel
from utils import UTIL_EntitiesInSphere, ScreenWidth, ScreenHeight
from entities import C_HL2WarsPlayer
from core.signals import playercontrolunit, playerleftcontrolunit
from gameinterface import engine
from input import input


class HudUnitDisplayHealth(CHudElement, Panel):
    """Displays a health bar for the unit the player has direct control over.

    Hooks into control signals so the overlay is only visible while the
    player is in direct-control mode, and renders a proportional health bar
    anchored to the bottom of the screen.
    """
    def __init__(self):
        CHudElement.__init__(self, "HudUnitDisplayHealth")
        Panel.__init__(self, GetClientMode().GetViewport(), "HudUnitDisplayHealth")
        self.SetHiddenBits( HIDEHUD_UNIT ) 
        
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(False)
        self.SetPaintEnabled(False)
        self.SetPaintBackgroundEnabled(False)
        
        playercontrolunit.connect(self.OnPlayerControlUnit)
        playerleftcontrolunit.connect(self.OnPlayerLeftControlUnit)

        self.selections = None
        
    def UpdateOnDelete(self):
        playercontrolunit.disconnect(self.OnPlayerControlUnit)
        playerleftcontrolunit.disconnect(self.OnPlayerLeftControlUnit)
        
    def PerformLayout(self):
        super().PerformLayout()
        
        self.SetSize( scheme().GetProportionalScaledValueEx( self.GetScheme(), 200 ),
                scheme().GetProportionalScaledValueEx( self.GetScheme(), 30 ) )
        self.SetPos( scheme().GetProportionalScaledValueEx( self.GetScheme(), 20 ),
                scheme().GetProportionalScaledValueEx( self.GetScheme(), 420 ) )
                
    def OnPlayerControlUnit(self, player, unit, **kwargs):
        if player != C_HL2WarsPlayer.GetLocalHL2WarsPlayer():
            return
        self.SetPaintEnabled(True)
        self.selections = list(player.GetSelection())
        player.ClearSelection(False)
        engine.ServerCommand("player_clearselection")
        player.MakeSelection([unit])
        # calling this method because otherwise we won't see our unit in the third person view
        input().CAM_ToThirdPerson()
        input().CAM_ToThirdPersonShoulder()
        unit.UpdateVisibility()
        self.controlledunit = unit
        
    def OnPlayerLeftControlUnit(self, player, unit, **kwargs):
        if player != C_HL2WarsPlayer.GetLocalHL2WarsPlayer():
            return
        self.SetPaintEnabled(False)
        input().CAM_ToThirdPerson()
        player.MakeSelection(self.selections)
        unit.UpdateVisibility()
        self.controlledunit = None
        self.selections = None
            
    def Paint(self):
        super().Paint()

        unit = self.controlledunit
        if not unit:
            return

        width, tall = self.GetSize()
        # bar value template
        bar = scheme().GetProportionalScaledValueEx(self.GetScheme(), 30)
        left = int(w_health*width)

        # Draw both hp and energy bars
        # TODO: maybe in a better way?
        maxhealth = max(1, max(unit.maxhealth, unit.health))
        healthweight = float(unit.health) / maxhealth
        surface().DrawSetColor(Color(255 - int(healthweight * 255), int(healthweight * 255), 0, 255))
        surface().DrawFilledRect(0, 0, int(healthweight * width), bar)
        surface().DrawSetColor(Color(255, 255, 255, 255))
        surface().DrawOutlinedRect(0, 0, width, bar)
        
        if unit.maxenergy > 0:
            y = bar + 4
            energyweight = float(unit.energy) / unit.maxenergy
            surface().DrawSetColor(Color(0, 80, 255, 255))
            surface().DrawFilledRect(0, y, int(energyweight * width), y + bar)
            surface().DrawSetColor(Color(255, 255, 255, 255))
            surface().DrawOutlinedRect(0, y, width, y + bar)      

hudunitdisplayhealth = CHudElementHelper( HudUnitDisplayHealth() )