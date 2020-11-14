from srcbase import HIDEHUD_STRATEGIC, Color, KeyValues
from vgui import CHudElement, GetClientMode, scheme, XRES, YRES, HudIcons, surface, AddTickSignal, GetAnimationController
from vgui.controls import Panel, Label, AnimationController, ImagePanel
from utils import ScreenWidth, ScreenHeight
from core.factions import GetFactionInfo
from core.resources import resources, resourcecaps, GetResourceInfo
from entities import C_HL2WarsPlayer
from core.units import unitpopulationcount, GetMaxPopulation
from gameinterface import ConVarRef
from collections import defaultdict
from sound import soundengine

# Hud default main parts
from core.hud import (BaseHudAbilities, HudUnitsContainer, AbilityButton,
                      AbilityHudInfo, BaseHudMinimap, BaseHudUnits, BaseHudGroups)
                      
cl_teamcolor_relationbased = ConVarRef('cl_teamcolor_relationbased')

class BackgroundPanel(Panel):
    def __init__(self, parent, panelname):
        super(BackgroundPanel, self).__init__(parent, panelname)
        
        self.SetPaintBackgroundEnabled(True)
        self.background = HudIcons().GetIcon(self.backgroundtexture)

    def PaintBackground(self):
        if self.background:
            w, h = self.GetSize()
            self.background.DrawSelf(0, 0, w, h, self.drawcolor)
            
    background = None
    backgroundtexture = None
    drawcolor = Color(255, 255, 255, 255)
    
class TopPanel(Panel):
    def __init__(self, parent, panelname):
        super(TopPanel, self).__init__(parent, panelname)

        self.SetPaintBackgroundEnabled(False)
        
    def ApplySchemeSettings(self, schemeobj):
        super(TopPanel, self).ApplySchemeSettings(schemeobj)
        
        self.background = HudIcons().GetIcon(self.backgroundtexture)

    def Paint(self):
        if self.background:
            w, h = self.GetSize()
            self.background.DrawSelf(0, 0, w, h, self.drawcolor)
            
    def OnMouseReleased(self, code):
        # let parent deal with it
        self.CallParentFunction(KeyValues("MouseReleased", "code", code))
        
    def OnMousePressed(self, code):
        # let parent deal with it
        self.CallParentFunction(KeyValues("MousePressed", "code", code))
        
    def OnMouseDoublePressed(self, code):
        self.CallParentFunction(KeyValues("MouseDoublePressed", "code", code))
        
    background = None
    backgroundtexture = None
    drawcolor = Color(255, 255, 255, 255)
    
class HudMinimapSection(BackgroundPanel):
    def __init__(self, parent):
        super(HudMinimapSection, self).__init__(parent, 'HudMinimapSection')
        
        self.SetProportional(True)
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(False)
        
        self.minimap = BaseHudMinimap(parent)
        
        self.teamcolorbutton = AbilityButton(parent, 'teamcolortoggle')
        self.teamcolorbutton.SetAllImages(HudIcons().GetIcon(self.teamcolorbuttontexture), Color(255, 255, 255, 255))
        self.teamcolorbutton.SetImage(self.teamcolorbutton.BUTTON_ENABLED_MOUSE_OVER, HudIcons().GetIcon(self.teamcolorbuttonhovertexture), Color(255, 255, 255, 255))
        self.teamcolorbutton.SetCommand('teamcolortoggle')
        self.teamcolorbutton.AddActionSignalTarget(self)
        self.teamcolorbutton.SetMouseInputEnabled(True)
        self.teamcolorbutton.SetVisible(True)
        self.teamcolorbutton.SetZPos(10)
        self.teamcolorbutton.SetEnabled(True)
        
    def SetVisible(self, visible):
        super(HudMinimapSection, self).SetVisible(visible)
        if self.minimap:
            self.minimap.SetVisible(visible)
        if self.teamcolorbutton:
            self.teamcolorbutton.SetVisible(visible)
            
    def UpdateOnDelete(self):
        if self.minimap:
            self.minimap.DeletePanel()
            self.minimap = None
        if self.teamcolorbutton:
            self.teamcolorbutton.DeletePanel()
            self.teamcolorbutton = None
        
    def PerformLayout(self):
        super(HudMinimapSection, self).PerformLayout()
        
        x, y = self.GetPos()
        self.minimap.SetPos(x+int(self.minimapxpos*self.GetWide()), y+int(self.minimapypos*self.GetTall()))
        self.minimap.SetSize(int(self.minimapwide*self.GetWide()), int(self.minimaptall*self.GetTall()))

        wide, tall = self.GetSize()
        self.teamcolorbutton.SetPos(x+int(wide*self.teamcolorrelposx), y+int(tall*self.teamcolorrelposy))
        self.teamcolorbutton.SetSize(int(wide*0.1), int(tall*0.1))
        
    def OnCommand(self, command):
        if command == 'teamcolortoggle':
            cl_teamcolor_relationbased.SetValue(not cl_teamcolor_relationbased.GetBool())
            return True
        return super(HudMinimapSection, self).OnCommand(command)
        
    backgroundtexture = 'hud_rebels_minimap'
    teamcolorbuttontexture = 'hud_rebels_button_toggleteamcolor'
    teamcolorbuttonhovertexture = 'hud_rebels_button_toggleteamcolorhover'
    teamcolorrelposx = 0.85
    teamcolorrelposy = 0.15
    minimapxpos = 0.0693069307
    minimapypos = 0.0891304348
    minimapwide = 0.782178218
    minimaptall = 0.852173913
    
