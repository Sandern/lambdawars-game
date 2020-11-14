from srcbase import Color, IN_DUCK
from vgui import cursors, surface, AddTickSignal, HudIcons, scheme, vgui_input, images
from vgui.controls import Panel, Label, TextEntry
from entities import C_HL2WarsPlayer, MouseTraceData
from input import ButtonCode_t
from gameinterface import engine, concommand
from collections import defaultdict
from core.signals import FireSignalRobust, selectionchanged, refreshhud, garrisonchanged
from .abilitybutton import AbilityButton
from .infobox import UnitHudInfo, AttributeUnitHudInfo
from math import floor
from input import MOUSE_RIGHT
from operator import attrgetter

class UnitButton(AbilityButton):
    """ Button that represents an unit. """
    def GetHealth(self):
        return self._health
    def SetHealth(self, health):
        if health == self._health:
            return
        self._health = health
        self.CalculateHealthBar()
        
    health = property(GetHealth, SetHealth)
    
    def CalculateHealthBar(self):
        # Calculate pos, size and colors
        red = 230 - int(self._health * 230.0)
        green = int(self._health * 230.0)

        x, y = self.GetSize()

        self.xmin = int(self.hpxmincoord * x)
        self.ymin = int(self.hpymincoord * y)
        self.ymax = int(self.hpymaxcoord * y)
        self.xmax = self.xmin + int(self._health * (x - ( 2 * (1.0-self.hpxmaxcoord) * x )))
        self.drawcolor = Color(red, green, 0, 255)
        self.FlushSBuffer() # Trigger the Paint function in python
        
    _health = -1.0 
    drawcolor = Color(0, 230, 0, 255)
    xmin = 0
    xmax = 0
    ymin = 0
    ymax = 0
    
    hpxmincoord = 0.0625
    hpxmaxcoord = 0.9375
    hpymincoord = 0.8125
    hpymaxcoord = 0.9375  
    
    unit = None
    info = None
    smallIcon = None
    
    def Paint(self):
        """ Draw health bar behind the button image
            This is specific for the used unit images """
        # draw how much health we still got
        surface().DrawSetColor(self.drawcolor)
        surface().DrawFilledRect(self.xmin, self.ymin, self.xmax, self.ymax)  
            
        super().Paint()
        
        w, h = self.GetSize()
        if self.smallIcon:
            self.smallIcon.DrawSelf(0, 0, w*0.2, h*0.2, whitecolor)

    def UpdateCursor(self):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return

        if player.GetSingleActiveAbility():
            self.SetCursor(cursors.GetCursor("resource/arrows/ability_cursor.ani"))
        else:
            self.SetCursor(cursors.GetCursor("resource/arrows/default_cursor.cur"))
        
    def OnCursorEntered(self):
        super().OnCursorEntered()
        self.ShowAbility()
        self.UpdateCursor()

    def OnCursorExited(self):
        super().OnCursorExited()
        self.HideAbility()
        self.UpdateCursor()
        
    def ShowAbility(self):
        if self.info:
            infopanel = self.GetParent().infopanel
            # for some reason LocalToScreen doesn't works like it should, so just use GetCursorPosition
            #x, y = self.GetPos()
            #print '1 x: %d, y: %d' % (x, y)
            #x, y = self.LocalToScreen(x, y)
            #print '2 x: %d, y: %d' % (x, y)
            x, y = vgui_input().GetCursorPosition()
            infopanel.MoveTo(x, y, up=True)
            infopanel.unit = self.unit
            infopanel.ShowAbility(self.info, contextpanel=self)

    def HideAbility(self):
        infopanel = self.GetParent().infopanel
        infopanel.HideAbility()
        infopanel.unit = None
        
    def OnMouseDoublePressed(self, code):
        if code != ButtonCode_t.MOUSE_LEFT:
            self.OnMousePressed(code)
            return
            
        self.GetParent().OnUnitDoublePressed(self.unit)
        
