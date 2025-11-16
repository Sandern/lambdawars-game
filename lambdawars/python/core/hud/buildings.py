"""HUD widgets for building production queues and construction status.

Provides panels and buttons used to display building production queues,
construction progress, and related ability information on the HUD.
"""
from srcbase import Color
from vgui import images, surface, scheme, XRES, YRES, vgui_input
from vgui.controls import Panel, Label, BitmapButton
from entities import C_HL2WarsPlayer
from gameinterface import engine

from .units import BaseHudSingleUnit
from .infobox import QueueUnitHudInfo

class BuildQueueButton(BitmapButton):
    """Button representing a queued unit/structure with count and progress.

    Draws the production count, build progress overlay, and forwards hover
    events to show the related ability information panel.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.EnableSBuffer(False)
        
    def Paint(self):
        super(BuildQueueButton,self).Paint()
        
        # Draw the amount of units
        if self.amount > 0:
            self.PaintNumbers(self.numberfont, 8, 5, self.amount)
            
        unit = self.unit
        if not unit:
            return

        # Draw the build progress
        if unit.nextcompletiontime and unit.buildtime > 0:
            w, h = self.GetSize()
            
            self.weight = 1.0 - unit.GetBuildProgress()
            surface().DrawSetColor(self.progresscolor)
            surface().DrawFilledRect(0, 0, int(w*self.weight), h)

    def ApplySchemeSettings(self, schemeobj):
        super().ApplySchemeSettings(schemeobj)
        
        self.numberfont = schemeobj.GetFont('Default')
        
    def PaintNumbers(self, font, xpos, ypos, value):
        """Paint a number at the specified position.
        
        Args:
            font: Font to use for drawing.
            xpos (int): X position.
            ypos (int): Y position.
            value (int): Number to display.
        """
        surface().DrawSetTextColor(self.amountcolor)
        surface().DrawSetTextFont(font)

        # adjust the position to take into account 3 characters
        surface().DrawSetTextPos(xpos, ypos)
        surface().DrawUnicodeString(str(value))
        
    def OnCursorEntered(self):
        super().OnCursorEntered()
        self.ShowAbility()

    def OnCursorExited(self):
        super().OnCursorExited()
        self.HideAbility()
        
    def ShowAbility(self):
        """Show ability information panel when hovering over this queue slot.
        
        Displays the ability info panel at the cursor position with details
        about the queued ability.
        """
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
        """Hide the ability information panel.
        
        Called when mouse cursor leaves the queue slot.
        """
        infopanel = self.GetParent().infopanel
        infopanel.HideAbility()
        infopanel.unit = None
        
    progresscolor = Color(0, 0, 200, 100)
    amountcolor = Color(255, 255, 255, 200)
    weight = 0.0
    
    unit = None
    info = None
        
    _amount = 0
    @property
    def amount(self): 
        return self._amount
    @amount.setter
    def amount(self, amount): 
        self._amount = amount
        self.FlushSBuffer()
    _amount = 0
    
white = Color(255, 255, 255, 255)
    
class HudBuildQueue(Panel):
    """HUD panel for displaying building production queues.
    
    Shows the production queue for a selected building, including queued
    units/abilities, build progress, health, and energy. Displays ability
    information when hovering over queue slots.
    """
    def __init__(self, parent, config):
        super().__init__(parent, "HudBuildQueue")
        
        self.SetPaintBackgroundEnabled(False)
        
        # Create build queue buttons
        self.slots = []
        for i in range(0, self.BUILDQUEUEBUTTONS):
            self.slots.append( self.CreateButtonQueue('queue_'+str(i)) )
            
        self.name = Label(self, "Name", "My name")
        self.health = Label(self, 'Health', '')
        self.energy = Label(self, 'Energy', '')
        
        self.infopanel = QueueUnitHudInfo()
        
    def UpdateOnDelete(self):
        """Clean up the floating info panel when this HUD element is removed."""
        if self.infopanel:
            self.infopanel.DeletePanel()
        
    def CreateButtonQueue(self, command):
        """Create a new queue button for the production queue.
        
        Args:
            command (str): Command string to execute when clicked.
            
        Returns:
            BuildQueueButton: The created button instance.
        """
        slot = BuildQueueButton(self, command)
        slot.SetOverlayImage(slot.BUTTON_ENABLED_MOUSE_OVER, images.GetImage("VGUI/button_hover"), Color(255, 255, 255, 255))
        slot.SetOverlayImage(slot.BUTTON_PRESSED, images.GetImage("VGUI/button_selected"), Color(255, 255, 255, 255))
        slot.SetCommand(command)
        slot.AddActionSignalTarget(self)
        slot.SetMouseInputEnabled(True)
        slot.SetVisible(True)
        return slot
        
    def OnShowHud(self):
        """Called when this HUD section becomes visible (currently no-op)."""
        pass
        
    def Update(self):
        """Update the build queue display with current building state.
        
        Refreshes queue slots, unit counts, build progress, and building
        health/energy information for the currently selected building.
        """
        if self.IsVisible() == False:
            return
            
        # Retrieve the building 
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if player == None or player.CountUnits() == 0:
            self.slots[0].nextcompletiontime = None
            return
        
        unit = player.GetUnit(0).Get()
        if not unit or not unit.isbuilding:
            return
        
        # Show construction queue
        for i, slot in enumerate(self.slots):
            slot.amount = unit.buildamount[i]
            if unit.buildtypes[i] is None:
                slot.SetAllImages(images.GetImage('vgui/units/unit_none.vmt'), white)
                slot.info = None
                slot.unit = None
            else:
                info = unit.unitinfo.GetAbilityInfo(unit.buildtypes[i], unit.GetOwnerNumber())
                slot.SetAllImages(info.image, white)
                slot.info = info
                
                if i == 0:
                    slot.unit = unit
                else:
                    slot.unit = None
                    
        # General info
        info = unit.unitinfo
        self.name.SetText(info.displayname)

        self.health.SetText('%d / %d' % (unit.health, unit.maxhealth))
        if unit.maxenergy != 0:
            self.energy.SetVisible(True)
            self.energy.SetText('%d / %d' % (unit.energy, unit.maxenergy))
            self.energy.SetFgColor(Color(0,0,255,255)) # FIXME, shouldn't be needed here.
            self.energy.SetBgColor(Color(200,200,200,0))
        else:
            self.energy.SetVisible(False)
            
    def ApplySchemeSettings(self, schemeobj):
        super().ApplySchemeSettings(schemeobj)

        self.name.SetBgColor(Color(200,200,200,0))
        self.health.SetBgColor(Color(200,200,200,0))
        self.energy.SetBgColor(Color(200,200,200,0))
        self.health.SetFgColor(Color(0,255,0,255))
        self.energy.SetFgColor(Color(0,0,255,255))
        
    def PerformLayout(self):
        """Arrange the queue buttons plus label positions inside the panel."""
        super().PerformLayout()
        
        width, tall = self.GetSize()

        cyclesize = 0
        buttonsize = YRES(30)
        
        xoffset = XRES(35)
        yoffset = YRES(25)
        
        for i, slot in enumerate(self.slots):
            slot.SetSize(buttonsize, buttonsize)
            slot.SetPos(xoffset + cyclesize + buttonsize * i, yoffset)

        #self.cyclebuttons[0].SetSize( cyclesize, cyclesize )
        #self.cyclebuttons[0].SetPos( 0, 0 )
        #self.cyclebuttons[1].SetSize( cyclesize, cyclesize )
        #self.cyclebuttons[1].SetPos( 0, cyclesize )
        
        x, y = self.GetPos()
        w, h = self.GetSize()
        self.name.SetPos(xoffset+int(w*0.01), int(h*0.05))
        self.name.SetSize(int(w*1.0), int(h*0.1))
        
        self.health.SetPos(int(w*0.01), int(h*0.77))
        self.health.SetSize(int(w*1.0), int(h*0.075))
        self.energy.SetPos(int(w*0.01), int(h*0.875))
        self.energy.SetSize(int(w*1.0), int(h*0.075))
        
    def OnCommand(self, command):
        """Send commands to the server when the player clicks queue slots."""
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer() 
        splitted = command.split('_')
        if splitted[0] == 'queue':
            slot = int(splitted[1])
            engine.ClientCommand( 'player_queue %d ' % (slot) )
            return
        raise Exception('Unknown command ' + command)
        
    def OnSelectionChanged(self, player, **kwargs):
        """Refresh queue display whenever the player's selection changes."""
        self.Update()
        
    # Settings
    BUILDQUEUEBUTTONS = 5