class HudPopulationSection(BackgroundPanel):
    def __init__(self, parent, config):
        super(HudPopulationSection, self).__init__(parent, 'HudPopulationSection')
        
        self.amountunits = Label(self,"UnitsAmount","")
        self.amountunits.MakeReadyForUse()
        self.amountunits.SetScheme(scheme().LoadSchemeFromFile("resource/ClientScheme.res", "ClientScheme"))
        self.amountunits.SetPaintBackgroundEnabled(False)
        self.amountunits.SetPaintBorderEnabled(False)
        self.amountunits.SetContentAlignment(Label.a_west)

        AddTickSignal(self.GetVPanel(), 250)
        
    def PerformLayout(self):
        super(HudPopulationSection, self).PerformLayout()
        
        margintop = scheme().GetProportionalScaledValueEx(self.GetScheme(), 10)
        marginleft = scheme().GetProportionalScaledValueEx(self.GetScheme(), 38)
        self.amountunits.SetSize(scheme().GetProportionalScaledValueEx(self.GetScheme(), 50), 
            scheme().GetProportionalScaledValueEx(self.GetScheme(), 20))
        self.amountunits.SetPos(marginleft, margintop)
                
    def OnTick(self):
        super(HudPopulationSection, self).OnTick()
        
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
        # update amount of units
        ownernumber = player.GetOwnerNumber()
        pop = unitpopulationcount[ownernumber]
        maxpop = GetMaxPopulation(ownernumber)
        self.amountunits.SetText('%s / %s' % (pop, maxpop))
        if pop > maxpop:
            self.amountunits.SetFgColor(Color(255, 0, 0, 255))
        else:
            self.amountunits.SetFgColor(Color(255, 255, 255, 255))
            
    backgroundtexture = 'hud_rebels_population'
    