class AttributeLabel(Label):
    def OnCursorEntered(self):
        super().OnCursorEntered()
        self.ShowAbility()

    def OnCursorExited(self):
        super().OnCursorExited()
        self.HideAbility()
        
    def ShowAbility(self):
        if self.info:
            infopanel = self.GetParent().attrinfopanel
            # for some reason LocalToScreen doesn't works like it should, so just use GetCursorPosition
            #x, y = self.GetPos()
            #print '1 x: %d, y: %d' % (x, y)
            #x, y = self.LocalToScreen(x, y)
            #print '2 x: %d, y: %d' % (x, y)
            x, y = vgui_input().GetCursorPosition()
            infopanel.MoveTo(x, y, up=True)
            infopanel.unit = self.unit
            infopanel.ShowAbility(self.info, contextpanel=self)

    def HideAbility(self):
        infopanel = self.GetParent().attrinfopanel
        infopanel.HideAbility()
        infopanel.unit = None
        
    unit = None
    info = None
    
class BaseHudUnits(Panel):
    """ Panel used for showing multiple selected units. """
    def __init__(self, parent, config):
        super().__init__(parent, "BaseHudUnits")
        
        self.config = config
        
        self.unitbuttontexture = config.get('units_button_enabled', 'hud_rebels_unitbutton_enabled')
        self.unitbuttontextureselected = config.get('units_button_pressed', 'hud_rebels_unitbutton_pressed')
        self.unitbuttontexturehover = config.get('units_button_hover', 'hud_rebels_unitbutton_hover')
        self.unitbuttoniconcoords = config.get('units_button_iconcoords', (0.1, 0.1, 0.8, 0.8)) # X, Y, Wide, Tall
        self.unitbuttonhpbounds = config.get('units_button_hpbounds', (0.0625, 0.9375, 0.8125, 0.9375)) # xmin, xmax, ymin, ymax

        self.EnableSBuffer(True)
        self.SetProportional(True)
        self.SetPaintBackgroundEnabled(False)
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(True)
        
        self.slotsizex = 0
        self.slotsizey = 0
        
        # Create unit buttons
        self.slots = []
        for i in range(0, self.MAXUNITSLOTS):
            namecommand = 'unitslot_%d' % (i)
            namecommand2 = 'unitslotright_'+ str(i)
            slot = UnitButton(self, namecommand)
            slot.iconcoords = self.unitbuttoniconcoords
            slot.hpxmincoord = self.unitbuttonhpbounds[0]
            slot.hpxmaxcoord = self.unitbuttonhpbounds[1]
            slot.hpymincoord = self.unitbuttonhpbounds[2]
            slot.hpymaxcoord = self.unitbuttonhpbounds[3]
            slot.SetZPos(1)
            slot.SetAllImages(HudIcons().GetIcon(self.unitbuttontexture), Color(255, 255, 255, 255))
            if self.unitbuttontextureselected:
                slot.SetImage(slot.BUTTON_ENABLED_MOUSE_OVER, HudIcons().GetIcon(self.unitbuttontextureselected), Color(255, 255, 255, 255))
            if self.unitbuttontextureselected:
                slot.SetImage(slot.BUTTON_PRESSED, HudIcons().GetIcon(self.unitbuttontextureselected), Color(255, 255, 255, 255))
            slot.SetCommand(namecommand)
            slot.SetCommandRightClick(namecommand2)
            slot.SetMouseClickEnabled(MOUSE_RIGHT, True) # Default is left only
            slot.AddActionSignalTarget(self)
            slot.SetMouseInputEnabled(True)
            slot.SetVisible(False)
            self.slots.append(slot)
        self.neededslots = 0 # Slots that should be visible (equals amount of units)
        
        # Info box
        self.infopanel = UnitHudInfo()
        
    def UpdateOnDelete(self):
        if self.infopanel:
            self.infopanel.HideAbility()
            self.infopanel.DeletePanel()
            self.infopanel = None
        
    def SetVisible(self, visible):
        super().SetVisible(visible)
        if not visible and self.infopanel:
            self.infopanel.HideAbility()
            
    def OnShowHud(self):
        pass
            
    def Update(self):
        # Update health
        for i in range(0, self.neededslots):
            slot = self.slots[i]
            unit = slot.unit
            if not unit:
                continue
            slot.health = unit.HealthFraction()

    def PerformLayout(self):
        """ Setup the unit buttons """
        super().PerformLayout()

        spacingx = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.spacingx) 
        spacingy = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.spacingy) 
        
        w, h = self.GetSize()
        
        # Compute grid
        y = 2
        for i in range(0, 100):
            spacingh = (spacingy * y) - spacingy
            self.slotsizey = int( ((h-spacingh) / y) * (1 - (h/w)) * 1.5 ) 
            self.slotsizex = int(self.slotsizey * self.buttonwideratio)

            x = int(floor(w/(self.slotsizex+spacingx-1)))
            
            if x * y > self.neededslots:
                self.curmax = x * y
                self.curmin = int(x * y * 0.75)
                break
                
            y += 1
            
        # Set size and position for each button
        for j in range(0, y):
            for i in range(0, x):
                self.slots[i+j*x].SetSize(self.slotsizex, self.slotsizey)
                self.slots[i+j*x].SetPos(i*self.slotsizex+i*spacingx, j*self.slotsizey+j*spacingy)
                self.slots[i+j*x].CalculateHealthBar()
                
    #@profile('BaseHudUnits.Paint')
    def Paint(self):
        super().Paint()
        
        #self.PaintActiveUnitsType()
            
    '''def PaintActiveUnitsType(self):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
            
        hlmin, hlmax = player.GetSelectedUnitTypeRange()
        if hlmin == -1:
            return
        
        w, h = self.GetSize()
        
        # Set color
        surface().DrawSetColor(255, 255, 255, 200)

        # Find start
        xstart = hlmin
        yrow = 0
        remaining = hlmax - hlmin
        while xstart >= x:
            xstart -= x
            yrow += 1 

        # Draw first
        drawmax = min(xstart+remaining, x)
        surface().DrawOutlinedRect( xstart * self.slotsizex, (yrow)*self.slotsizey, drawmax * self.slotsizex, (yrow+1)*self.slotsizey)
        yrow += 1
        remaining = (hlmax - hlmin) - (drawmax-xstart)
        while remaining > 0:
            drawmax = min(remaining, x)
            surface().DrawOutlinedRect( 0, (yrow)*self.slotsizey, drawmax * self.slotsizex, (yrow+1)*self.slotsizey)
            remaining -= x
            yrow += 1'''
            
    def OnCommand(self, command):
        
        splitted = command.split('_')
        if splitted[0] == 'unitslot':
            idx = int(splitted[1])
            self.OnSlotLeftClick(self.slots[idx])
            return
        elif splitted[0] == 'unitslotright':
            idx = int(splitted[1])
            self.OnSlotRightClick(self.slots[idx])
            return
        raise Exception('Unknown command ' + command)
        
    def OnSlotLeftClick(self, slot):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer() 
        unit = slot.unit

        active_ability = player.GetSingleActiveAbility()
        if active_ability:
            mousedata = MouseTraceData()
            mousedata.ent = unit
            player.PortraitClick(mousedata)
            slot.UpdateCursor()
            return

        ctrldown = player.buttons & IN_DUCK
        unittype = unit.GetUnitType()
        if not ctrldown:
            # Control not down: selects unit type for casting abilities
            player.SetSelectedUnitType(unit.GetUnitType())
            FireSignalRobust(refreshhud)
        else:
            # Control down: Selects all units of this type in selection, removing the others
            selection = list(player.GetSelection())
            player.ClearSelection(False) # Do not trigger on selection changed, since we do that below too already.
            engine.ServerCommand("player_clearselection")
            player.MakeSelection([unit for unit in selection if unit.GetUnitType() == unittype])
            
    def OnSlotRightClick(self, slot):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer() 
        unit = slot.unit
        ctrldown = player.buttons & IN_DUCK
        unittype = unit.GetUnitType()
        if not ctrldown:
            # Control not down: removes the unit
            player.RemoveUnit(unit)
            engine.ServerCommand('player_removeunit %d' % (unit.entindex()))
        else:
            # Control down: Removes all units of this type in selection
            selection = list(player.GetSelection())
            player.ClearSelection(False) # Do not trigger on selection changed, since we do that below too already.
            engine.ServerCommand("player_clearselection")
            player.MakeSelection([unit for unit in selection if unit.GetUnitType() != unittype])
            
    def OnUnitDoublePressed(self, unit):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
        player.ClearSelection(False) # Do not trigger on selection changed, since we do that below too already.
        engine.ServerCommand('player_clearselection')
        player.AddUnit(unit)
        engine.ServerCommand('player_addunit %d' % unit.entindex())
        
    def UpdateUnits(self, units):
        # Update amount of visible slots if needed
        unitcount = len(units)
        if self.neededslots != unitcount:
            self.neededslots = min(unitcount, self.MAXUNITSLOTS)
            
            if self.neededslots > self.curmax or self.neededslots < self.curmin:
                self.PerformLayout()

            for i, slot in enumerate(self.slots):
                slot.SetVisible(i < unitcount)

            self.FlushSBuffer() # Trigger Paint() in Python
            
        # Update unit images
        for i in range(0, self.neededslots):
            slot = self.slots[i]
            unit = units[i]
            if not unit:
                continue
            slot.iconimage = unit.unitinfo.image
            slot.health = unit.HealthFraction()
            slot.unit = unit
            slot.info = unit.unitinfo
            #if hasattr(unit, 'grenadeUnlocked') and unit.grenadeUnlocked:
                #print('Add image')
                #slot.smallIcon = scheme().GetImage('vgui/icons/grenade_icon', False)
                #slot.smallIcon = images.GetImage('vgui/icons/grenade_icon')
            #else:
                #slot.smallIcon = None
                

    def OnSelectionChanged(self, player, **kwargs):
        self.UpdateUnits(player.GetSelection())
            
    unitimgcolor = Color(255, 255, 255, 255)

    #: The maximum number of unit slots available in the hud
    MAXUNITSLOTS = 300
    
    curmax = 0
    spacingx = 2
    spacingy = 2
    buttonwideratio = 0.875
    
