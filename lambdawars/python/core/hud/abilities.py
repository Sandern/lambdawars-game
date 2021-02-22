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
    def ApplySchemeSettings(self, scheme):
        super().ApplySchemeSettings(scheme)
        
        self.SetBorder(None)
    
    #@profile('AbilitySectionButton.Paint')
    def Paint(self):
        super().Paint()
        if not self.rechargecomplete or self.rechargecomplete == float("inf") or self.rechargetime == 0:
            return
            
        w, h = self.GetSize()
        
        weight = (self.rechargecomplete-gpGlobals.curtime) / self.rechargetime

        # draw how much health we still got
        surface().DrawSetColor(Color(0, 0, 200, 100))
        surface().DrawFilledRect(0, 0, int(w * weight), h)
        surface().DrawFilledRect(0, 0, 0, h)
            
    def OnCursorEntered(self):
        super().OnCursorEntered()
        self.ShowAbility()
        self.GetParent().OnTick() # Do an extra tick to update infobox for now 
        
    def OnCursorExited(self):
        super().OnCursorExited()
        self.HideAbility()
        
    def ShowAbility(self):
        if self.info:
            infopanel = self.GetParent().infopanel
            infopanel.MoveToDefault()
            infopanel.ShowAbility(self.info, self.slot, contextpanel=self)

    def HideAbility(self):
        self.GetParent().infopanel.HideAbility()
        
    rechargecomplete = None
    rechargetime = None
    
    info = None

class BaseHudAbilities(Panel):
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
        super().SetVisible(visible)
        if not visible and self.infopanel:
            self.infopanel.HideAbility()
        
    def UpdateOnDelete(self):
        selectionchanged.disconnect(self.OnSelectionChanged)
        abilitymenuchanged.disconnect(self.OnAbilityMenuChanged)
        refreshhud.disconnect(self.OnRefreshHud)
        resourceset.disconnect(self.OnRefreshHud)
        self.infopanel = None
        
    def PerformLayout(self):      
        """ Setup the abilities buttons """
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
        for unit in units:
            if info.name in unit.abilitiesbyname:
                return True
        return False
        
    def HasUnitAutocastOn(self, info, units):
        if not info.supportsautocast:
            return False
        for unit in units:
            if info.name not in unit.abilitiesbyname:
                continue
            if unit.abilitycheckautocast[info.uid]:
                return True
        return False
        
    def RefreshSlots(self):
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
        self.RefreshSlots()
        self.OnTick() # Extra tick to make changes look smooth
        
    def OnRefreshHud(self, **kwargs):
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
    
    