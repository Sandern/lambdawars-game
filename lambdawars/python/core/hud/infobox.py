from srcbase import Color
from vgui import scheme, GetClientMode, surface, scheme, AddTickSignal, RemoveTickSignal, vgui_input, localize
from vgui.controls import Panel, Label, TextEntry
from entities import C_HL2WarsPlayer
from core.abilities import GetAbilityInfo, GetTechNode
from core.units.info import unitlistpertype
from core.factions import GetFactionInfo
from core.resources import GetResourceInfo
import hotkeymgr
from gameinterface import engine
from gamerules import GameRules


class Description(TextEntry):
    def ApplySchemeSettings(self, schemobj):
        super().ApplySchemeSettings(schemobj)

        self.SetFgColor(Color(200,200,200,255))
        self.SetBgColor(Color(200,200,200,0))

        self.SetFont( schemobj.GetFont( "DebugFixedSmall" ) )

        self.SetBorder(None)


class InfoLabel(Label):
    def __init__(self, parent, panelname, text, fontcolor=None):
        super().__init__(parent, panelname, text)
        
        self.SetScheme(scheme().LoadSchemeFromFile("resource/HL2Wars.res", "HL2Wars")) 
        self.SetPaintBackgroundEnabled(False)
        self.SetPaintBorderEnabled(False)
        self.SetContentAlignment(Label.a_west)
        self.SetSize(scheme().GetProportionalScaledValueEx(self.GetScheme(), 50),
            scheme().GetProportionalScaledValueEx(self.GetScheme(), 15 ))
        self.fontcolor = fontcolor
        
    def ApplySchemeSettings(self, schemobj):
        super().ApplySchemeSettings(schemobj)
        
        hfontsmall = schemobj.GetFont("DefaultVerySmall")
        
        self.SetFont(hfontsmall)
        self.SetBgColor(Color(0,0,0,0))
        if self.fontcolor:
            self.SetFgColor(self.fontcolor)
        else:
            self.SetFgColor(Color(200,200,200,255))


class InfoObject(object):
    def __init__(self, parent, name, headertext, attribute=None, fontcolor=None):
        super().__init__()
        
        self.header = InfoLabel(parent, "%sHeader" % (name), headertext, fontcolor=fontcolor)
        self.info = InfoLabel(parent, "InfoText", "", fontcolor=fontcolor)
        self.attribute = attribute
        
    def UpdateLayout(self, xindent, cury, xwidth, ysize):
        if self.header.IsVisible():
            self.header.SetPos(xindent, cury)
            wide = self.header.GetWide()
            self.info.SetPos(xindent + wide, cury)
            cury += ysize
        return cury
        
    def SetText(self, text):
        self.info.SetText(text)
        
    def SetVisible(self, vis):
        self.header.SetVisible(vis)
        self.info.SetVisible(vis)
        self.vis = vis
        
    def IsVisible(self):
        return self.vis
        
    def SetColor(self, color):
        self.header.SetFgColor(color)
        self.info.SetFgColor(color)
        self.header.fontcolor = color
        self.info.fontcolor = color

    vis = False


class InfoGenRequirement(object):
    def __init__(self, parent, name, header_text, attribute=None, fontcolor=None):
        super().__init__()

        self.parent = parent
        self.header_text = header_text
        self.header = InfoLabel(parent, "%sHeader" % name, header_text, fontcolor=fontcolor)
        self.attribute = attribute
        
    def UpdateLayout(self, xindent, cury, xwidth, ysize):
        if self.header.IsVisible():
            self.header.SetPos(xindent, cury)
            self.header.SetSize(scheme().GetProportionalScaledValueEx(self.header.GetScheme(), 100),
                                scheme().GetProportionalScaledValueEx(self.header.GetScheme(), 15))
            cury += ysize
        return cury
        
    def SetVisible(self, vis):
        self.header.SetVisible(vis)
        self.vis = vis
        
    def IsVisible(self):
        return self.vis
        
    def SetColor(self, color):
        self.header.SetFgColor(color)
        self.header.fontcolor = color

    vis = False


