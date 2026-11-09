"""Shared framed sections for the faction RTS HUDs.

Builds the minimap, population, resource, ability, unit, and control-group
blocks used by the Rebel and Combine HUDs. Each section paints a background
icon and lays a core HUD widget inside it. Faction modules subclass a section
and replace ``backgroundtexture``.

Example:
    from wars_game.hud.warshud import HudMinimapSection

    section = HudMinimapSection(GetClientMode().GetViewport())
    section.SetVisible(True)
"""
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
    """Panel that paints one HUD icon across its rectangle.

    Subclasses set ``backgroundtexture`` to an icon name. The icon is resolved
    in the constructor and stretched to the panel size while the background
    paints. ``drawcolor`` tints that icon.

    Example:
        class PopulationFrame(BackgroundPanel):
            backgroundtexture = 'hud_rebels_population'

        frame = PopulationFrame(viewport, 'PopulationFrame')
    """
    def __init__(self, parent, panelname):
        """Create the panel and resolve its background icon.

        Args:
            parent (Panel): Parent VGUI panel.
            panelname (str): Panel name registered with VGUI.

        Example:
            frame = BackgroundPanel(viewport, 'HudFrame')
        """
        super(BackgroundPanel, self).__init__(parent, panelname)
        
        self.SetPaintBackgroundEnabled(True)
        self.background = HudIcons().GetIcon(self.backgroundtexture)

    def PaintBackground(self):
        """Draw the background icon stretched to the panel.

        Nothing is drawn when the icon name did not resolve.

        Example:
            frame.PaintBackground()
        """
        if self.background:
            w, h = self.GetSize()
            self.background.DrawSelf(0, 0, w, h, self.drawcolor)
            
    background = None
    backgroundtexture = None
    drawcolor = Color(255, 255, 255, 255)
    
class TopPanel(Panel):
    """Overlay that paints a HUD icon and forwards mouse input.

    The background icon is resolved when the scheme is applied, then drawn
    from ``Paint`` rather than the panel background. Mouse press, release,
    and double-press are passed to the parent so a frame on top of another
    HUD control does not swallow the click.

    Example:
        overlay = TopPanel(section, 'MinimapOverlay')
        overlay.backgroundtexture = 'hud_rebels_minimap'
    """
    def __init__(self, parent, panelname):
        """Create the overlay with background painting disabled.

        Args:
            parent (Panel): Parent VGUI panel.
            panelname (str): Panel name registered with VGUI.

        Example:
            overlay = TopPanel(section, 'MinimapOverlay')
        """
        super(TopPanel, self).__init__(parent, panelname)

        self.SetPaintBackgroundEnabled(False)
        
    def ApplySchemeSettings(self, schemeobj):
        """Resolve the background icon from the active scheme.

        Args:
            schemeobj (IScheme): Scheme VGUI is applying to this panel.

        Example:
            overlay.ApplySchemeSettings(scheme().GetIScheme(overlay.GetScheme()))
        """
        super(TopPanel, self).ApplySchemeSettings(schemeobj)
        
        self.background = HudIcons().GetIcon(self.backgroundtexture)

    def Paint(self):
        """Draw the background icon stretched to the panel.

        Nothing is drawn when the icon name did not resolve.

        Example:
            overlay.Paint()
        """
        if self.background:
            w, h = self.GetSize()
            self.background.DrawSelf(0, 0, w, h, self.drawcolor)
            
    def OnMouseReleased(self, code):
        """Forward a mouse release to the parent panel.

        Args:
            code (int): Button code from ``input.ButtonCode_t``.

        Example:
            overlay.OnMouseReleased(ButtonCode_t.MOUSE_LEFT)
        """
        self.CallParentFunction(KeyValues("MouseReleased", "code", code))
        
    def OnMousePressed(self, code):
        """Forward a mouse press to the parent panel.

        Args:
            code (int): Button code from ``input.ButtonCode_t``.

        Example:
            overlay.OnMousePressed(ButtonCode_t.MOUSE_LEFT)
        """
        self.CallParentFunction(KeyValues("MousePressed", "code", code))
        
    def OnMouseDoublePressed(self, code):
        """Forward a mouse double-press to the parent panel.

        Args:
            code (int): Button code from ``input.ButtonCode_t``.

        Example:
            overlay.OnMouseDoublePressed(ButtonCode_t.MOUSE_LEFT)
        """
        self.CallParentFunction(KeyValues("MouseDoublePressed", "code", code))
        
    background = None
    backgroundtexture = None
    drawcolor = Color(255, 255, 255, 255)
    
