from srcbase import HIDEHUD_STRATEGIC, Color
from vgui import CHudElement, GetClientMode, scheme, XRES, YRES, HudIcons, surface, AddTickSignal, GetAnimationController
from vgui.controls import Panel
from core.hud import HudInfo

# Hud default main parts
from core.hud import AbilityHudInfo

from .warshud import (HudMinimapSection, HudPopulationAndResourceSection, HudAbilitiesSection,
                     HudUnitsSection, HudGroups)

class HudCombineMinimapSection(HudMinimapSection):
    backgroundtexture = 'hud_combine_minimap'
    teamcolorbuttontexture = 'hud_combine_button_toggleteamcolor'
    teamcolorbuttonhovertexture = 'hud_combine_button_toggleteamcolorhover'
    teamcolorrelposx = 0.82
    teamcolorrelposy = 0.33
    minimapxpos = 0.05
    minimapypos = 0.1658
    minimapwide = 0.7682
    minimaptall = 0.7682
    
class HudRebelsPopulationAndResourceSection(HudPopulationAndResourceSection):
    backgroundtexture = 'hud_combine_populationandresource'
    
    margintop = 14
    marginleft = 20
    spacing = 17
    
class HudCombineAbilitiesSection(HudAbilitiesSection):
    backgroundtexture = 'hud_combine_abilities'
    topmargin = 10
    bottommargin = 10
    leftmargin = 15
    rightmargin = 5
    
class HudCombineUnitsSection(HudUnitsSection):
    backgroundtexture = 'hud_combine_units'
    topmargin = 28
    bottommargin = 10
    leftmargin = 8
    rightmargin = 28
    
class HudCombine(CHudElement, Panel):
    config = {
        'ability_button_enabled' : 'hud_combine_button_enabled',
        'ability_button_disabled' : 'hud_combine_button_disabled',
        'ability_button_pressed' : 'hud_combine_button_pressed',
        'ability_button_hover' : 'hud_combine_button_hover',
        'ability_button_autocastoverlay' : 'hud_combine_button_autocastoverlay',
        'ability_button_autocastoverlay_off' : 'hud_combine_button_autocastoverlay_off',
        
        'units_button_enabled' : 'hud_combine_unitbutton_enabled',
        'units_button_pressed' : 'hud_combine_unitbutton_pressed',
        'units_button_hover' : 'hud_combine_unitbutton_hover',
        
        'groups_button' : 'hud_combine_groupbutton',
    }

    def __init__(self):
        CHudElement.__init__(self, "HudCombine")
        Panel.__init__(self, None, "HudCombine")
        
        viewport = GetClientMode().GetViewport()
        
        self.SetParent(viewport)
        self.SetHiddenBits(HIDEHUD_STRATEGIC)

        # Create panels
        self.infobox = AbilityHudInfo()
        self.minimapsection = HudCombineMinimapSection(viewport)
        self.populationandresource = HudRebelsPopulationAndResourceSection(viewport, self.config)
        self.abilities = HudCombineAbilitiesSection(viewport, self.infobox, self.config)
        self.units = HudCombineUnitsSection(viewport, self.infobox, self.config)
        self.groups = HudGroups(viewport, self.config)
        
        self.groups.buttontexture = 'hud_combine_groupbutton'
        
        # Create a list for easy access
        # TODO: Consider removed attributes above?
        self.subpanels = {
            'infobox' : self.infobox, 
            'minimapsection' : self.minimapsection, 
            'populationandresource' : self.populationandresource,
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
        super(HudCombine, self).ApplySchemeSettings(scheme_obj)

        self.SetBgColor(Color(0,0,0,0))
        
    def PerformLayout(self):
        super(HudCombine, self).PerformLayout()
        
        self.SetSize(0,0)
        
        # save the screen size and get the aspect ratio
        self.screenwidth, self.screenheight = surface().GetScreenSize()
        self.aspect = self.screenwidth / float(self.screenheight)

        # Minimap + Population + resource panel
        # These panels are based on the left side of the screen.
        minimapwide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 158)
        self.minimapsection.SetPos( scheme().GetProportionalScaledValueEx(self.GetScheme(), 0),
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-151+1))
        self.minimapsection.SetSize( minimapwide,
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 151))
        
        self.populationandresource.SetPos( minimapwide - scheme().GetProportionalScaledValueEx(self.GetScheme(), 10),
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-110-1))
        self.populationandresource.SetSize( scheme().GetProportionalScaledValueEx(self.GetScheme(), 107),
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 110))

        # Abilities + units.
        # These panels are based from the right side of the screen
        abilitieswide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 159)
        abilitiesoverlap = scheme().GetProportionalScaledValueEx(self.GetScheme(), 9)
        self.abilities.SetPos(self.screenwidth-abilitieswide,
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-141+1))
        self.abilities.SetSize(abilitieswide,
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 141))

        if self.aspect > 1.7:
            # 16:9
            unitswide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 311)
            self.units.SetPos(self.screenwidth-unitswide-abilitieswide+abilitiesoverlap,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-110+1))
            self.units.SetSize( unitswide,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 110))
        elif self.aspect >= 1.5:
            self.populationandresource.SetZPos(-20)
            self.units.SetZPos(-1)
            
            abilitiesoverlap += scheme().GetProportionalScaledValueEx(self.GetScheme(), 9)
            # 16:10
            unitswide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 311)
            self.units.SetPos(self.screenwidth-unitswide-abilitieswide+abilitiesoverlap,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-110+1))
            self.units.SetSize( unitswide,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 110))
        elif self.aspect == 1.25:
            unitswide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 200)
            self.units.SetPos(self.screenwidth-unitswide-abilitieswide+abilitiesoverlap,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-94+1))
            self.units.SetSize( unitswide,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 94))
            
            self.units.background = HudIcons().GetIcon('hud_combine_units_small')
        else:
            # 4:3 suckers
            unitswide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 235)
            self.units.SetPos(self.screenwidth-unitswide-abilitieswide+abilitiesoverlap,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-94+1))
            self.units.SetSize( unitswide,
                         scheme().GetProportionalScaledValueEx(self.GetScheme(), 94))
                         
            # Override background of units for smaller version
            self.units.background = HudIcons().GetIcon('hud_combine_units_small')
                     
        # Groups auto fixes the wide (to scale with the button ratio and number of buttons)
        groupsy = scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-94+1)-int(self.groups.GetTall()*0.6)
        self.groups.SetTall(scheme().GetProportionalScaledValueEx(self.GetScheme(), 30))
        self.groups.SetPos(self.screenwidth-unitswide-abilitieswide+abilitiesoverlap, groupsy)
        self.groups.basey = groupsy
        self.groups.hovery = scheme().GetProportionalScaledValueEx(self.GetScheme(), 480-94+1)-int(self.groups.GetTall()*0.9)
                     
        # Info box
        self.infobox.mainhud_tall = scheme().GetProportionalScaledValueEx(self.GetScheme(), 135)
        self.infobox.iswidescreen = (self.aspect >= 1.45)
        self.infobox.PerformLayout()
        
    def SetVisible(self, visible):
        super(HudCombine, self).SetVisible(visible)
        for name, panel in self.subpanels.items():
            if panel and name not in ['infobox']:
                panel.SetVisible(visible)
                
    subpanels = {}
        
class CombineHudInfo(HudInfo):
    name = 'combine_hud'
    cls = HudCombine