# rebels
class HudResourceSection(BackgroundPanel):
    def __init__(self, parent, config):
        super(HudResourceSection, self).__init__(parent, 'HudResourceSection')
        
        self.icons = []
        self.resources = []
        
        self.lastresources = defaultdict(lambda: 0)
        self.convergespeeds = defaultdict(lambda: 30)
        
        for i in range(0, 3):
            l = Label(self, 'ResourcesAmount%d' % (i), '')
            l.MakeReadyForUse()
            l.SetScheme(scheme().LoadSchemeFromFile("resource/ClientScheme.res", "ClientScheme"))
            l.SetPaintBackgroundEnabled(False)
            l.SetPaintBorderEnabled(False)
            self.resources.append(l)
            
            icon = ImagePanel(self, 'ResourceIcon%d' % (i))
            icon.scaleimage = True
            self.icons.append(icon)
        
        AddTickSignal(self.GetVPanel(), 50)
        
    def ApplySchemeSettings(self, scheme_obj):
        super(HudResourceSection, self).ApplySchemeSettings(scheme_obj)

        for l in self.resources:
            l.SetBgColor(Color(0,0,0,0))
            l.SetFgColor(Color(225,225,225,255))
            l.SetContentAlignment(Label.a_west)
        
    def PerformLayout(self):
        super(HudResourceSection, self).PerformLayout()
        
        spacing = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.spacing)
        margintop = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.margintop)
        marginleft = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.marginleft)
        
        sizey = scheme().GetProportionalScaledValueEx(self.GetScheme(), 20)
        sizeyicon = scheme().GetProportionalScaledValueEx(self.GetScheme(), 15)
        
        for i, l in enumerate(self.resources):
            x = marginleft
        
            icon = self.icons[i]
            icon.SetSize(sizeyicon, sizeyicon)
            icon.SetPos(x, margintop + scheme().GetProportionalScaledValueEx(self.GetScheme(), 2) + spacing*i)
        
            l.SetSize(scheme().GetProportionalScaledValueEx(self.GetScheme(), 50), sizey)
            l.SetPos(x + sizey, margintop + spacing*i)

    def OnTick(self):
        super(HudResourceSection, self).OnTick()
        
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return

        faction = player.GetFaction()
        info = GetFactionInfo(faction)
        if not info or not info.resources:
            return

        # update amount of resources
        for i, r in enumerate(info.resources):
            if i >= 3:
                break
                
            resource = info.resources[i]
            
            resinfo = GetResourceInfo(resource)
            if not resinfo:
                continue
            
            icon = self.icons[i]
            if resinfo.icon:
                icon.SetImage(resinfo.icon)
                
            oldresource = self.lastresources[resource]
            targetresource = resources[player.GetOwnerNumber()][resource]
            
            if oldresource == targetresource:
                self.convergespeeds[resource] = 30 # Reset
                newresource = targetresource
            else:
                convergespeed = self.convergespeeds[resource]
                
                if oldresource < targetresource:
                    newresource = min(oldresource + (0.05 * convergespeed), targetresource)
                    if(resource !="requisition"):
                        if convergespeed > 34:
                            # play tick sound
                            soundengine.EmitAmbientSound('misc\hud_resource_tick.wav', 0.8)       
                else:
                    newresource = max(oldresource - (0.05 * convergespeed), targetresource)
                    if convergespeed > 34:
                        # play tick sound
                        soundengine.EmitAmbientSound('misc\hud_resource_tick.wav', 0.8)          
                            
                self.convergespeeds[resource] *= (1.05)
                    
            newresource = int(newresource)
            self.lastresources[resource] = newresource
            
            text = '%s' % (newresource)

            if resinfo.iscapped:
                text += ' / %s' % (resourcecaps[player.GetOwnerNumber()][resource])
            if self.resources[i].GetText() != text:
                self.resources[i].SetText(text)
        
    backgroundtexture = 'hud_rebels_resource'
    margintop = 5
    marginleft = 10
    spacing = 20
    
