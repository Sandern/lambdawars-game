"""HUD overlays for displaying health and control state of the player's unit.

Adds panels that react to control events and render health bars or other
status information for the unit currently being directly controlled by the
player.
"""
from srcbase import Color, HIDEHUD_UNIT
from vgui import CHudElement, scheme, GetClientMode, CHudElementHelper, surface, FontDrawType_t
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

    def ApplySchemeSettings(self, schemeobj):
        super().ApplySchemeSettings(schemeobj)
        self.hfontsmall = schemeobj.GetFont("DefaultSmall")

    def PerformLayout(self):
        super().PerformLayout()
        schemeobj = scheme()
        width = schemeobj.GetProportionalScaledValueEx(self.GetScheme(), 200)
        height = schemeobj.GetProportionalScaledValueEx(self.GetScheme(), 32)
        margin = schemeobj.GetProportionalScaledValueEx(self.GetScheme(), 20)
        self.SetSize(width, height)
        self.SetPos(ScreenWidth() - width - margin, ScreenHeight() - height - margin)
                
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
        player.ClearSelection(False)
        engine.ServerCommand("player_clearselection")
        player.MakeSelection(self.selections)
        unit.UpdateVisibility()
        self.controlledunit = None
        self.selections = None
            
    def Paint(self):
        super().Paint()

        unit = self.controlledunit
        if not unit or not getattr(self, 'hfontsmall', None):
            return

        width, tall = self.GetSize()
        bar = scheme().GetProportionalScaledValueEx(self.GetScheme(), 16)
        s = surface()

        # Draw both hp and energy bars
        # TODO: maybe in a better way?
        maxhealth = max(1, max(unit.maxhealth, unit.health))
        healthweight = float(unit.health) / maxhealth
        s.DrawSetColor(Color(
            255 - int(healthweight * 255), 
            int(healthweight * 168), 
            int(healthweight * 60), 
            255 - int(healthweight * 128)
            ))
        s.DrawFilledRect(0, 0, int(healthweight * width), bar)
        s.DrawSetColor(Color(255, 255, 255, 255))
        s.DrawOutlinedRect(0, 0, width, bar)
        self.DrawBarText('%d / %d' % (unit.health, unit.maxhealth), 0, bar, width)

        if unit.maxenergy > 0:
            y = bar + 4
            maxenergy = max(1, max(unit.maxenergy, unit.energy))
            energyweight = float(unit.energy) / maxenergy
            s.DrawSetColor(Color(
                0, 
                int(energyweight * 80), 
                int(energyweight * 255), 
                255 - int(energyweight * 64)
                ))
            s.DrawFilledRect(0, y, int(energyweight * width), y + bar - 2)
            s.DrawSetColor(Color(255, 255, 255, 255))
            s.DrawOutlinedRect(0, y, width, y + bar - 2)
            self.DrawBarText('%d / %d' % (unit.energy, unit.maxenergy), y, bar - 2, width)

    def DrawBarText(self, text, y, bar, width):
        s = surface()
        wide, texttall = s.GetTextSize(self.hfontsmall, text)
        s.DrawSetTextFont(self.hfontsmall)
        s.DrawSetTextColor(Color(255, 255, 255, 255))
        s.DrawSetTextPos(int((width - wide) / 2), int(y + (bar - texttall) / 2))
        s.DrawUnicodeString(text, FontDrawType_t.FONT_DRAW_DEFAULT) 

hudunitdisplayhealth = CHudElementHelper( HudUnitDisplayHealth() )