class BaseHudGarrisonUnits(BaseHudUnits):
    def __init__(self, parent, config={}):    
        super().__init__(parent, config)
        
        self.health = Label(self, 'Health', '')
        self.population = Label(self, 'Population', '')
        self.health.EnableSBuffer(False)
        self.population.EnableSBuffer(False)
        garrisonchanged.connect(self.OnGarrisonChanged)
        
    def ApplySchemeSettings(self, schemeobj):
        super().ApplySchemeSettings(schemeobj)
       
        self.health.SetBgColor(Color(200,200,200,0))
        self.health.SetFgColor(Color(0,255,0,255))
        
        self.population.SetBgColor(Color(200,200,200,0))
        self.population.SetFgColor(Color(255,255,255,255))
        
    def PerformLayout(self):
        super().PerformLayout()
        
        fonth = scheme().GetProportionalScaledValueEx(self.GetScheme(), 15)
        
        #x, y = self.GetPos()
        w, h = self.GetSize()

        self.health.SetPos(int(w*0.25), int(h*0.87))
        self.health.SetSize(int(w*1.0), fonth)
        
        self.population.SetPos(int(w*0.45), int(h*0.87))
        self.population.SetSize(int(w*1.0), fonth)
    
    def Update(self):
        super().Update()
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player or player.CountUnits() != 1:
            return
            
        unit = player.GetUnit(0)

        # Make sure to show a minimum of 1 hp (might in fact be between 0 and 1,
        # or lost precision when sending to client)
        self.health.SetText('%d / %d' % (max(1, unit.health), unit.maxhealth))
        self.population.SetText('Pop: %d / %d' % (unit.GetCurrentPopulation(), unit.maxpopulation))
        
    def UpdateOnDelete(self):
        super().UpdateOnDelete()
        
        garrisonchanged.disconnect(self.OnGarrisonChanged)
        
    def OnSelectionChanged(self, player, **kwargs):
        units = player.GetSelection()
        if not units:
            return
        building = units[0]
        if not hasattr(building, 'units'):
            return
        self.UpdateUnits(building.units)
        self.building = building
        
    def OnGarrisonChanged(self, building, **kwargs):
        self.UpdateUnits(building.units)
        
    def OnSlotLeftClick(self, slot):
        if not self.building:
            return
        engine.ServerCommand('player_ungarrison_unit %d' % (slot.unit.entindex()))
        
    def OnSlotRightClick(self, slot):
        if not self.building:
            return
        engine.ServerCommand('player_ungarrison_unit %d' % (slot.unit.entindex()))
        
    def OnUnitDoublePressed(self, unit):
        pass
        
    building = None
    