class HudMinimapSection(BackgroundPanel):
    """Minimap frame with a team-color toggle.

    Hosts the live minimap and the button that flips
    ``cl_teamcolor_relationbased``. The map and button are parented to the
    viewport, not this frame, so they draw above the background art. Faction
    HUDs subclass this and replace the background and button textures.
    Showing or hiding the section also shows or hides those two children.

    Example:
        section = HudMinimapSection(GetClientMode().GetViewport())
        section.SetVisible(True)
    """
    def __init__(self, parent):
        """Build the frame, the live minimap, and the team-color button.

        Args:
            parent (Panel): Viewport panel that owns the section.

        Example:
            section = HudMinimapSection(GetClientMode().GetViewport())
        """
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
        """Show or hide the frame, the minimap, and the team-color button.

        Args:
            visible (bool): ``True`` to show the section.

        Example:
            section.SetVisible(player.GetControlledUnit() is not None)
        """
        super(HudMinimapSection, self).SetVisible(visible)
        if self.minimap:
            self.minimap.SetVisible(visible)
        if self.teamcolorbutton:
            self.teamcolorbutton.SetVisible(visible)
            
    def UpdateOnDelete(self):
        """Delete the minimap and team-color button with this frame.

        Both children are parented to the viewport, so destroying the frame
        alone would leave them on screen.

        Example:
            section.UpdateOnDelete()
        """
        if self.minimap:
            self.minimap.DeletePanel()
            self.minimap = None
        if self.teamcolorbutton:
            self.teamcolorbutton.DeletePanel()
            self.teamcolorbutton = None
        
    def PerformLayout(self):
        """Place the minimap and team-color button inside the frame.

        Positions are fractions of this panel's size: ``minimapxpos``,
        ``minimapypos``, ``minimapwide``, ``minimaptall``, ``teamcolorrelposx``,
        and ``teamcolorrelposy``.

        Example:
            section.PerformLayout()
        """
        super(HudMinimapSection, self).PerformLayout()
        
        x, y = self.GetPos()
        self.minimap.SetPos(x+int(self.minimapxpos*self.GetWide()), y+int(self.minimapypos*self.GetTall()))
        self.minimap.SetSize(int(self.minimapwide*self.GetWide()), int(self.minimaptall*self.GetTall()))

        wide, tall = self.GetSize()
        self.teamcolorbutton.SetPos(x+int(wide*self.teamcolorrelposx), y+int(tall*self.teamcolorrelposy))
        self.teamcolorbutton.SetSize(int(wide*0.1), int(tall*0.1))
        
    def OnCommand(self, command):
        """Toggle relation-based team colors when the button fires.

        Args:
            command (str): Command name sent by the child button.

        Returns:
            bool: ``True`` when ``teamcolortoggle`` was handled.

        Example:
            section.OnCommand('teamcolortoggle')
        """
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
    """Population counter framed by the faction HUD art.

    Shows the local owner's current population and the population cap as
    ``current / max``. The label turns red when the count is over the cap.
    The counter refreshes four times a second.

    Args:
        parent (Panel): Viewport panel that owns the section.
        config (dict): HUD config passed by the faction HUD. This section
            does not read it.

    Example:
        population = HudPopulationSection(viewport, {})
    """
    def __init__(self, parent, config):
        """Create the population label and start its refresh tick.

        Args:
            parent (Panel): Viewport panel that owns the section.
            config (dict): Unused. Accepted so every section shares a constructor.

        Example:
            population = HudPopulationSection(viewport, {})
        """
        super(HudPopulationSection, self).__init__(parent, 'HudPopulationSection')
        
        self.amountunits = Label(self,"UnitsAmount","")
        self.amountunits.MakeReadyForUse()
        self.amountunits.SetScheme(scheme().LoadSchemeFromFile("resource/ClientScheme.res", "ClientScheme"))
        self.amountunits.SetPaintBackgroundEnabled(False)
        self.amountunits.SetPaintBorderEnabled(False)
        self.amountunits.SetContentAlignment(Label.a_west)

        AddTickSignal(self.GetVPanel(), 250)
        
    def PerformLayout(self):
        """Place the population label inside the frame.

        The label sits 38 units from the left and 10 from the top, in
        proportional scheme units.

        Example:
            population.PerformLayout()
        """
        super(HudPopulationSection, self).PerformLayout()
        
        margintop = scheme().GetProportionalScaledValueEx(self.GetScheme(), 10)
        marginleft = scheme().GetProportionalScaledValueEx(self.GetScheme(), 38)
        self.amountunits.SetSize(scheme().GetProportionalScaledValueEx(self.GetScheme(), 50), 
            scheme().GetProportionalScaledValueEx(self.GetScheme(), 20))
        self.amountunits.SetPos(marginleft, margintop)
                
    def OnTick(self):
        """Refresh the population text from the local owner's counts.

        The text is red when population is above the cap and white otherwise.

        Example:
            population.OnTick()
        """
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
    """Resource counters framed by the faction HUD art.

    Shows up to three resources from the local player's faction. Each row is
    an icon plus a number. When a value changes, the displayed number eases
    toward the real amount and a tick sound plays once the change is fast.
    Capped resources are drawn as ``amount / cap``.

    Example:
        resources_panel = HudResourceSection(viewport, {})
    """
    def __init__(self, parent, config):
        """Create three resource rows and start the refresh tick.

        Args:
            parent (Panel): Viewport panel that owns the section.
            config (dict): Unused. Accepted so every section shares a constructor.

        Example:
            resources_panel = HudResourceSection(viewport, {})
        """
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
        """Style the resource labels for the active scheme.

        Args:
            scheme_obj (IScheme): Scheme VGUI is applying to this panel.

        Example:
            resources_panel.ApplySchemeSettings(scheme_obj)
        """
        super(HudResourceSection, self).ApplySchemeSettings(scheme_obj)

        for l in self.resources:
            l.SetBgColor(Color(0,0,0,0))
            l.SetFgColor(Color(225,225,225,255))
            l.SetContentAlignment(Label.a_west)
        
    def PerformLayout(self):
        """Stack the resource icons and labels down the frame.

        Row spacing, top margin, and left margin come from ``spacing``,
        ``margintop``, and ``marginleft`` on the class.

        Example:
            resources_panel.PerformLayout()
        """
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
        """Ease each displayed resource toward the owner's real amount.

        A tick sound plays while the displayed value is catching up quickly.
        Requisition does not play that sound when the amount is rising.

        Example:
            resources_panel.OnTick()
        """
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
    """Combine frame that shows population and resources together.

    The population count sits on the lower part of the frame. Up to three
    faction resources sit above it, using the same eased counter and tick
    sound as ``HudResourceSection``.

    Example:
        panel = HudPopulationAndResourceSection(viewport, {})
    """
    def __init__(self, parent, config):
        """Create the population label, three resource rows, and the tick.

        Args:
            parent (Panel): Viewport panel that owns the section.
            config (dict): Unused. Accepted so every section shares a constructor.

        Example:
            panel = HudPopulationAndResourceSection(viewport, {})
        """
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
        """Style the resource labels for the active scheme.

        Args:
            scheme_obj (IScheme): Scheme VGUI is applying to this panel.

        Example:
            panel.ApplySchemeSettings(scheme_obj)
        """
        super(HudPopulationAndResourceSection, self).ApplySchemeSettings(scheme_obj)

        for l in self.resources:
            l.SetBgColor(Color(0,0,0,0))
            l.SetFgColor(Color(255,255,255,255))
            l.SetContentAlignment(Label.a_west)
        
    def PerformLayout(self):
        """Place the population label and the resource rows in the frame.

        The population label is anchored near the bottom. Resource rows use
        ``spacing``, ``margintop``, and ``marginleft``.

        Example:
            panel.PerformLayout()
        """
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
        """Refresh population and ease each resource toward its real amount.

        Population text turns red when the count is over the cap. The resource
        tick sound matches ``HudResourceSection``.

        Example:
            panel.OnTick()
        """
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
    """Ability-bar frame.

    Insets ``BaseHudAbilities`` inside the faction background. The ability
    panel reports hover details through the shared info box.

    Example:
        abilities = HudAbilitiesSection(viewport, infobox, config)
    """
    def __init__(self, parent, infobox, config):
        """Create the ability grid inside this frame.

        Args:
            parent (Panel): Viewport panel that owns the section.
            infobox (AbilityHudInfo): Panel that shows the hovered ability.
            config (dict): Layout values forwarded to ``BaseHudAbilities``.

        Example:
            abilities = HudAbilitiesSection(viewport, infobox, {})
        """
        super(HudAbilitiesSection, self).__init__(parent, 'HudAbilitiesSection')
        
        self.SetProportional(True)
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(True)
        
        self.abilitypanel = BaseHudAbilities(self, infobox, config)
        self.abilitypanel.marginbottom = 2
        self.abilitypanel.margintop = 3
        
    def UpdateOnDelete(self):
        """Delete the ability grid with this frame.

        Example:
            abilities.UpdateOnDelete()
        """
        self.abilitypanel.DeletePanel()
        
    def PerformLayout(self):
        """Inset the ability grid by the section margins.

        ``topmargin``, ``bottommargin``, ``leftmargin``, and ``rightmargin``
        are proportional scheme units.

        Example:
            abilities.PerformLayout()
        """
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