class InfoUnitLimitRequirement(InfoGenRequirement):
    def CustomUpdate(self, color):
        abi_info = self.parent.showability

        unit_limit = getattr(getattr(GameRules(), 'info', object), 'unit_limits', {}).get(abi_info.name, None)
        if unit_limit is None:
            self.SetVisible(False)
            return

        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return

        owner = player.GetOwnerNumber()

        self.SetVisible(True)
        self.SetColor(color)

        # Assume not localized string when nothing is found.
        header_text = localize.Find(self.header_text) or self.header_text
        self.header.SetText(header_text % (len(unitlistpertype[owner][abi_info.name]), unit_limit))

class InfoList(object):
    def __init__(self, parent, name, headertext):
        self.header = InfoList(parent, "%sHeader" % (name), headertext)
        self.items = []
        self.itemlabels = []
        
    def UpdateLayout(self, xindent, cury, xwidth, ysize):
        if self.header.IsVisible() and self.itemlabels:
            self.header.SetPos(xindent, cury)
            cury += ysize
            for il in self.itemlabels:
                il.SetPos(xindent+xindent, cury)
                il.SetWide(xwidth-xindent)
                cury += ysize
        return cury
        
    def UpdateItems(self, items):
        self.items = items
        for il in self.itemlabels:
            il.DeletePanel()
        self.itemlabels = []
        if not items:
            return
        for i in self.items:
            il = InfoLabel(self, 'Item', '%s' % (i)) 
            il.SetVisible(True)
            self.itemlabels.append(il)