class BaseHudSingleUnit(Panel):
    """Default panel showed when you have a single unit selected.
       Shows the name, description and other statistics about the unit."""
    def __init__(self, parent, config={}):    
        super().__init__(parent, 'BaseHudSingleUnit')
        
        self.EnableSBuffer(True)
        self.SetProportional(True)
        self.SetPaintBackgroundEnabled( False )
        self.SetKeyBoardInputEnabled( False )
        self.SetMouseInputEnabled( True )
        
        self.name = Label(self, "Name", "My name")

        self.attributes = AttributeLabel(self, 'Attributes', '')
        self.attacks = Label(self, 'Attacks', '')

        self.health = Label(self, 'Health', '')
        self.energy = Label(self, 'Energy', '')
        
        self.attrinfopanel = AttributeUnitHudInfo()
        
        self.name.EnableSBuffer(False)
        self.attributes.EnableSBuffer(False)
        self.attacks.EnableSBuffer(False)
        self.health.EnableSBuffer(False)
        self.energy.EnableSBuffer(False)
        
    def ApplySchemeSettings(self, schemeobj):
        super().ApplySchemeSettings(schemeobj)
        
        self.name.SetBgColor(Color(200,200,200,0))

        self.attributes.SetFgColor(Color(200,200,200,255))
        self.attributes.SetBgColor(Color(200,200,200,0))
        self.attacks.SetFgColor(Color(200,200,200,255))
        self.attacks.SetBgColor(Color(200,200,200,0))
        
        self.health.SetBgColor(Color(200,200,200,0))
        self.energy.SetBgColor(Color(200,200,200,0))
        self.health.SetFgColor(Color(0,255,0,255))
        self.energy.SetFgColor(Color(0,0,255,255))

    def PerformLayout(self):
        super().PerformLayout()
        
        fonth = scheme().GetProportionalScaledValueEx(self.GetScheme(), 15)
        
        #x, y = self.GetPos()
        w, h = self.GetSize()
        
        insety = int(h*0.05)
        self.name.SetPos(int(w*0.01), insety)
        self.name.SetSize(int(w*1.0), fonth)

        self.attributes.SetPos(int(w*0.01), insety + fonth)
        self.attributes.SetSize(int(w*1.0), fonth)
        self.attacks.SetPos(int(w*0.01), insety + fonth * 2)
        self.attacks.SetSize(int(w*1.0), fonth)
        
        self.health.SetPos(int(w*0.01), int(h*0.77))
        self.health.SetSize(int(w*1.0), fonth)
        self.energy.SetPos(int(w*0.01), int(h*0.875))
        self.energy.SetSize(int(w*1.0), fonth)
        
    def OnShowHud(self):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player or player.CountUnits() != 1:
            return
            
        unit = player.GetUnit(0)
        info = unit.unitinfo
        attacks = getattr(unit, 'attacks', None)
        
        self.attributes.unit = unit
        self.attributes.info = info
        
        attributes = unit.GetActiveAttributes()
        attribstext = ('%s' % (' - '.join([a.name for a in iter(sorted(attributes.values(), key=attrgetter('order')))])))
        
        if getattr(info, 'maxspeed', 0) != 0:
            attribstext += ', speed: %d' % info.maxspeed
        elif hasattr(unit, 'maxspeed'):
            attribstext += ', speed: %d' % unit.maxspeed
            
        self.name.SetText(info.displayname)
        self.attributes.SetText(attribstext)
        
        if attacks:
            mainattack = attacks[0]
        else:
            mainattack = None

        attackstext = ''
            
        if mainattack:
            adjusteddamage = mainattack.damage * unit.accuracy
            if attackstext:
                attackstext += ', '
            attackstext += 'dmg: %d, firerate: %.1f rps, range: %d' % (adjusteddamage, 1/(mainattack.attackspeed) if mainattack.attackspeed > 0 else 0, int(mainattack.maxrange))
            if unit.IsUnit() and unit.unitinfo.tier is not 0:
                attackstext += ', tier: %d' % unit.unitinfo.tier
            if mainattack.usesbursts:
                avgburst = int((mainattack.minburst + mainattack.maxburst)/2.0)
                avgresttime = float((mainattack.minresttime + mainattack.maxresttime)/2.0)
                attackstext += ', burst: %d, rest time: %.1f s' % (avgburst, avgresttime)
                
        self.attacks.SetText(attackstext)
                     
    def Update(self):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player or player.CountUnits() != 1:
            return
            
        unit = player.GetUnit(0)

        # Make sure to show a minimum of 1 hp (might in fact be between 0 and 1,
        # or lost precision when sending to client)
        self.health.SetText('%d / %d' % (max(1, unit.health), unit.maxhealth))
        if unit.maxenergy != 0:
            self.energy.SetVisible(True)
            self.energy.SetText('%d / %d' % (unit.energy, unit.maxenergy))
            self.energy.SetFgColor(Color(0, 0, 255, 255))  # FIXME, shouldn't be needed here.
            self.energy.SetBgColor(Color(200, 200, 200, 0))
        else:
            self.energy.SetVisible(False)
            
    def OnSelectionChanged(self, player, **kwargs):
        self.Update()