class HudAbilitiesFPSSection(HudAbilitiesSection):
    """One-row ability bar for a possessed unit.

    The twelve ability slots are laid out left to right instead of the RTS
    4 by 3 grid. The owning HUD places this section at the bottom center of
    the screen.

    Example:
        bar = HudAbilitiesFPSSection(viewport, infobox, config)
    """
    def __init__(self, parent, infobox, config):
        super(HudAbilitiesFPSSection, self).__init__(parent, infobox, config)
        self.abilitypanel.usefpsmap = True
        self.abilitypanel.nslotsx = 6
        self.abilitypanel.nslotsy = 2
        for slot in self.abilitypanel.slots:
            slot.iconcoords = (0.2, 0.2, 0.55, 0.55)
        # Panels start visible. The strategic HUD is already shown on map load,
        # so its SetVisible does not run until the first control toggle.
        self.SetVisible(False)

    def PerformLayout(self):
        super(HudAbilitiesFPSSection, self).PerformLayout()

    backgroundtexture = ''
    
    topmargin = 0
    bottommargin = 0
    leftmargin = 0
    rightmargin = 0

class HudUnits(BaseHudUnits):
    """Selected-unit grid used inside ``HudUnitsSection``.

    ``scale_values`` maps a panel width to ``(button size, buttons per row)``.
    ``unitbuttonhpbounds`` is the health-bar rectangle inside each unit button,
    as fractions ``(left, right, top, bottom)``.

    Example:
        panel.defaultunitpanelclass = HudUnits
    """
    scale_values = {
        20 : (10, 2),
        60 : (15, 3),
        80 : (20, 4)
    }
    unitbuttonhpbounds = (0.043, 0.96, 0.87, 0.96) # xmin, xmax, ymin, ymax
    