class BaseHudInfo(Panel):
    def __init__(self, 
            showhotkey=True, 
            showrechargetime=True, 
            showcosts=True, 
            showenergy=True,
            showtechreq=True,
            showbuildtime=True,
            showpopulation=True):
        super().__init__(None, "BaseHudInfo")
        self.SetParent(GetClientMode().GetViewport())

        self.SetProportional(True)
        self.SetPaintBackgroundEnabled(True)
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(False)     
        self.SetScheme(scheme().LoadSchemeFromFile("resource/HL2Wars.res", "HL2Wars"))  
        self.SetVisible(False)
        self.SetZPos(100)

        # Settings
        self.showhotkey = showhotkey
        self.showrechargetime = showrechargetime
        self.showcosts = showcosts
        self.showenergy = showenergy
        self.showtechreq = showtechreq
        self.showbuildtime = showbuildtime
        self.showpopulation = showpopulation
        
        # Create elements
        self.title = Label(self, "Title", "Put your title here!")
        self.title.SetPaintBackgroundEnabled(False)
        self.title.SetPaintBorderEnabled(False)
        self.title.SetContentAlignment(Label.a_west)
        self.title.SetVisible(True)
        
        self.hotkey = Label(self, "Hotkey", "")
        self.hotkey.SetPaintBackgroundEnabled(False)
        self.hotkey.SetPaintBorderEnabled(False )
        self.hotkey.SetContentAlignment(Label.a_west)
        self.hotkey.SetVisible(False)

        self.description = Description(self, "Description")
        self.description.SetPaintBackgroundEnabled( True )
        self.description.SetPaintBorderEnabled( True )
        self.description.SetVisible( True )
        self.description.SetVerticalScrollbar( False )
        self.description.SetMultiline( True )
        self.description.SetEditable( False )
        self.description.SetEnabled( True )
        
        self.description.SetText("")
        
        self.autocast = Label(self, "AutoCast", "Autocast supported")
        self.autocast.SetPaintBackgroundEnabled(False)
        self.autocast.SetPaintBorderEnabled(False)
        self.autocast.SetContentAlignment(Label.a_west)
        self.autocast.SetVisible(False)
        
    def ApplySchemeSettings(self, schemobj):
        super().ApplySchemeSettings(schemobj)
        
        self.SetBgColor(self.GetSchemeColor("ObjElement.BgColor", self.GetBgColor(), schemobj))
        self.SetBorder(schemobj.GetBorder("BaseBorder"))

        hfontnormal = schemobj.GetFont("Default")
        hfontsmallest = schemobj.GetFont("DebugFixedSmall")
    
        self.title.SetFont(hfontnormal)
        self.title.SetBgColor(Color(0,0,0,0))
        self.title.SetFgColor(Color(185,181,68,255))
        
        self.hotkey.SetFont(hfontnormal)
        self.hotkey.SetBgColor(Color(0,0,0,0))
        self.hotkey.SetFgColor(Color(220,220,0,255))
        
        self.description.SetFont(hfontsmallest)  
        
        self.autocast.SetBgColor(Color(0,0,0,0))
        self.autocast.SetFgColor(Color(220,220,0,255))
        self.autocast.SetFont(hfontnormal)  

    def PerformLayout(self):
        super().PerformLayout()
        
        # To position ourself above the mainhud we need to know the height of the main hud.
        if not self.mainhud_tall:
            self.mainhud_tall = scheme().GetProportionalScaledValueEx(self.GetScheme(), 135)
         
        screenwidth, screenheight = surface().GetScreenSize()
        self.iswidescreen = engine.GetScreenAspectRatio(screenwidth, screenheight) > 1.5
        width = scheme().GetProportionalScaledValueEx( self.GetScheme(), 180 if self.iswidescreen else 150 )
        self.SetWide(width)
        tall = scheme().GetProportionalScaledValueEx( self.GetScheme(), 5 )
        xpos = screenwidth - width
        
        xindent = scheme().GetProportionalScaledValueEx( self.GetScheme(), 10 ) # Indent for headers/labels
        xwidth = width - xindent*2
        ysize = scheme().GetProportionalScaledValueEx( self.GetScheme(), 10 )

        # Position the remaining elements (only if they are visible)
        self.title.SetPos(xindent, tall)
        self.title.SizeToContents()
        self.title.SetTall(ysize)
        title_wide = self.title.GetWide()
        self.hotkey.SetPos(xindent + title_wide + scheme().GetProportionalScaledValueEx( self.GetScheme(), 3 ), tall)
        self.hotkey.SetSize(scheme().GetProportionalScaledValueEx( self.GetScheme(), 25 ), ysize)
        tall += ysize
        
        tall = self.PerformLayoutElements(xindent, tall, xwidth, ysize)

        if self.description.IsVisible():
            # Keep some space between description and other info labels
            tall += scheme().GetProportionalScaledValueEx(self.GetScheme(), 5)
        
            self.description.SetPos( xindent, tall)
            self.description.SetWide(xwidth)
            self.description.SetToFullHeight()
            tall += self.description.GetTall()
            
        # Add autocast lable if needed
        if self.autocast.IsVisible():
            self.autocast.SetPos( xindent, tall)
            self.autocast.SetWide(xwidth)
            self.autocast.SetTall(ysize)
            tall += self.autocast.GetTall()
        
        # Keep some space between bottom and last element
        tall += scheme().GetProportionalScaledValueEx(self.GetScheme(), 5)
        
        # Finally set our size and position
        ypos = screenheight - self.mainhud_tall - tall
        self.defaultx = xpos
        self.defaulty = ypos
        if self.defaultpos:
            self.curx = xpos
            self.cury = ypos
        if self.posup:
            self.SetPos(self.curx, self.cury - tall)
        else:
            self.SetPos(self.curx, self.cury)
        self.SetTall(tall)
        
    def MoveTo(self, x, y, up=False):
        self.posup = up
        self.curx = x
        self.cury = y
        self.defaultpos = False
            
    def MoveToDefault(self):
        self.defaultpos = True
        self.posup = False

    def OnTick(self):
        if not self.IsVisible():
            return
            
        super().OnTick()
        
        # Fix/Work-around for a problem where the CursorEntered/CursorExited events don't arrive in the correct order, which
        # can happen at low framerates. Detect here if the mouse is still on the original panel and trigger time out otherwise.
        if self.contextpanel and self.showtimeout == None and vgui_input().GetMouseFocus() != self.contextpanel.GetVPanel():
            self.showtimeout = gpGlobals.curtime + self.TIMEOUT

        if self.showtimeout != None and self.showtimeout < gpGlobals.curtime:
            self.ShowAbility(None)
        elif self.showability:
            self.UpdateElements()
            self.Repaint()    
                
    # Changing the ability shown
    showability = None
    def ShowAbility(self, showability, slot=-1, unittype=None, contextpanel=None):
        if not showability:
            self.ClearInfoPanel()
            return
            
        # Get Player
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            self.ClearInfoPanel()
            return

        self.showtimeout = None
        self.contextpanel = contextpanel
        if showability == self.showability:
            self.PerformLayout()
            return  
            
        self.showability = showability
        self.unittype = player.GetSelectedUnitType() if not unittype else unittype
        
        AddTickSignal(self.GetVPanel(), 100)

        # Now change the information of the shown ability
        info = showability
        
        self.title.SetText(info.displayname)
        self.description.SetText(info.description)
        
        if self.showhotkey and slot != -1:
            self.hotkeychar = hotkeymgr.hotkeysystem.GetHotkeyForAbility(info, slot)
            if self.hotkeychar:
                self.hotkey.SetText('[%s]' % (self.hotkeychar.upper()) )
                self.hotkey.SetVisible(True)
            else:
                self.hotkey.SetVisible(False)
        else:
            self.hotkey.SetVisible(False)
            
        self.OnShowElements()
            
        self.SetVisible(True)
        
        self.PerformLayout()
        
        # Do an extra tick to color them correctly
        self.OnTick()
        
    def ClearInfoPanel(self):
        self.showability = None
        self.contextpanel = None
        self.SetVisible(False)
        RemoveTickSignal(self.GetVPanel())
        
    def GetColorBasedOnRequirements(self, requirements, name):
        return self.requiredcolor if name in requirements else self.normalcolor
        
    def PerformLayoutElements(self, xindent, cury, xwidth, ysize):
        return cury
        
    def UpdateElements(self):
        pass
            
    def OnShowElements(self):
        pass
        
    TIMEOUT = 0.05

    def HideAbility(self, timeout=TIMEOUT):
        self.showtimeout = gpGlobals.curtime + timeout

    # Default settings
    bgcolor = Color(255, 255, 255, 255)
    mainhud_tall = None
    iswidescreen = False
    
    normalcolor = Color(200,200,200,255)
    requiredcolor = Color(200,0,0,255)
    
    curx = 0
    cury = 0
    defaultpos = True
    posup = False
    showtimeout = None
    contextpanel = None
    hotkeychar = None