# combine   
class HudPopulationAndResourceSection(BackgroundPanel):
    def __init__(self, parent, config):
        super(HudPopulationAndResourceSection, self).__init__(parent, 'HudPopulationAndResourceSection')
        
        self.amountunits = Label(self,"UnitsAmount","")
        self.amountunits.MakeReadyForUse()
        self.amountunits.SetScheme(scheme().LoadSchemeFromFile("resource/ClientScheme.res", "ClientScheme"))
        self.amountunits.SetPaintBackgroundEnabled(False)
        self.amountunits.SetPaintBorderEnabled(False)
        self.amountunits.SetContentAlignment(Label.a_west)
        
        self.icons = []
        self.resources = []
        
        self.lastresources = defaultdict(lambda: 0)
        self.convergespeeds = defaultdict(lambda: 30)
        
        for i in range(0, 3):
            l = Label(self, 'ResourcesAmount%d' % (i), '')
            l.MakeReadyForUse()
            l.SetScheme(scheme().LoadSchemeFromFile("resource/ClientScheme.res", "ClientScheme"))
            l.SetPaintBackgroundEnabled(False)
            l.SetPaintBorderEnabled(False)
            self.resources.append(l)
            
            icon = ImagePanel(self, 'ResourceIcon%d' % (i))
            icon.scaleimage = True
            self.icons.append(icon)
        
        AddTickSignal(self.GetVPanel(), 50)
            
    def ApplySchemeSettings(self, scheme_obj):
        super(HudPopulationAndResourceSection, self).ApplySchemeSettings(scheme_obj)

        for l in self.resources:
            l.SetBgColor(Color(0,0,0,0))
            l.SetFgColor(Color(255,255,255,255))
            l.SetContentAlignment(Label.a_west)
        
    def PerformLayout(self):
        super(HudPopulationAndResourceSection, self).PerformLayout()
        
        sizex, sizey = self.GetSize()
        
        margintop = scheme().GetProportionalScaledValueEx(self.GetScheme(), 10)
        marginleft = scheme().GetProportionalScaledValueEx(self.GetScheme(), 45)
        self.amountunits.SetSize(scheme().GetProportionalScaledValueEx(self.GetScheme(), 50), 
            scheme().GetProportionalScaledValueEx(self.GetScheme(), 20))
        self.amountunits.SetPos(marginleft, int(sizey * 0.675))
        
        spacing = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.spacing)
        margintop = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.margintop)
        marginleft = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.marginleft)
        
        sizey = scheme().GetProportionalScaledValueEx(self.GetScheme(), 15)
        sizeyicon = scheme().GetProportionalScaledValueEx(self.GetScheme(), 15)
        #iconshrink = scheme().GetProportionalScaledValueEx(self.GetScheme(), 2)
        
        for i, l in enumerate(self.resources):
            x = marginleft
            if i == 2:
                x += scheme().GetProportionalScaledValueEx(self.GetScheme(), 5)
        
            icon = self.icons[i]
            icon.SetSize(sizeyicon, sizeyicon)
            icon.SetPos(x, margintop + scheme().GetProportionalScaledValueEx(self.GetScheme(), 2) + spacing*i)
        
            l.SetSize(scheme().GetProportionalScaledValueEx(self.GetScheme(), 50), sizey)
            l.SetPos(x + sizey, margintop + spacing*i)
        
    def OnTick(self):
        super(HudPopulationAndResourceSection, self).OnTick()
        
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return

        faction = player.GetFaction()
        info = GetFactionInfo(faction)
        if not info or not info.resources:
            return
            
        # update amount of units
        ownernumber = player.GetOwnerNumber()
        pop = unitpopulationcount[ownernumber]
        maxpop = GetMaxPopulation(ownernumber)
        self.amountunits.SetText('%s/%s' % (pop, maxpop))
        if pop > maxpop:
            self.amountunits.SetFgColor(Color(255, 0, 0, 255))
        else:
            self.amountunits.SetFgColor(Color(255, 255, 255, 255))

        # update amount of resources
        for i, r in enumerate(info.resources):
            if i >= 3:
                break
                
            resource = info.resources[i]
            icon = self.icons[i]
            
            resinfo = GetResourceInfo(resource)
            if not resinfo:
                continue
            
            icon = self.icons[i]
            if resinfo.icon:
                icon.SetImage(resinfo.icon)
                
            oldresource = self.lastresources[resource]
            targetresource = resources[player.GetOwnerNumber()][resource]
            
            if oldresource == targetresource:
                self.convergespeeds[resource] = 30 # Reset
                newresource = targetresource
            else:
                convergespeed = self.convergespeeds[resource]
                
                if oldresource < targetresource:
                    newresource = min(oldresource + (0.05 * convergespeed), targetresource)
                    if(resource !="requisition"):
                        if convergespeed > 34:
                            # play tick sound
                            soundengine.EmitAmbientSound('misc\hud_resource_tick.wav', 0.8)
                else:
                    newresource = max(oldresource - (0.05 * convergespeed), targetresource)
                    if convergespeed > 34:
                        # play tick sound
                        soundengine.EmitAmbientSound('misc\hud_resource_tick.wav', 0.8)          
                    
                self.convergespeeds[resource] *= (1.05)

            newresource = int(newresource)
            self.lastresources[resource] = newresource
                
            text = '%s' % (newresource)
            if resinfo.iscapped:
                text += ' / %s' % (resourcecaps[player.GetOwnerNumber()][resource])
            
            if self.resources[i].GetText() != text:
                self.resources[i].SetText(text)

    backgroundtexture = 'hud_rebels_populationandresource'
    
    margintop = 15
    marginleft = 10
    spacing = 22
    
