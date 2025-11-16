"""HUD Abilities panel for Lambda Wars.

Provides UI for displaying and interacting with unit and player abilities.
"""
from srcbase import Color
from vgui import surface, AddTickSignal, HudIcons, scheme
from vgui.controls import Panel
from entities import C_HL2WarsPlayer
from gameinterface import engine
from .abilitybutton import AbilityButton
from input import MOUSE_RIGHT

from core.abilities import SendAbilityMenuChanged, ClientDoAbility, GetTechNode
from core.units import GetUnitInfo
from core.signals import selectionchanged, abilitymenuchanged, refreshhud, resourceset

class AbilitySectionButton(AbilityButton):
    """Button for displaying individual ability slots in the abilities panel.
    
    Extends AbilityButton to show recharge progress overlay and handle
    ability information display on hover.
    """
    def ApplySchemeSettings(self, scheme):
        """Strip borders so the slot artwork occupies the full button area."""
        super().ApplySchemeSettings(scheme)
        self.SetBorder(None)
    
    #@profile('AbilitySectionButton.Paint')
    def Paint(self):
        """Draw the underlying button art and a cooldown overlay if needed."""
        super().Paint()
        if not self.rechargecomplete or self.rechargecomplete == float("inf") or self.rechargetime == 0:
            return
            
        w, h = self.GetSize()
        
        weight = (self.rechargecomplete-gpGlobals.curtime) / self.rechargetime

        # draw how much health we still got
        surface().DrawSetColor(Color(0, 0, 200, 100))
        surface().DrawFilledRect(0, 0, int(w * weight), h)
            
    def OnCursorEntered(self):
        """Show the tooltip and force a tick so the data is current."""
        super().OnCursorEntered()
        self.ShowAbility()
        self.GetParent().OnTick() # Do an extra tick to update infobox for now 
        
    def OnCursorExited(self):
        """Hide the tooltip when the cursor leaves the ability slot."""
        super().OnCursorExited()
        self.HideAbility()
        
    def ShowAbility(self):
        """Show ability information panel when hovering over this button.
        
        Displays the ability info panel with details about the ability
        in this slot.
        """
        if self.info:
            infopanel = self.GetParent().infopanel
            infopanel.MoveToDefault()
            infopanel.ShowAbility(self.info, self.slot, contextpanel=self)

    def HideAbility(self):
        """Hide the ability information panel.
        
        Called when mouse cursor leaves the button.
        """
        self.GetParent().infopanel.HideAbility()
        
    rechargecomplete = None
    rechargetime = None
    
    info = None