class AbilityHudInfo(BaseHudInfo):
    def __init__(self):
        super().__init__(showhotkey=True)
        
        # setting up headers for some Label's
        self.costheader = InfoLabel(self, "InfoCostHeader", self.cost)
        self.costs = []
        
        self.time = InfoObject(self, 'InfoTime', self.rechargetime, 'rechargetime')
        self.buildtime = InfoObject(self, "InfoBuildTime", self.buildtime, 'buildtime')
        self.population = InfoObject(self, "InfoPopulation", self.population, 'population')
        self.energy = InfoObject(self, "InfoEnergy", self.energy, 'energy')
        self.providespopulation = InfoObject(self, "InfoProvPopulation", self.providespopulation, 'providespopulation')
        
        self.genericinfolabels = [
            self.time,
            self.buildtime,
            self.population,
            self.energy,
            self.providespopulation,
        ]
        
        self.showifrequired = [
            InfoGenRequirement(self, "InfoMaxActiveOne", self.maxoneactive, 'maxoneactive'),
            InfoGenRequirement(self, "InfoNeedsUpgrade", self.needsupgrade, 'needsupgrade'),
            InfoGenRequirement(self, "InfoLocked", self.abilocked, 'locked'),
            InfoGenRequirement(self, "InfoPowered", self.needspow, 'powered'),
        ]

        self.custom_info_labels = [
            InfoUnitLimitRequirement(self, "InfoUnitLimit", self.unitlimit, 'unit_limit'),
        ]
        
        self.techheader = InfoLabel(self, "InfoTech", self.requirements)
        self.techrequirements = []

    cost = "#HUD_Cost"
    rechargetime = "#HUD_RechargeTime"
    buildtime = '#HUD_BuildTime'
    population = "#HUD_Population"
    energy = "#HUD_Energy"
    providespopulation = "#HUD_ProvPop"
    maxoneactive = "#HUD_MaxOneActive"
    needsupgrade = "#HUD_NeedsUpgrade"
    abilocked = "#HUD_AbiLocked"
    needspow = "#HUD_NeedsPower"
    unitlimit = "#HUD_UnitLimit"
    requirements = "#HUD_Requirements"

    def PerformLayoutElements(self, xindent, cury, xwidth, ysize):
        if self.costheader.IsVisible():
            self.costheader.SetPos(xindent, cury)
            cury += ysize
            for tr in self.costs:
                tr.SetPos(xindent+xindent, cury)
                tr.SetWide(xwidth-xindent)
                cury += ysize
                
        for label in self.genericinfolabels:
            if not label.IsVisible():
                continue
            cury = label.UpdateLayout(xindent, cury, xwidth, ysize)

        for label in self.showifrequired:
            if not label.IsVisible():
                continue
            cury = label.UpdateLayout(xindent, cury, xwidth, ysize)

        for label in self.custom_info_labels:
            if not label.IsVisible():
                continue
            cury = label.UpdateLayout(xindent, cury, xwidth, ysize)

        if self.techheader.IsVisible():
            self.techheader.SetPos(xindent, cury)
            self.techheader.SetWide(xwidth)
            cury += ysize
            for tr in self.techrequirements:
                tr.SetPos(xindent+xindent, cury)
                tr.SetWide(xwidth-xindent)
                cury += ysize
                
        return cury
        
    def HasUnitAutocastOn(self, info, units):
        for unit in units:
            if info.name not in unit.abilitiesbyname:
                continue
            if unit.abilitycheckautocast[info.uid]:
                return True
        return False
        
    def OnShowElements(self):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
            
        owner = player.GetOwnerNumber()
        factioninfo = GetFactionInfo(player.GetFaction())
            
        requirements = self.showability.GetRequirementsUnits(player)
        
        info = self.showability
        
        for c in self.costs:
            c.DeletePanel()
        self.costs = []
        if len(info.costs) != 0:
            costs = None
            
            # Prefer to show the costs that match the specified resources of the player faction
            if factioninfo:
                for clist in info.costs:
                    hassall = True
                    for c in clist:
                        if c[0] not in factioninfo.resources:
                            hassall = False
                            break
                        if hassall:
                            costs = clist
                    if costs:
                        break
                            
            # Default to first cost set
            if not costs:
                costs = info.costs[0]

            self.costheader.SetVisible(True)
            for c in costs:
                resinfo = GetResourceInfo(c[0])
                displayname = resinfo.displayname if resinfo else c[0]
                l = InfoLabel(self, 'Cost', '%s %s' % (c[1], displayname),
                              fontcolor=self.GetColorBasedOnRequirements(requirements, 'resources')) 
                l.SetVisible(True)
                self.costs.append(l)
        else:
            self.costheader.SetVisible(False)
       
        for label in self.genericinfolabels:
            # Don't display the label if the attribute does not exists or if
            # the value evaluates to zero (i.e. 0)
            value = getattr(info, label.attribute, None)
            if value:
                label.SetText(str(value))
                label.SetVisible(True)
            else:
                label.SetVisible(False)
                
        for label in self.showifrequired:
            if label.attribute in requirements:
                label.SetVisible(True)
                color = self.GetColorBasedOnRequirements(requirements, label.attribute)
                label.SetColor(color)
            else:
                label.SetVisible(False)

        for label in self.custom_info_labels:
            color = self.GetColorBasedOnRequirements(requirements, label.attribute)
            label.CustomUpdate(color)
                
        for tr in self.techrequirements:
            tr.DeletePanel()

        self.techrequirements = []
        if len(info.techrequirements) != 0:
            self.techheader.SetVisible(True)
            for tr in info.techrequirements:
                techinfo = GetAbilityInfo(tr)
                if not techinfo:
                    continue
                technode = GetTechNode(techinfo, owner)
                if not technode:
                    continue
                color = self.requiredcolor if not technode.techenabled else self.normalcolor
                l = InfoLabel(self, 'TechRequirement', '- %s' % techinfo.displayname, fontcolor=color)
                l.technode = technode
                l.SetVisible(True)
                self.techrequirements.append(l)
        else:
            self.techheader.SetVisible(False)
            
        self.autocast.SetVisible(info.supportsautocast)
            
    def UpdateElements(self):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return

        if not self.unittype:
            return
            
        # Get requirements
        requirements = self.showability.GetRequirementsUnits(player)

        color = self.GetColorBasedOnRequirements(requirements, 'recharging')
        self.time.SetColor(color)
        
        color = self.GetColorBasedOnRequirements(requirements, 'resources')
        self.costheader.SetFgColor(color)
        for c in self.costs:
            c.SetFgColor(color)
            
        if hasattr(self.showability, 'population'):
            color = self.GetColorBasedOnRequirements(requirements, 'population')
            self.population.SetColor(color)
            
        color = self.GetColorBasedOnRequirements(requirements, 'energy')
        self.energy.SetColor(color)
        
        hasrequiredtech = False
        for tr in self.techrequirements:
            if not tr.technode.techenabled:
                color = self.requiredcolor
                hasrequiredtech = True
            else:
                color = self.normalcolor
            tr.SetFgColor(color)
            
        if hasrequiredtech:
            color = self.requiredcolor
        else:
            color = self.normalcolor
        self.techheader.SetFgColor(color)
            
        info = self.showability
        if info.supportsautocast:
            if self.HasUnitAutocastOn(info, player.GetSelection()):
                self.autocast.SetText(self.autocaston)
            else:
                self.autocast.SetText(self.autocastoff)

    autocaston = '#HUD_AutocastOn'
    autocastoff = "#HUD_AutocastOff"