class HudAbilitiesSection(BackgroundPanel):
    def __init__(self, parent, infobox, config):
        super(HudAbilitiesSection, self).__init__(parent, 'HudAbilitiesSection')
        
        self.SetProportional(True)
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(True)
        
        self.abilitypanel = BaseHudAbilities(self, infobox, config)
        self.abilitypanel.marginbottom = 2
        self.abilitypanel.margintop = 3
        
    def UpdateOnDelete(self):
        self.abilitypanel.DeletePanel()
        
    def PerformLayout(self):
        super(HudAbilitiesSection, self).PerformLayout()
        
        x, y = self.GetPos()
        topmargin = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.topmargin)
        botmargin = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.bottommargin)
        leftmargin = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.leftmargin)
        rightmargin = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.rightmargin)
        self.abilitypanel.SetPos(leftmargin, topmargin)
        self.abilitypanel.SetSize(self.GetWide()-leftmargin-rightmargin, self.GetTall()-topmargin-botmargin)

    backgroundtexture = 'hud_rebels_abilities'
    
    topmargin = 5
    bottommargin = 5
    leftmargin = 5
    rightmargin = 5
    
class HudUnits(BaseHudUnits):
    scale_values = {
        20 : (10, 2),
        60 : (15, 3),
        80 : (20, 4)
    }
    unitbuttonhpbounds = (0.043, 0.96, 0.87, 0.96) # xmin, xmax, ymin, ymax
    
class HudUnitsSection(BackgroundPanel):
    def __init__(self, parent, infopanel, config):
        super(HudUnitsSection, self).__init__(parent, 'HudUnitsSection')
        
        self.SetProportional(True)
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(True)
        
        self.unitpanel = HudUnitsContainer(self, infopanel, config)
        self.unitpanel.defaultunitpanelclass = HudUnits
        
    def UpdateOnDelete(self):
        self.unitpanel.DeletePanel()
        
    def PerformLayout(self):
        super(HudUnitsSection, self).PerformLayout()
        
        x, y = self.GetPos()
        topmargin = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.topmargin)
        botmargin = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.bottommargin)
        leftmargin = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.leftmargin)
        rightmargin = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.rightmargin)
        
        leftrightmargin = scheme().GetProportionalScaledValueEx(self.GetScheme(), 5)
        self.unitpanel.SetPos(leftmargin, topmargin)
        self.unitpanel.SetSize(self.GetWide()-leftmargin-rightmargin, self.GetTall()-topmargin-botmargin)

    backgroundtexture = 'hud_rebels_units'
    
    topmargin = 5
    bottommargin = 5
    leftmargin = 5
    rightmargin = 5
    
class HudGroups(BaseHudGroups):
    def OnCursorEnteredButton(self, button):
        super(HudGroups, self).OnCursorEnteredButton(button)
        x, y = button.controlpanel.LocalToScreen(0, 0)
        GetAnimationController().RunAnimationCommand(button, "ypos", y+int(-1*button.GetTall()*0.3), 0.0, 0.25, AnimationController.INTERPOLATOR_LINEAR)
    def OnCursorExitedButton(self, button):
        super(HudGroups, self).OnCursorExitedButton(button)
        x, y = button.controlpanel.LocalToScreen(0, 0)
        GetAnimationController().RunAnimationCommand(button, "ypos", y, 0.0, 0.25, AnimationController.INTERPOLATOR_LINEAR)
