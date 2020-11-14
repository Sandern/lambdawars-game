from srcbase import HIDEHUD_STRATEGIC, Color, KeyValues
from vgui import CHudElement, GetClientMode, scheme, XRES, YRES, HudIcons, surface, AddTickSignal, GetAnimationController
from vgui.controls import Panel, Label, AnimationController
from utils import ScreenWidth, ScreenHeight
from core.hud import HudInfo
from core.factions import GetFactionInfo
from core.resources import resources
from entities import C_HL2WarsPlayer
from core.units import unitpopulationcount, GetMaxPopulation
from gameinterface import ConVarRef

# Hud default main parts
from core.hud import AbilityHudInfo

from .warshud import (HudMinimapSection, HudPopulationSection, HudResourceSection, HudAbilitiesSection,
                     HudUnitsSection, HudGroups)
                     
class HudRebelsMinimapSection(HudMinimapSection):
    backgroundtexture = 'hud_rebels_minimap'
    teamcolorbuttontexture = 'hud_rebels_button_toggleteamcolor'
    teamcolorbuttonhovertexture = 'hud_rebels_button_toggleteamcolorhover'
    
class HudRebelsPopulationSection(HudPopulationSection):
    backgroundtexture = 'hud_rebels_population'
    
class HudRebelsResourceSection(HudResourceSection):
    backgroundtexture = 'hud_rebels_resource'

class HudRebelsAbilitiesSection(HudAbilitiesSection):
    backgroundtexture = 'hud_rebels_abilities'
    
class HudRebelsUnitsSection(HudUnitsSection):
    backgroundtexture = 'hud_rebels_units'

class HudRebels(CHudElement, Panel):
    config = {
    
    }

    def __init__(self):
        CHudElement.__init__(self, "HudRebels")
        Panel.__init__(self, None, "HudRebels")
        
        viewport = GetClientMode().GetViewport()
        
        self.SetParent(viewport)
        self.SetHiddenBits(HIDEHUD_STRATEGIC)

        # Create panels
        self.infobox = AbilityHudInfo()
        self.minimapsection = HudRebelsMinimapSection(viewport)
        self.population = HudRebelsPopulationSection(viewport, self.config)
        self.resource = HudRebelsResourceSection(viewport, self.config)
        self.abilities = HudRebelsAbilitiesSection(viewport, self.infobox, self.config)
        self.units = HudRebelsUnitsSection(viewport, self.infobox, self.config)
        self.groups = HudGroups(viewport, self.config)
        
        # Create a list for easy access
        # TODO: Consider removed attributes above?
        self.subpanels = {
            'infobox' : self.infobox, 
            'minimapsection' : self.minimapsection, 
            'population' : self.population, 
            'resource' : self.resource,
            'abilities' : self.abilities,
            'units' : self.units,
            'groups' : self.groups,
        }
        
    def UpdateOnDelete(self):
        # Delete panels that are not our children
        # otherwise they are still around when the new hud is created
        for name, panel in self.subpanels.items():
            if panel:
                panel.DeletePanel()
        self.subpanels = {}
            
    def ApplySchemeSettings(self, scheme_obj):
        super(HudRebels, self).ApplySchemeSettings(scheme_obj)

        self.SetBgColor(Color(0,0,0,0))
        
    def PerformLayout(self):
        super(HudRebels, self).PerformLayout()
        
        self.SetSize(0,0)
        
        # save the screen size and get the aspect ratio
        self.screenwidth, self.screenheight = surface().GetScreenSize()
        self.aspect = self.screenwidth / float(self.screenheight)
        
        # Minimap + Population + resource panel
        # These panels are based on the left side of the screen.
        minimapwide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 158)
        self.minimapsection.SetPos( scheme().GetProportionalScaledValueEx(self.GetScheme(), 0),
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-144+1))
        self.minimapsection.SetSize( minimapwide,
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 144))
        
        self.population.SetPos( minimapwide,
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-41-1))
        self.population.SetSize( scheme().GetProportionalScaledValueEx(self.GetScheme(), 133),
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 41))
                     
        self.resource.SetPos( minimapwide,
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-41-73-2))
        self.resource.SetSize( scheme().GetProportionalScaledValueEx(self.GetScheme(), 85),
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 73))
                     
        # Abilities + units.
        # These panels are based from the right side of the screen
        abilitieswide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 152)
        self.abilities.SetPos(self.screenwidth-abilitieswide,
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-135+1))
        self.abilities.SetSize(abilitieswide,
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 135))

        if self.aspect > 1.7:
            # 16:9
            unitswide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 341)
            self.units.SetPos(self.screenwidth-unitswide-abilitieswide,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-90+1))
            self.units.SetSize( unitswide,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 90))
        elif self.aspect >= 1.5:
            # 16:10
            unitswide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 255)
            self.units.SetPos(self.screenwidth-unitswide-abilitieswide,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-90+1))
            self.units.SetSize( unitswide,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 90))
        else:
            # 4:3 suckers
            unitswide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 195)
            self.units.SetPos(self.screenwidth-unitswide-abilitieswide,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-90+1))
            self.units.SetSize( unitswide,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 90))
                     
        # Groups auto fixes the wide (to scale with the button ratio and number of buttons)
        groupsy = scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-90+1)-int(self.groups.GetTall()*0.6)
        self.groups.SetTall(scheme().GetProportionalScaledValueEx(self.GetScheme(), 30))
        self.groups.SetPos(self.screenwidth-unitswide-abilitieswide, groupsy)
        self.groups.basey = groupsy
        self.groups.hovery = scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-90+1)-int(self.groups.GetTall()*0.9)

        # Info box
        self.infobox.mainhud_tall = scheme().GetProportionalScaledValueEx(self.GetScheme(), 135)
        self.infobox.iswidescreen = (self.aspect >= 1.45)
        self.infobox.PerformLayout()
        
    def SetVisible(self, visible):
        super(HudRebels, self).SetVisible(visible)
        for name, panel in self.subpanels.items():
            if panel and name not in ['infobox']:
                panel.SetVisible(visible)
                
    subpanels = {}
                
class RebelsHudInfo(HudInfo):
    name = 'rebels_hud'
    cls = HudRebels

"""
# Cef based version
from cef import viewport, CefHudPanel

class CefRebelsHud(CefHudPanel):
    name = 'rebels'
    htmlfile = 'ui/viewport/rebels/rebels.html'
    classidentifier = 'viewport/hud/wars/Rebels'
    cssfiles = CefHudPanel.cssfiles + ['rebels/rebels.css']
    
    def GetConfig(self):
        ''' Dictionary passed as config to javascript, used for initializing. '''
        config = super(CefRebelsHud, self).GetConfig()
        config['visible'] = True
        return config

class CefRebelsHudInfo(HudInfo):
    name = 'rebels_hud_cef'
    cefcls = CefRebelsHud
"""
    