class BaseHudSingleUnitCombat(BaseHudSingleUnit):
    def __init__(self, parent, config={}):  
        super().__init__(parent, config)
        
        self.kills = Label(self, "Kills", "")

    def ApplySchemeSettings(self, schemeobj):
        super().ApplySchemeSettings(schemeobj)

        self.kills.SetFgColor(Color(255,255,255,255))
        self.kills.SetBgColor(Color(200,200,200,0))
        
    def PerformLayout(self):
        super().PerformLayout()
        
        x, y = self.GetPos()
        w, h = self.GetSize()

        self.kills.SetPos(int(w*0.01), int(h*0.65))
        self.kills.SetSize(int(w*1.0), int(h*0.1))
        
    def Update(self):
        super().Update()
        
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player or player.CountUnits() != 1:
            return
            
        unit = player.GetUnit(0)
        self.kills.SetText('Kills: %d' % (unit.kills))
            
class HudUnitsContainer(Panel):
    """ Container for the units section in the hud.
        Shows a different panel depending on the selected units."""
    def __init__(self, parent, infopanel, config={}):
        super().__init__(parent, "HudUnitsContainer")
        
        self.config = config
    
        self.infopanel = infopanel
        self.unitpanels = defaultdict(lambda : None)
        
        self.EnableSBuffer(True)
        self.SetProportional(True)
        self.SetPaintBackgroundEnabled(False)
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(True)

        refreshhud.connect(self.OnRefreshHud)
        selectionchanged.connect(self.OnSelectionChanged)
        
        AddTickSignal(self.GetVPanel(), 350)
        
        self.OnRefreshHud()

    def UpdateOnDelete(self):
        refreshhud.disconnect(self.OnRefreshHud)
        selectionchanged.disconnect(self.OnSelectionChanged)
        
    #@profile('HudUnitsContainer.OnTick')
    def OnTick(self):
        if not self.IsVisible():
            return

        curpanel = self.unitpanels[self.curunitpanelclass]
        if curpanel:
            curpanel.Update()
            
    def RecalculateUnitPanel(self):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
            
        # Determine which panel we should show
        if player.CountUnits() == 1:
            unit = player.GetUnit(0)
            unit.UpdateUnitPanelClass()
            newunitpanelclass = unit.unitpanelclass
        else:
            newunitpanelclass = self.defaultunitpanelclass
        
        # Update panel if changed
        if newunitpanelclass != self.curunitpanelclass:
            if self.unitpanels[self.curunitpanelclass]:
                self.unitpanels[self.curunitpanelclass].SetVisible(False)
            
            self.curunitpanelclass = newunitpanelclass
            if self.curunitpanelclass:
                # Create panel if not yet initialized
                if not self.unitpanels[self.curunitpanelclass]:
                    self.unitpanels[self.curunitpanelclass] = self.curunitpanelclass(self, self.config)
                    self.unitpanels[self.curunitpanelclass].SetPos(0,0)
                    self.unitpanels[self.curunitpanelclass].SetSize(self.GetWide(),self.GetTall())
                self.unitpanels[self.curunitpanelclass].SetVisible(True)
                
        # Always update when this is called.
        self.unitpanels[self.curunitpanelclass].OnShowHud()
        self.unitpanels[self.curunitpanelclass].Update()
                
    def PerformLayout(self):
        super().PerformLayout()
        
        wide, tall = self.GetSize()
        for v in self.unitpanels.values():
            if not v:
                continue
            v.SetPos(0,0)
            v.SetSize(wide, tall)
        
    def OnRefreshHud(self, **kwargs):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
        self.OnSelectionChanged(player)
         
    def OnSelectionChanged(self, player, **kwargs):
        self.RecalculateUnitPanel()
        if self.unitpanels[self.curunitpanelclass]:
            self.unitpanels[self.curunitpanelclass].OnSelectionChanged(player)
        
    curunitpanelclass = None
    defaultunitpanelclass = BaseHudUnits
