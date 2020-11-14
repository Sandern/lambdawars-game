from srcbase import Color
from vgui import surface, AddTickSignal, HudIcons, scheme
from vgui.controls import Panel, Label
from entities import C_HL2WarsPlayer, PLAYER_MAX_GROUPS
from gameinterface import engine
from .abilitybutton import AbilityButton
from core.signals import groupchanged

class GroupButton(AbilityButton):
    def __init__(self, parent, text, groupnumber, controlpanel):
        super().__init__(parent, text)
    
        self.groupnumber = groupnumber
        self.controlpanel = controlpanel
        self.SetMouseInputEnabled(True)
        self.SetZPos(-5)

    def Paint(self):
        super().Paint()
        
        self.PaintNumbers(self.numberfont, 5, 2, self.groupnumber)
        
    def ApplySchemeSettings(self, schemeobj):
        super().ApplySchemeSettings(schemeobj)
        
        self.numberfont = schemeobj.GetFont('Default')
        
    def PaintNumbers(self, font, xpos, ypos, value):
        """ Paints a number at the specified position """
        surface().DrawSetTextColor(self.numbercolor)
        surface().DrawSetTextFont(font)

        # adjust the position to take into account 3 characters
        surface().DrawSetTextPos(xpos, ypos)
        surface().DrawUnicodeString(str(value))
        
    def OnCursorEntered(self):
        super().OnCursorEntered()
        self.controlpanel.OnCursorEnteredButton(self)
        
    def OnCursorExited(self):
        super().OnCursorExited()
        self.controlpanel.OnCursorExitedButton(self)
        
    numbercolor = Color(255, 255, 255, 200)
    
class BaseHudGroups(Panel):
    """ Generic panel for group buttons.
        
    """
    def __init__(self, parent, config={}):
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
        groupchanged.disconnect(self.OnGroupChanged)
        for slot in self.slots:
            slot.DeletePanel()
        self.slots = []
            
    def SetVisible(self, visible):
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
        """ Setup the unit buttons """
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
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer() 
        splitted = command.split('_')
        if splitted[0] == 'group':
            group = int(splitted[1])
            player.SelectGroup(group)
            engine.ServerCommand( 'select_group %d ' % (group) )
            return
        raise Exception('Unknown command ' + command)
        
    def OnCursorEnteredButton(self, button): pass
    def OnCursorExitedButton(self, button): pass
    
    buttontextureselected = 'hud_classic_button_selected'
    buttontexturehover = 'hud_classic_button_hover'
    buttoniconcoords = (0.1, 0.1, 0.8, 0.8) # X, Y, Wide, Tall 
    buttonwideratio = 0.905263158
    spacingx = 2
        