class UnitHudInfo(BaseHudInfo):
    def __init__(self):
        super().__init__(showhotkey=False)
        
        self.health = InfoObject(self, "InfoHealth", self.strhealth, fontcolor=self.healthcolor)
        self.energy = InfoObject(self, "InfoEnergy", self.strenergy, fontcolor=self.energycolor)
        
    def PerformLayoutElements(self, xindent, cury, xwidth, ysize):
        if self.health.IsVisible():
            cury = self.health.UpdateLayout(xindent, cury, xwidth, ysize)
        if self.energy.IsVisible():
            cury = self.energy.UpdateLayout(xindent, cury, xwidth, ysize)
        return cury
        
    def OnShowElements(self):
        self.health.SetVisible(self.unit.maxhealth > 0)
        self.energy.SetVisible(self.unit.maxenergy > 0)
        
    def UpdateElements(self):
        if not self.unit:
            return
            
        self.health.SetText('%d / %d' % (max(1, self.unit.health), self.unit.maxhealth))
        self.health.SetColor(self.healthcolor)
        self.energy.SetText('%d / %d' % (self.unit.energy, self.unit.maxenergy))
        self.energy.SetColor(self.energycolor)
        
    unit = None
    healthcolor = Color(0, 255, 0, 255)
    energycolor = Color(0, 200, 255, 255)
    strhealth = "#HUD_Health"
    strenergy = "#HUD_Energy"