class HudBuildSingleUnit(BaseHudSingleUnit):
    """HUD panel for displaying single building information.
    
    Shows building details including resource generation limits for
    buildings that generate resources over time.
    """
    def __init__(self, parent, config):
        super().__init__(parent, config)
        
        self.resourcesleft = Label(self,"Progress","")
        self.resourcesleft.SetBgColor(Color(0,0,0,0))
        self.resourcesleft.SetPaintBackgroundEnabled(False)
        self.resourcesleft.SetPaintBorderEnabled(False)
        self.resourcesleft.SetContentAlignment(Label.a_west)
        self.resourcesleft.SetVisible(False)
    
    def ApplySchemeSettings(self, scheme_obj):
        super().ApplySchemeSettings(scheme_obj)

        self.resourcesleft.SetFgColor(Color(255,255,255,255))

    def OnShowHud(self):
        """Make resource-left label visible only for generators with tracking."""
        super().OnShowHud()
    
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player or player.CountUnits() != 1:
            return
        unit = player.GetUnit(0).Get()       
        if not unit.isbuilding or not unit.generateresources:
            return
        
        resourcetype = unit.generateresources['type']
        self.resourcesleft.SetVisible(resourcetype in unit.resourcesleft)
                
    def Update(self):
        """Update base panel info plus remaining resource readout."""
        super().Update()
        
        if self.resourcesleft.IsVisible():
            # Retrieve the building 
            player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
            if not player or player.CountUnits() == 0:
                return
            unit = player.GetUnit(0).Get()       
            if not unit.isbuilding or not unit.generateresources:
                return

            resourcetype = unit.generateresources['type']
            maxgenerate = unit.resourcesleft.get(resourcetype, 0)
            self.resourcesleft.SetText('Max left: %s' % (str(int(maxgenerate))))
        
    def PerformLayout(self):
        """Align the 'resources left' label under the main stats block."""
        super().PerformLayout()
        
        w, h = self.GetSize()
        self.resourcesleft.SetPos(int(0.02 * w), int(0.55 * h))
        self.resourcesleft.SetSize(w-int(0.1 * w), scheme().GetProportionalScaledValueEx(self.GetScheme(), 20))
    
