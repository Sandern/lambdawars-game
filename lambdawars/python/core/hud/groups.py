"""HUD control-group widgets for selecting and managing unit groups.

Defines the base panel and button types that render control group slots,
respond to selection changes, and integrate with the ability info panels.
"""
from srcbase import Color
from vgui import surface, AddTickSignal, HudIcons, scheme
from vgui.controls import Panel, Label
from entities import C_HL2WarsPlayer, PLAYER_MAX_GROUPS
from gameinterface import engine
from .abilitybutton import AbilityButton
from core.signals import groupchanged

class GroupButton(AbilityButton):
    """Ability-style button representing a numbered control group slot.

    Paints the group digit overlay, updates selection hover state, and
    notifies the parent control panel when the mouse enters or leaves so
    the HUD can highlight matching units in the grid.
    """
    def __init__(self, parent, text, groupnumber, controlpanel):
        super().__init__(parent, text)
    
        self.groupnumber = groupnumber
        self.controlpanel = controlpanel
        self.SetMouseInputEnabled(True)
        self.SetZPos(-5)

    def Paint(self):
        """Paint the base ability button plus overlay the numeric group label."""
        super().Paint()
        
        self.PaintNumbers(self.numberfont, 5, 2, self.groupnumber)
        
    def ApplySchemeSettings(self, schemeobj):
        """Cache the scheme font so digit overlays match the HUD style."""
        super().ApplySchemeSettings(schemeobj)
        
        self.numberfont = schemeobj.GetFont('Default')
        
    def PaintNumbers(self, font, xpos, ypos, value):
        """Paints a number at the specified position.
        
        Sets the draw color/font, moves the text draw position, and renders the
        provided value using those settings.
        
        Args:
            font: VGUI font handle used to draw the text.
            xpos (int): X coordinate inside the button.
            ypos (int): Y coordinate inside the button.
            value (int): Number/string to render.
        """
        surface().DrawSetTextColor(self.numbercolor)
        surface().DrawSetTextFont(font)

        # adjust the position to take into account 3 characters
        surface().DrawSetTextPos(xpos, ypos)
        surface().DrawUnicodeString(str(value))
        
    def OnCursorEntered(self):
        """Notify the parent panel so it can highlight matching units."""
        super().OnCursorEntered()
        self.controlpanel.OnCursorEnteredButton(self)
        
    def OnCursorExited(self):
        """Notify the parent panel when the cursor leaves this group slot."""
        super().OnCursorExited()
        self.controlpanel.OnCursorExitedButton(self)
        
    numbercolor = Color(255, 255, 255, 200)
    
class BaseHudGroups(Panel):
    """Base panel for displaying control group buttons in the HUD.
    
    Manages a row of buttons representing numbered control groups (1-9).
    Each button shows the icon of the first unit in that group and allows
    selecting the group by clicking. Updates automatically when groups change.
    """
    def __init__(self, parent, config={}):
        """Initialize the horizontal row of group buttons using HUD skin data."""
        super().__init__(parent, "HudGroups")
        
        self.SetMouseInputEnabled(True)
        self.SetPaintEnabled(False)
        self.SetPaintBackgroundEnabled(False)
        self.SetZPos(-5)
        
        self.buttontexture = config.get('groups_button', 'hud_rebels_groupbutton')
        
        # Create build queue buttons
        self.slots = []
        for i in range(0, PLAYER_MAX_GROUPS):
            self.slots.append( self.CreateGroupButton('group_'+str(i), i+1) )
            
        groupchanged.connect(self.OnGroupChanged)

    def UpdateOnDelete(self):
        """Disconnect signals and delete any spawned group buttons."""
        groupchanged.disconnect(self.OnGroupChanged)
        for slot in self.slots:
            slot.DeletePanel()
        self.slots = []
            
    def SetVisible(self, visible):
        """Show/hide buttons and refresh icons when re-enabled."""
        super().SetVisible(visible)
        
        if not visible:
            for slot in self.slots:
                slot.SetVisible(visible)
        else:
            player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer() 
            if player:
                for slot in self.slots:
                    self.OnGroupChanged(player, slot.groupnumber-1)
        
    def OnGroupChanged(self, player, group, **kwargs):
        """Handle when a control group changes.
        
        Updates the group button visibility and icon based on whether
        the group has units. Shows the first unit's icon if the group
        has units, hides the button if empty.
        
        Args:
            player: Player entity.
            group (int): Group number (0-based).
        """
        try:
            slot = self.slots[group]
        except IndexError:
            print('BaseHudGroups.OnGroupChanged: Invalid group %d' % (group))
            return
        
        numunits = player.CountGroup(group)
        if numunits > 0:
            unit = player.GetGroupUnit(group, 0)
            slot.SetVisible(True)
            if not unit:
                return
            slot.iconimage = unit.unitinfo.image
            slot.SetVisible(True)
        else:
            slot.SetVisible(False)
            
    def CreateGroupButton(self, command, group):
        """Create a new control group button.
        
        Args:
            command (str): Command string to execute when clicked.
            group (int): Group number (1-based).
            
        Returns:
            GroupButton: The created button instance.
        """
        slot = GroupButton(self.GetParent(), command, group, self)
        slot.iconcoords = self.buttoniconcoords
        slot.SetAllImages(HudIcons().GetIcon(self.buttontexture), Color(255, 255, 255, 255) )
        slot.SetOverlayImage(slot.BUTTON_ENABLED_MOUSE_OVER, HudIcons().GetIcon(self.buttontexturehover), Color(255, 255, 255, 255))
        slot.SetOverlayImage(slot.BUTTON_PRESSED, HudIcons().GetIcon(self.buttontextureselected), Color(255, 255, 255, 255))
        slot.SetCommand(command)
        slot.AddActionSignalTarget(self)
        slot.SetMouseInputEnabled(True)
        slot.SetVisible(False)
        return slot
        
    def PerformLayout(self):
        """Setup the unit buttons horizontally with proportional spacing."""
        super().PerformLayout()
        
        width, tall = self.GetSize()
        
        spacingx = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.spacingx) 

        buttonwidth = int(tall*self.buttonwideratio)
        
        width = (buttonwidth+spacingx) * PLAYER_MAX_GROUPS
        self.SetWide(width)
        
        x, y = self.LocalToScreen(0,0)
        
        for i in range(0, PLAYER_MAX_GROUPS):
            self.slots[i].SetSize(buttonwidth, tall)
            self.slots[i].SetPos(x+i*buttonwidth+i*spacingx, y)

    def OnCommand(self, command):
        """Handle control group button click commands.
        
        Selects the control group when a group button is clicked.
        
        Args:
            command (str): Command string in format 'group_N'.
        """
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer() 
        splitted = command.split('_')
        if splitted[0] == 'group':
            group = int(splitted[1])
            player.SelectGroup(group)
            engine.ServerCommand( 'select_group %d ' % (group) )
            return
        raise Exception('Unknown command ' + command)
        
    def OnCursorEnteredButton(self, button):
        """Handle when mouse enters a group button.
        
        Args:
            button: GroupButton that was entered.
        """
        pass
        
    def OnCursorExitedButton(self, button):
        """Handle when mouse exits a group button.
        
        Args:
            button: GroupButton that was exited.
        """
        pass
    
    buttontextureselected = 'hud_classic_button_selected'
    buttontexturehover = 'hud_classic_button_hover'
    buttoniconcoords = (0.1, 0.1, 0.8, 0.8) # X, Y, Wide, Tall 
    buttonwideratio = 0.905263158
    spacingx = 2
        