class HudUnitsSection(BackgroundPanel):
    """Selected-unit frame.

    Hosts a ``HudUnitsContainer`` that uses ``HudUnits`` for the unit buttons.
    Hovering a button shows that unit in ``infopanel``.

    Example:
        units = HudUnitsSection(viewport, infobox, config)
    """
    def __init__(self, parent, infopanel, config):
        """Create the unit grid inside this frame.

        Args:
            parent (Panel): Viewport panel that owns the section.
            infopanel (AbilityHudInfo): Panel that shows the hovered unit.
            config (dict): Layout values forwarded to ``HudUnitsContainer``.

        Example:
            units = HudUnitsSection(viewport, infobox, {})
        """
        super(HudUnitsSection, self).__init__(parent, 'HudUnitsSection')
        
        self.SetProportional(True)
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(True)
        
        self.unitpanel = HudUnitsContainer(self, infopanel, config)
        self.unitpanel.defaultunitpanelclass = HudUnits
        
    def UpdateOnDelete(self):
        """Delete the unit grid with this frame.

        Example:
            units.UpdateOnDelete()
        """
        self.unitpanel.DeletePanel()
        
    def PerformLayout(self):
        """Inset the unit grid by the section margins.

        ``topmargin``, ``bottommargin``, ``leftmargin``, and ``rightmargin``
        are proportional scheme units.

        Example:
            units.PerformLayout()
        """
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
    """Control-group bar that lifts a button while the cursor is over it.

    Entering a group button slides it up by 30 percent of its height. Leaving
    the button slides it back. Both moves take a quarter of a second.

    Example:
        groups = HudGroups(viewport, config)
    """
    def OnCursorEnteredButton(self, button):
        """Slide a group button upward while the cursor is over it.

        Args:
            button (GroupButton): Button the cursor entered.

        Example:
            groups.OnCursorEnteredButton(button)
        """
        super(HudGroups, self).OnCursorEnteredButton(button)
        x, y = button.controlpanel.LocalToScreen(0, 0)
        GetAnimationController().RunAnimationCommand(button, "ypos", y+int(-1*button.GetTall()*0.3), 0.0, 0.25, AnimationController.INTERPOLATOR_LINEAR)
    def OnCursorExitedButton(self, button):
        """Slide a group button back down when the cursor leaves it.

        Args:
            button (GroupButton): Button the cursor left.

        Example:
            groups.OnCursorExitedButton(button)
        """
        super(HudGroups, self).OnCursorExitedButton(button)
        x, y = button.controlpanel.LocalToScreen(0, 0)
        GetAnimationController().RunAnimationCommand(button, "ypos", y, 0.0, 0.25, AnimationController.INTERPOLATOR_LINEAR)