class HudBuildConstruction(BaseHudSingleUnit):
    """HUD panel for displaying building construction progress.
    
    Shows the construction progress percentage for buildings that are
    currently being built or upgraded.
    """
    def __init__(self, parent, config):
        super().__init__(parent, config)

        self.constructionstate = Label(self,"Progress","")
        self.constructionstate.SetBgColor(Color(0,0,0,0))
        self.constructionstate.SetPaintBackgroundEnabled(False)
        self.constructionstate.SetPaintBorderEnabled(False)
        self.constructionstate.SetContentAlignment(Label.a_west)
        self.constructionstate.SetVisible(True)
        
    def ApplySchemeSettings(self, scheme_obj):
        super().ApplySchemeSettings(scheme_obj)

        self.constructionstate.SetFgColor(Color(255,255,255,255))

    def Update(self):
        """Update base stats and show the latest construction percentage."""
        super().Update()
        
        # Retrieve the building 
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player or player.CountUnits() == 0:
            return
        unit = player.GetUnit(0).Get()       
        if not unit.isbuilding:
            return
        self.constructionstate.SetText('Construction Progress: %s' % (str(int(unit.constructprogress*100))))
        
    def PerformLayout(self):
        """Position the construction progress label relative to panel size."""
        super().PerformLayout()
        
        w, h = self.GetSize()
        self.constructionstate.SetPos(int(0.02 * w), int(0.55 * h))
        self.constructionstate.SetSize(w-int(0.1 * w), scheme().GetProportionalScaledValueEx(self.GetScheme(), 20))