class QueueUnitHudInfo(BaseHudInfo):
    def __init__(self):
        super().__init__(showhotkey=False)

        self.buildtime = InfoObject(self, "InfoBuildTime", "#HUD_UnitBuildTime")
        
    def PerformLayoutElements(self, xindent, cury, xwidth, ysize):
        if self.buildtime.IsVisible(): cury = self.buildtime.UpdateLayout(xindent, cury, xwidth, ysize)
        return cury
        
    def OnShowElements(self):
        self.buildtime.SetVisible(self.unit != None)
        
    def UpdateElements(self):
        if not self.unit:
            return
            
        progress = self.unit.GetBuildProgress()
        timepassed = progress * self.unit.buildtime
        self.buildtime.SetText('%d / %d' % (timepassed, self.unit.buildtime))


class AttributeUnitHudInfo(BaseHudInfo):
    def __init__(self):
        super().__init__(showhotkey=False)
        
    def OnShowElements(self):
        attributedesc = ''
        unit = self.unit
        attributes = unit.GetActiveAttributes()
        for attr in attributes.values():
            attributedesc += attr.description
    
        self.title.SetText(self.strattributes)
        self.description.SetText(attributedesc)

    strunitbuildtime = "#HUD_UnitBuildTime"
    strattributes = "#HUD_Attributes"