class BaseHudAbilities(Panel):
    """Base panel for displaying unit abilities in the HUD.
    
    Manages a grid of ability buttons that display available abilities
    for the selected unit type. Handles ability availability, recharge
    states, autocast indicators, and ability execution.
    """
    def __init__(self, parent, infopanel, config={}):
        super().__init__(parent, "HudAbilities")
        
        self.buttontexture = config.get('ability_button_enabled', 'hud_rebels_button_enabled')
        self.buttontexturedisabled = config.get('ability_button_disabled', 'hud_rebels_button_disabled')
        self.buttontextureselected = config.get('ability_button_pressed', 'hud_rebels_button_pressed')
        self.buttontexturehover = config.get('ability_button_hover', 'hud_rebels_button_hover')
        self.buttonautocastoverlaytexture = config.get('ability_button_autocastoverlay', 'hud_rebels_button_autocastoverlay')
        self.buttonautocastoverlayofftexture = config.get('ability_button_autocastoverlay_off', 'hud_rebels_button_autocastoverlay_off')
        self.buttoniconcoords = config.get('ability_button_iconcoords', (0.1, 0.1, 0.8, 0.8)) # X, Y, Wide, Tall 
        
        self.EnableSBuffer(True)
        self.SetProportional(True)
        self.SetPaintBackgroundEnabled(False)
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(True)    

        self.infopanel = infopanel
        
        # Create buttons
        self.slots = []
        nslots = self.nslotsx * self.nslotsy
        for i in range(0, nslots):
            namecommand = 'abilityslot_'+ str(i)
            namecommand2 = 'abilityslotright_'+ str(i)
            slot = AbilitySectionButton(self, namecommand)
            slot.iconcoords = self.buttoniconcoords
            slot.SetAllImages(HudIcons().GetIcon(self.buttontexture), Color(255, 255, 255, 255))
            if self.buttontexturedisabled:
                slot.SetImage(slot.BUTTON_DISABLED, HudIcons().GetIcon(self.buttontexturedisabled), Color(255, 255, 255, 255))
            if self.buttontexturehover:
                slot.SetImage(slot.BUTTON_ENABLED_MOUSE_OVER, HudIcons().GetIcon(self.buttontexturehover), Color(255, 255, 255, 255))
            if self.buttontextureselected:
                slot.SetImage(slot.BUTTON_PRESSED, HudIcons().GetIcon(self.buttontextureselected), Color(255, 255, 255, 255))
            slot.SetCommand(namecommand)
            slot.SetCommandRightClick(namecommand2)
            slot.SetMouseClickEnabled(MOUSE_RIGHT, True) # Default is left only
            slot.AddActionSignalTarget(self)
            slot.SetMouseInputEnabled(True)
            slot.SetVisible(False)
            slot.slot = i
            self.slots.append(slot)
            
        selectionchanged.connect(self.OnSelectionChanged)
        abilitymenuchanged.connect(self.OnAbilityMenuChanged)
        refreshhud.connect(self.OnRefreshHud)
        resourceset.connect(self.OnRefreshHud)
            
        AddTickSignal(self.GetVPanel(), 350)
        
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if player:
            self.OnSelectionChanged(player)
        
    def SetVisible(self, visible):
        """Ensure the infopanel hides when the ability grid itself is hidden."""
        super().SetVisible(visible)
        if not visible and self.infopanel:
            self.infopanel.HideAbility()
        
    def UpdateOnDelete(self):
        """Disconnect HUD signals when the panel is destroyed/reloaded."""
        selectionchanged.disconnect(self.OnSelectionChanged)
        abilitymenuchanged.disconnect(self.OnAbilityMenuChanged)
        refreshhud.disconnect(self.OnRefreshHud)
        resourceset.disconnect(self.OnRefreshHud)
        self.infopanel = None
        
    def PerformLayout(self):      
        """Compute slot dimensions from proportional margins and place buttons. Sets up the ability buttons."""
        super().PerformLayout()
        
        margintop = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.margintop) 
        marginbottom = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.marginbottom) 
        marginleft = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.marginleft) 
        marginright = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.marginright) 
        
        w, h = self.GetSize()
        sizex = int((w-marginleft-marginright) / self.nslotsx)
        sizey = int((h-margintop-marginbottom) / self.nslotsy)

        # Set size and position for each button
        for y in range(0, self.nslotsy):
            for x in range(0, self.nslotsx):
                self.slots[x+y*self.nslotsx].SetSize(sizex, sizey)
                self.slots[x+y*self.nslotsx].SetPos(marginleft+x*sizex, margintop+y*sizey)
                
    #@profile('BaseHudAbilities.OnTick')
    def OnTick(self):
        """Update ability buttons on each tick.
        
        Refreshes enabled/disabled states and recharge progress overlays
        for all ability buttons based on current unit selection and ability
        recharge times.
        """
        if not self.IsVisible():
            return
            
        super().OnTick()
        
        if not self.activeunitinfo:
            return
        
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer() 
        if not player:
            return

        # Set abilities
        # TODO: only need to do this per tick atm because of the recharge time
        #       Would be nice to make it signal based.
        for slot in self.slots:
            info = slot.info
            if not info:
                continue
            
            # Can we do this ability? Set enabled/disabled
            # The image depends on it
            cando, rechargecomplete = self.CalculateCanDoAbility(info, player)
            if cando:
                slot.SetEnabled(True)
                slot.rechargecomplete = None
            else:
                slot.SetEnabled(False)
                slot.rechargecomplete = rechargecomplete
                slot.rechargetime = info.rechargetime

    def GetActiveUnitInfo(self):
        """Get the unit info for the currently selected unit type.
        
        Returns:
            UnitInfo: Unit info object for the selected unit type, or None
                     if no unit is selected.
        """
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer() 
        if not player:
            return None
        # Should always have unit info ( fallback is unit_unknown )
        highlight_unittype = player.GetSelectedUnitType()
        if not highlight_unittype:
            return None
        unitinfo = GetUnitInfo(highlight_unittype, fallback=None)
        return unitinfo
        
    def AbilityInUnits(self, info, units):
        """Check if any of the given units have this ability.
        
        Args:
            info: AbilityInfo to check for.
            units: List of unit entities.
            
        Returns:
            bool: True if at least one unit has the ability, False otherwise.
        """
        for unit in units:
            if info.name in unit.abilitiesbyname:
                return True
        return False
        
    def HasUnitAutocastOn(self, info, units):
        """Check if any unit has autocast enabled for this ability.
        
        Args:
            info: AbilityInfo to check autocast for.
            units: List of unit entities.
            
        Returns:
            bool: True if at least one unit has autocast enabled, False otherwise.
        """
        if not info.supportsautocast:
            return False
        for unit in units:
            if info.name not in unit.abilitiesbyname:
                continue
            if unit.abilitycheckautocast[info.uid]:
                return True
        return False
        
    def RefreshSlots(self):
        """Refresh all ability slots with current selection state.
        
        Updates button visibility, icons, enabled/disabled states, and
        autocast indicators based on the currently selected units and
        their available abilities.
        """
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer() 
        if not player:
            return
        
        self.activeunitinfo = self.GetActiveUnitInfo()
        hlmin, hlmax = player.GetSelectedUnitTypeRange()
        units = player.GetSelection()[hlmin:hlmax]
        unit = units[0] if units else None #player.GetUnit(self.hlmin) if self.hlmin >= 0 else None
        self.activeownernumber = player.GetOwnerNumber()

        # Hide everything if there is no unit type or if we selected another player's unit
        if not self.activeunitinfo or not unit or not unit.CanPlayerControlUnit(player):
            for slot in self.slots:
                slot.SetVisible(False)
                slot.info = None
            return
            
        # Retrieve the active hud abilities map
        abilitiesmap = player.hudabilitiesmap[-1] if getattr(player, 'hudabilitiesmap', None) else self.activeunitinfo.abilities
            
        # Set abilities
        for i, slot in enumerate(self.slots):
            try:
                info = self.activeunitinfo.GetAbilityInfo(abilitiesmap[i], self.activeownernumber)
            except KeyError:
                slot.SetVisible(False)
                continue
                
            if not info or not self.AbilityInUnits(info, units):
                slot.SetVisible(False)
                continue
                
            technode = GetTechNode(info, self.activeownernumber)
            if not technode.available and not technode.showonunavailable:
                slot.SetVisible(False)
                continue
                
            slot.SetVisible(True)
            slot.info = info
            
            # Can we do this ability? Set enabled/disabled
            # The image depends on it
            cando, rechargecomplete = self.CalculateCanDoAbility(info, player)
            if cando:
                slot.SetEnabled(True)
                if slot.IsCursorOver():
                    slot.SetArmed(True)
                slot.iconimage = info.image
                slot.rechargecomplete = None
            else:
                slot.SetEnabled(False)
                slot.SetArmed(False)
                slot.iconimage = info.image_dis
                slot.rechargecomplete = rechargecomplete
                slot.rechargetime = info.rechargetime
                
            if self.buttonautocastoverlaytexture and self.HasUnitAutocastOn(info, units):
                slot.SetAutocastOverlayImage(HudIcons().GetIcon(self.buttonautocastoverlaytexture))
            elif info.supportsautocast:
                slot.SetAutocastOverlayImage(HudIcons().GetIcon(self.buttonautocastoverlayofftexture))
            else:
                slot.SetAutocastOverlayImage(None)
            
            if slot.IsCursorOver():
                slot.ShowAbility()
                
        
    def CalculateCanDoAbility(self, info, player):
        """Calculate if the ability can be used and when it will be ready.
        
        Checks all selected units to see if any can use the ability.
        If none can, returns the earliest recharge completion time.
        
        Args:
            info: AbilityInfo to check.
            player: Player entity.
            
        Returns:
            tuple: (can_do (bool), recharge_complete_time (float))
        """
        minrechargecomplete = float('inf')
        
        for unit in player.GetSelection():
            if info.name not in unit.abilitiesbyname:
                continue
            if info.CanDoAbility(player, unit=unit):
                return True, 0.0
            try:
                if unit.abilitynexttime[info.uid] < minrechargecomplete:
                    minrechargecomplete = unit.abilitynexttime[info.uid]
            except KeyError:
                minrechargecomplete = 0
        return False, minrechargecomplete    
    
    def OnCommand(self, command):
        """Handle ability button click commands.
        
        Executes the ability on left click or toggles autocast on right click.
        
        Args:
            command (str): Command string in format 'abilityslot_N' or 'abilityslotright_N'.
        """
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        hlmin, hlmax = player.GetSelectedUnitTypeRange()
        splitted = command.split('_')
        unit = player.GetUnit(hlmin)
        unitinfo = unit.unitinfo
        slot = int(splitted[1])
        
        # Retrieve the active hud abilities map
        abilitiesmap = player.hudabilitiesmap[-1] if getattr(player, 'hudabilitiesmap', None) else unitinfo.abilities
        info = unitinfo.GetAbilityInfo(abilitiesmap[slot], unit.GetOwnerNumber())

        if splitted[0] == 'abilityslot':
            ClientDoAbility(player, info, unitinfo.name)
            return
        elif splitted[0] == 'abilityslotright':
            engine.ServerCommand('player_abilityalt %s' % (info.name))
            return
        raise Exception('Unknown command ' + command)
        
    def OnSelectionChanged(self, player, **kwargs):
        """Handle when unit selection changes.
        
        Updates the selected unit type and refreshes ability slots to
        show abilities for the newly selected unit type.
        
        Args:
            player: Player entity.
        """
        # Update highlighted units area
        unitcount = player.CountUnits()
        if unitcount == 0:
            if player.GetSelectedUnitType():
                player.SetSelectedUnitType(None)
            player.hudabilitiesmap = []
            SendAbilityMenuChanged()
        else:
            if player.GetSelectedUnitType() != player.GetUnit(0).GetUnitType():
                player.SetSelectedUnitType(player.GetUnit(0).GetUnitType())
                player.hudabilitiesmap = []
                SendAbilityMenuChanged()
        
        self.RefreshSlots()
        self.OnTick() # Extra tick to make changes look smooth
        
    def OnAbilityMenuChanged(self, **kwargs):
        """Handle when the ability menu structure changes.
        
        Refreshes ability slots when entering/exiting sub-menus.
        """
        self.RefreshSlots()
        self.OnTick() # Extra tick to make changes look smooth
        
    def OnRefreshHud(self, **kwargs):
        """Handle HUD refresh signal.
        
        Refreshes ability slots when resources or other game state changes.
        """
        self.RefreshSlots()
        self.OnTick() # Extra tick to make changes look smooth

    margintop = 0
    marginbottom = 0
    marginleft = 0
    marginright = 0
    
    nslotsx = 4
    nslotsy = 3
    
    activeunitinfo = None
    activeownernumber = None
    
    