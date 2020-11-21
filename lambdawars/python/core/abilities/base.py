""" Defines the base class for abilities.

    Provides common methods for completing, cancelling, taking resources, selecting units, etc.
"""

from srcbase import IN_SPEED
from srcbuiltins import (RegisterTickMethod, RegisterPerFrameMethod, UnregisterTickMethod, UnregisterPerFrameMethod,
                         IsTickMethodRegistered)
import traceback

from .info import AbilityInfo, GetTechNode, active_abilities, wars_ability_debug, GetAbilityInfo, dbabilities
from core.resources import TakeResources, GiveResources, FindFirstCostSet
from core.usermessages import usermessage, CRecipientFilter, CSingleUserRecipientFilter
from core.dispatch import receiver
from core.signals import (FireSignalRobust, postlevelshutdown, prelevelinit, abilitycompleted, abilitycanceled,
                          abilitycompleted_by_name, abilitycanceled_by_name)
from core.decorators import clientonly, clientonly_assert, serveronly_assert
from utils import UTIL_ListPlayersForOwnerNumber
from entities import CBaseEntity, CHL2WarsPlayer
from gameinterface import engine, concommand, ConVarRef, AutoCompletion
from gamerules import GameRules
from fields import FloatField
import weakref

if isserver:
    from core.signals import selectionchanged
    from utils import UTIL_GetCommandClient
else:
    from core.signals import playerspawned, abilitymenuchanged
    import hotkeymgr

sv_cheats = ConVarRef('sv_cheats')


# Use this to stop the Init function (to prevent the remainder of the function to run)
class StopInit(Exception):
    pass


# Base ability class
class AbilityBase(AbilityInfo):
    """ Base class for abilities."""
    def InitAbility(self, 
                    id,
                    player,
                    ischeat=False,
                    unittype=None,
                    forcedserveronly=False,
                    autocasted=False,
                    **kwargs):
        """ Creates a new ability instance.
        
            Args:
                id (int): id of this ability (automatically assigned by DoAbility).
                player (entity): Reference to player entity.

            Kwargs:
                ischeat (bool): Indicates if executed as cheat. Can be used to skip requirements or make
                         the ability behave differently.
                unittype (str): Unit type executing this ability.
                forcedserveronly (bool): Never try to initialize on the client. Used for the strategic AI.
                autocasted (bool): Whether this ability was autocasted
        """
        assert player != None, 'Abilities require a valid player'
        self.info = self
        self.abilityid = id
        self.player = player
        self.ischeat = ischeat
        self.units = []  # List of units actively executing this ability
        self.removedunits = []  # List of weak refs to units who were executing the ability, but were removed afterwards
        self.unittype = unittype
        self.ownernumber = self.player.GetOwnerNumber()
        self.timestamp = gpGlobals.curtime
        self.autocasted = autocasted
        self.kwarguments = kwargs
        
        # Precache in we are not precached yet
        PrecacheAbility(self.name)
        
        active_abilities.add(self)
        
        if isserver and wars_ability_debug.GetBool():
            DevMsg(1, "%s: Starting ability %s (autocasted: %s)\n" % ('Client' if isclient else 'Server', self.name, self.autocasted))
            
        # Determine if the ability should be server only
        # This means the ability is not created on the client executing the ability
        if forcedserveronly:
            self.serveronly = True
        elif ischeat:
            self.serveronly = self.serveronly or self.playerserveronly
        else:
            self.serveronly = self.serveronly or self.unitserveronly
            
        try: 
            self.Init()
        except StopInit:
            assert self.stopped, 'Ability raised StopInit exception, but was not stopped correctly'

        # Completed/canceled in Init
        if self.stopped:
            return
        
        self.initialized = True
            
        if self.Tick:
            RegisterTickMethod(self.Tick, self.ticksignal)
        if self.Frame:
            RegisterPerFrameMethod(self.DoFrameCall)
            
        if isclient:
            self.ClientUpdateAbilitiesMenu()
        
        # If server, send message to client to create the ability
        if isserver and not self.serveronly:
            if self.player:
                filter = CSingleUserRecipientFilter(self.player)
                filter.MakeReliable()
                ClientCreateAbility(self.name, self.abilityid, self.ischeat, filter=filter)
            self.clientinitialized = True
                
    def ClientUpdateAbilitiesMenu(self):
        """ Updates the abilities menu for the client executing this ability.
            By default we clear any sub menu. Override this method to change
            this behavior. """
        # Clear any sub menu
        self.player.hudabilitiesmap = []
        SendAbilityMenuChanged()
                
    def Init(self):
        """ Initializes the ability. Override this method and not __init__!"""
        pass
        
    @classmethod           
    def Precache(info):
        """ Precaches the ability. Called once per map (only if the ability is going to be used)."""
        if info.activatesoundscript:
            if info.activatesoundscript[0] != '#':
                CBaseEntity.PrecacheSound(info.activatesoundscript)
                
    @classmethod
    def DoAbilityAlt(info, player):
        """ Implements ability alt functionality, which is triggered
            by right clicking the ability.
        
            By default this controls the autocast behaviour.
            Most abilities should keep this behaviour.

            Args:
                player (entity): Player executing the ability
        """
        selection = player.GetSelection()
        
        # Determine if we set all units to autocast or not.
        setautocast = False
        for unit in selection:
            if info.uid not in unit.abilities:
                continue
            if not unit.abilitycheckautocast[info.uid]:
                setautocast = True
                break
                
        # Now change autocast state
        for unit in selection:
            # Only units with this ability
            if info.uid not in unit.abilities:
                continue
            unit.abilitycheckautocast[info.uid] = setautocast

            # Make sure excluded autocast abilities are off
            if setautocast:
                for abi_name in info.autocast_exclude:
                    abi = unit.abilitiesbyname.get(abi_name, None)
                    if not abi:
                        continue
                    unit.abilitycheckautocast[abi.uid] = False

            # Attack definition for autocasting (when used as main attack)
            if info.autocast_attack:
                unit.RebuildAttackInfo()

            # TODO: Trigger this from setting abilitycheckautocast
            unit.UpdateAutocastLists()
            if hasattr(unit, 'DispatchEvent'):
                unit.DispatchEvent('OnAutocastChanged', info)

    def Cancel(self, cancelmsg=None, notification=None, debugmsg=''):
        """ Ability is canceled before execution.
        
            Will refund resources in case taken if refundoncancel was
            set to True.

            Kwargs:
                cancelmsg (str|None): Message displayed to player on cancel
                notification (str|None): Optional notification to be played
                debugmsg (str): Debug message print to console when debugging abilities
        """
        if self.stopped:
            return        
        self.stopped = True
        
        if isserver and wars_ability_debug.GetBool():
            DevMsg(1, 'Canceling/stopping ability %s (reason: %s)\n' % (self.name, debugmsg))
        
        # Refund if needed
        if isserver and self.refundoncancel:
            self.Refund()
        
        self.Cleanup()
        
        if self.oncancel:
            self.oncancel(self)
            
        FireSignalRobust(abilitycanceled, ability=self)
        FireSignalRobust(abilitycanceled_by_name[self.name], ability=self)
        
        # Notify client
        if isserver:
            if cancelmsg or notification:
                from core.notifications import DoNotificationAbi # FIXME
                players = UTIL_ListPlayersForOwnerNumber(self.ownernumber)
                msg_filter = CRecipientFilter()
                msg_filter.MakeReliable()
                [msg_filter.AddRecipient(p) for p in players]
                DoNotificationAbi(notification or 'ability', self.name, cancelmsg, filter=msg_filter)
        
            if self.player and not self.serveronly:
                recv_filter = CSingleUserRecipientFilter(self.player)
                recv_filter.MakeReliable()
                
                if not self.clientinitialized:
                    ClientCreateAbility(self.name, self.abilityid, self.ischeat, filter=recv_filter)
                    self.clientinitialized = True
                    
                if self.clientinitialized:
                    ClientAbilityCanceled(self.abilityid, filter=recv_filter)

    def Completed(self):
        """ Call when the ability is completed.
        
            On the server it will dispatch a completed message to the client.
        """
        if self.stopped:
            return
        self.stopped = True

        self.Cleanup()
        
        if self.oncompleted:
            self.oncompleted(self)
            
        FireSignalRobust(abilitycompleted, ability=self)
        FireSignalRobust(abilitycompleted_by_name[self.name], ability=self)
        
        if isserver:
            if self.player and not self.serveronly:
                # Notify client
                recvfilter = CSingleUserRecipientFilter(self.player)
                recvfilter.MakeReliable()
                
                if not self.clientinitialized:
                    ClientCreateAbility(self.name, self.abilityid, self.ischeat, filter=recvfilter)
                    self.clientinitialized = True
                    
                if self.clientinitialized:
                    ClientAbilityCompleted(self.abilityid, filter=recvfilter)
        
        self.TestContinueAbility()
 
    def ClearMouse(self, syncserverclient=False):
        """ Removes this ability from the active ability list of the player.
            This means the ability no longer receives mouse input from the player.
            This method does nothing if the ability is not active on player.
            
            Kwargs:
                syncserverclient (bool): Special case where the client or server will send a message to the server/client to 
                                         also clear the mouse. Usually this is not needed.
        """
        if self.player and self.player.IsActiveAbility(self):
            self.player.RemoveActiveAbility(self)
            if syncserverclient:
                if isclient:
                    engine.ServerCommand('player_abilityclearmouse %d' % (self.abilityid))
                else:
                    ClientAbilityClearMouse(self.abilityid)
            
    def Cleanup(self):
        """ Called by both completed and cancel to cleanup shared stuff,
            like visuals or unregistering tick and frame methods. 
        """
        # Indicates cleaned up was called and this ability instance should no longer used
        self.cleaned_up = True
        # Avoid the prediction callback will do a cleanup
        self._predicting = False
        
        # Make sure we don't hold the active ability of the player
        self.ClearMouse()

        # Remove Frame/Tick registered methods
        if self.Tick and IsTickMethodRegistered(self.Tick):
            UnregisterTickMethod(self.Tick)
            
        # Remove ourself from the active ability list
        active_abilities.discard(self)
        
        if wars_ability_debug.GetBool():
            DevMsg(1, 'AbilityBase.Cleanup: removed ability %s with id %d from the active ability list\n' % (self.name, self.abilityid))
    
    @serveronly_assert
    def TakeResources(self, refundoncancel=False, count=1):
        """ Takes resources from the player as per defined in costs.
        
            Kwargs:
               refundoncancel (bool): If it should refund on cancel
               count (int): number of times it should try to take resources
               
            Returns:
               int: number of times it was able to take resources
        """
        if not self.costs:
            return count
            
        ownernumber = self.ownernumber
            
        technode = GetTechNode(self.name, ownernumber)
        if technode.nocosts:
            return count
            
        taken = 0
        for i in range(0, count):
            resourcestaken = FindFirstCostSet(self.costs, ownernumber)
            if not resourcestaken:
                break
            TakeResources(ownernumber, resourcestaken, resource_category=self.resource_category)
            if not self.resourcestaken:
                self.resourcestaken = [resourcestaken]
            else:
                self.resourcestaken.append(resourcestaken)
            taken += 1
        self.refundoncancel = refundoncancel

        return taken
        
    @serveronly_assert
    def TakeEnergy(self, units):
        """ Takes energy from the list of units.
        
            Args:
               units (list,entity): units from which the energy should be taken.
               
            Returns:
                list: new list of units for which this succeeded. 
        """
        if type(units) != list:
            units = [units] # Assume reference to single unit
        valid = []
        for unit in units:
            if unit.TakeEnergy(self.energy):
                valid.append(unit)
        return valid
        
    @serveronly_assert
    def SetRecharge(self, units, t=0):
        """ Sets recharge on the input units.
        
            Args:
               units (list,entity): units on which the recharge should be set
        """
        if type(units) != list:
            # Assume reference to single unit
            units = [units]
        if self.rechargetime != 0:
            # Collect abilities on which to set the recharge time.
            # Usually just the executing ability, but for some abilities it also affects other abilities on the unit.
            abi_uids = set([self.uid])
            for abi_name in self.recharge_other_abilities:
                abi = GetAbilityInfo(abi_name)
                if not abi:
                    continue
                abi_uids.add(abi.uid)

            for unit in units:
                for uid in abi_uids:
                    unit.abilitynexttime[uid] = gpGlobals.curtime + self.rechargetime + t
                
    @serveronly_assert
    def Refund(self):
        """ Refunds taken resources to the player.
        
            This is normally done in the Cancel method.
        """
        ownernumber = self.ownernumber
        if self.resourcestaken:
            for resourcestaken in self.resourcestaken:
                resourcestaken = [(cost[0], cost[1] * self.refundmodifier) for cost in resourcestaken]
                GiveResources(ownernumber, resourcestaken)
            
    def PlayActivateSound(self):
        """ Plays activate sound.
            
            The actual moment this method is called is up for the sub classes, since
            it depends on the type of ability (target, instant, etc).
        """
        if not self.player or not isclient:
            return
        
        #print '%s playing activated sound %s %s' % (isclient, self.activatesoundscript, self.unit)
        if self.activatesoundscript:
            if self.activatesoundscript[0] == '#':
                if self.unit:
                    soundscript = self.unit.GetAbilitySound(self.activatesoundscript[1:])
                    if soundscript:
                        #print 'emitting sound %s' % (soundscript)
                        self.unit.PlayOrderSound(soundscript, force=self.activatesoundscript_force_play)
            else:
                #print 'emitting sound %s' % (self.activatesoundscript)
                if self.unit:
                    self.unit.PlayOrderSound(self.activatesoundscript, force=self.activatesoundscript_force_play)
                elif self.player:
                    self.player.EmitAmbientSound(-1, self.player.GetAbsOrigin(), self.activatesoundscript)

    def OnUnitRemoved(self, unit):
        """ Called when one of the units executing this ability was removed or killed.

            Args:
                unit (entity): handle to unit entity
        """
        if self.attachedtoorder:
            # OnUnitOrderEnded will do this
            return
        if unit in self.units:
            self.RemoveUnit(unit)
        if not self.units:
            self.OnAllUnitsCleared()
            
    def OnUnitOrderEnded(self, unit):
        """ Called when one of the unit executing this ability had an order attached
            to this ability and that order ended.
        """
        if unit in self.units:
            self.RemoveUnit(unit)
        if not self.units:
            self.OnAllUnitsCleared()
            
    def OnAllUnitsCleared(self):
        """ Called when all active units of this ability are cleared. This is useful
            for completing or cancelling the ability when all units are done or died.
        """
        pass
        
    @serveronly_assert
    def OnSelectionChanged(self, player):
        """ Notifies the selection of the player changed. 
            Clears mouse if the ability is operating on a set of units and the units
            are no longer in the selection.
            
            Override in case other behavior is desired.
            
            Args:
               player (entity): The player of which the selection changed.
        """
        if not self.units:
            return
            
        if player != self.player:
            return
            
        if not self.player.IsActiveAbility(self):
            return
            
        if not set(self.units).issubset(set(player.GetSelection())):
            self.ClearMouse()
        
    def SelectGroupUnits(self):
        """ Selects all units in the player selection which have this ability and can
            do the ability at his moment.
        """
        player = self.player
        self.unit = None
        self.units = []
        for unit in player.GetSelection():
            #if unit is garrisoned it still sould be able to shoot
            if not self.autocasted and not unit.CanPlayerControlUnit(player):
                continue
                
            activeability = unit.activeability
            if activeability and not activeability.interruptible:
                continue

            # Get the ability
            if self.name not in unit.abilitiesbyname:
                continue
            abiinfo = unit.abilitiesbyname[self.name]
            
            # Can do?
            if not abiinfo.CanDoAbility(player, unit):
                continue
                
            self.AddUnit(unit)
        return self.units
        
    def ComputeUnitCost(self, unit):
        """ Computes cost associated for unit executing this ability. 
        
            Lower costs are preferred. Return 0 for not implemented.
        """
        return 0
        
    def SelectSingleUnit(self):
        """ Returns an unit from the player selection that is able to do this ability.
        
            A unit is selected from the player selection based on the following rules:
            1. Unit should have the ability
            2. Should not have an active not interruptable ability (e.g. in the middle of throwing a grenade)
            3. Should be able to do the ability (e.g. enough resources, not recharging)
            4. Units will less abilities queued up should be preferred
            5. Test based on cost computed by ComputeUnitCost (e.g. target abilities compute the distance as cost)
        """
        # Find an unit with this type
        player = self.player
        self.unit = None
        self.units = []
        bestunit = None
        bestcost = None
        bestnabilities = None
        for unit in player.GetSelection():
            #if unit is garrisoned it still sould be able to shoot
            if not self.autocasted and not unit.CanPlayerControlUnit(player):
                continue
            
            # Check if there is an active ability and if it's interruptable
            activeability = unit.activeability
            if activeability and not activeability.interruptible:
                continue
            
            # Get the ability
            if self.name not in unit.abilitiesbyname:
                continue
            abiinfo = unit.abilitiesbyname[self.name]
            
            # Can do?
            if not abiinfo.CanDoAbility(player, unit):
                continue
            
            # Prefer units with no active ability
            try:
                nabilities = len([o for o in unit.orders if o.ability and not o.ability.autocasted])
            except AttributeError:
                nabilities = 0 # Not a basecombat unit (i.e. building or something else)
            if activeability and not activeability.autocasted: 
                nabilities += 1
            cost = self.ComputeUnitCost(unit)
            if not bestunit or nabilities < bestnabilities:
                bestunit = unit
                bestnabilities = nabilities
                bestcost = cost
            elif nabilities == bestnabilities and cost < bestcost:
                bestunit = unit
                bestnabilities = nabilities
                bestcost = cost
                
        if bestunit:
            self.AddUnit(bestunit)
            return bestunit
        return None
        
    def AddUnit(self, unit):
        """ Adds an unit to the list of active units executing this ability.
        
            Args:
               unit (entity): unit which should be added.
        """
        self.units.append(unit)
        self.unit = self.units[0]
        unit.participating_abilities.append(self)

    def RemoveUnit(self, unit):
        """ Removes an unit from the list of active units executing this ability.
        
            Args:
               unit (entity): unit which should be removed.
        """
        self.units.remove(unit)
        if unit == self.unit:
            self.unit = self.units[0] if self.units else None
        self.removedunits.append(weakref.ref(unit))
        unit.participating_abilities.remove(self)
            
    def AbilityOrderUnits(self, units, *args, **kwargs):
        """ Helper method for executing ability orders on a set of units.
        
            Args:
               units (list,entity): input units
               
            Returns:
                list: the generated ability orders
        """
        orders = []
        
        if type(units) != list: 
            units = [units]
            
        # Autocast should never cancel the existing order(s)
        alwaysqueue = True if self.autocasted else False
        idx = 0 if alwaysqueue else None
        
        for unit in units:
            if not unit or not unit.IsAlive():
                continue
            orders.append(unit.AbilityOrder(alwaysqueue=alwaysqueue, idx=idx, *args, **kwargs))
            
        return orders
    
    @classmethod
    def SetupOnUnit(info, unit):
        """ Optional method for setting up the ability on an unit. 
            Might be called multiple times on the same entity."""
        pass
        
    def AllowAutoCast(self, unit):
        """ Allow another ability to autocast while this ability is the active order of the passed unit. """
        return False
        
    @classmethod
    def CheckAutoCast(cls, unit):
        """ Return True if this ability executed autocast. """
        return False
        
    @classmethod
    def OverrideOrder(cls, unit, data, player):
        """ Called when this unit is ordered. Can be used to automatically
            execute this ability on right clicking something.
            
            Return True to override.
        
            Args:
               data (MouseData): mouse data
               player: 
        """
        return False
            
    @serveronly_assert
    def SetSyncedAttribute(self, name, value):
        """ Convient method for setting an attribute
            on both the server and client version of 
            the ability object.
        """
        setattr(self, name, value)
        if self.serveronly or not self.player:
            return
        assert self.clientinitialized, 'Can only call SetSyncedAttribute after initializing the client ability!'
        recvfilter = CSingleUserRecipientFilter(self.player)
        recvfilter.MakeReliable()
        ClientAbilitySetAttr(self.abilityid, name, value, filter=recvfilter)
            
    @serveronly_assert
    def SetInterruptible(self): 
        self.SetSyncedAttribute('interruptible', True)
        
    @serveronly_assert
    def SetNotInterruptible(self): 
        self.SetSyncedAttribute('interruptible', False)
        
    @clientonly_assert
    def SetPredicted(self):
        if self.stopped:
            return
        self._predicting = True
        RegisterTickMethod(self.PredictCallback, 2.5, False)
        
    @clientonly_assert
    def PredictCallback(self):
        try:
            if self._predicting:
                DevMsg(4, 'Prediction of ability %s failed!\n' % (self.name))
                if not self.stopped:
                    self._predictfailed = True
                    self.stopped = True
                    self.Cleanup()
        except:
            PrintWarning('Failed to cleanup ability %s with id %d\n' % (self.name, self.abilityid))
            traceback.print_exc()
        
    @clientonly_assert
    def ContinueAbility(self, hotkeysystem=None):
        self.continueabihotkeysystem = hotkeysystem
        # Delay by one frame to avoid problems with mouse events
        RegisterTickMethod(self.DoContinueAbility, 0.0, False)
        
    @clientonly_assert
    def DoContinueAbility(self):
        abi = ClientDoAbility(self.player, self.name, self.unittype)
        if not abi:
            return
        abi.clearmouseonspeedbuttonrelease = self.clearmouseonspeedbuttonrelease
        abi.clearmouseonhotkeyrelease = self.clearmouseonhotkeyrelease
        if self.continueabihotkeysystem:
            self.continueabihotkeysystem.activeability = abi
            self.continueabihotkeysystem = None
            
    @clientonly_assert
    def OnHotkeyReleased(self):
        #print('OnHotkeyReleased: ability id %d' % (self.abilityid))
        if self.clearmouseonhotkeyrelease:
            self.ClearMouse(syncserverclient=True)
            
    def OnSpeedButtonChanged(self):
        if self.clearmouseonspeedbuttonrelease:
            self.ClearMouse(syncserverclient=True)
            
    @clientonly
    def TestContinueAbility(self):
        if not self.allowcontinueability:
            return
            
        # Test if set through hotkey system
        hotkeysystem = hotkeymgr.hotkeysystem
        if hotkeysystem:
            if hotkeysystem.activeabiinfo and self.__class__ == hotkeysystem.activeabiinfo:
                self.ContinueAbility(hotkeysystem)
                self.allowcontinueability = False # Don't allow further test if this ability is not yet done on the client
                self.clearmouseonhotkeyrelease = True
                return
            
        player = CHL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
            
        # Test if holding shift, in which case we also continue
        if player.buttons & IN_SPEED:
            self.ContinueAbility()
            self.allowcontinueability = False # Don't allow further test if this ability is not yet done on the client
            self.clearmouseonspeedbuttonrelease = True
            return

    def DoFrameCall(self):
        """ Manages Frame call.
            Unregisters DoFrameCall after Cleanup. Not directly from cleanup, because
            unregister may only be called from the active frame method itself.
        """
        if self.cleaned_up:
            UnregisterPerFrameMethod(self.DoFrameCall)
            return

        self.Frame()

    # Update methods
    Frame = None
    Tick = None
    ticksignal = 0.1
    
    # Callbacks
    #: Assign this to a method you want to be called on ability completion. Takes a single argument: the ability self.
    oncompleted = None
    #: Assign this to a method you want to be called on ability cancel. Takes a single argument: the ability self.
    oncancel = None

    # Variables
    clientinitialized = False
    _predicting = False
    _predictfailed = False
    
    stopped = False
    refundoncancel = False
    interruptible = True
    autocasted = False
    attachedtoorder = False
    
    #: Modifies the amount of resources refunded
    refundmodifier = FloatField(value=1.0)
    
    clearedbyclientmsg = False
    initialized = False
    cleaned_up = False
    
    #: If True, the player executing the ability will directly create the ability on the client, 
    #: assign a predicted id, and then later sync up the ability. This prevents the player from
    #: noticing the lag between starting and executing the ability.
    predict = True
    
    unitserveronly = False
    playerserveronly = False
    
    #: If True, this ability is never created on the client of the player executing this ability.
    serveronly = False
    #: If True, this ability is only created on the client of the player executing this ability.
    clientonly = False
    
    unit = None
    resourcestaken = None
    
    #: Allow direct recasting of the ability when holding down the hotkey
    allowcontinueability = False
    #: Clear mouse when the "speed" key is released (IN_SPEED), used when the ability was continued after holding shift (client only setting)
    clearmouseonspeedbuttonrelease = False
    #: Clear mouse when the active hotkey is released, used when the ability was continued after holding the hotkey (client only setting)
    clearmouseonhotkeyrelease = False
    
    continueabihotkeysystem = None

    #: If casted by pressing a hotkey, this is a ref to the hotkey system.
    #: You can use this to notify the hotkey system when done. Then it will
    #: cast a new ability if the hotkey is still down (except if allowcontinueability
    #: is false).
    hotkeysystem = None
    
    # Autocast related
    #: CheckAutoCast called on unit think
    autocastcheckonunitthink = False
    #: CheckAutoCast called on unit return to idle
    autocastcheckonidle = False
    #: CheckAutoCast called on unit having a new enemy
    autocastcheckonenemy = False
    #: Attack definition for autocasting as main attack
    autocast_attack = None

# Creation of abilities
# ID's on server start at 0, while predicted id's at the client start at 16384 * entindex()
abilityid = 0 
abilityidmin = 0
abilityidmax = 16384

def GetNewAbilityID():
    global abilityid, abilityidmax, abilityidmin
    id = abilityid
    abilityid += 1
    if abilityid >= abilityidmax:
        abilityid = abilityidmin
    return id
    
def GetAbilityByID(id):
    return next((x for x in active_abilities if x.abilityid == id), None)
    
if isserver:
    @receiver(prelevelinit)
    def AbilitiesPreLevelInit(sender, **kwargs):
        global abilityid, abilityidmin, abilityidmax
        abilityid = 0
        abilityidmin = 0
        abilityidmax = 16384
        
    @receiver(selectionchanged)
    def OnSelectionChanged(sender, player, **kwargs):
        # Tell each ability the selection changed
        # This can be used to cancel the ability if it's an active mouse ability and
        # the unit being operated on was in the selection
        for abi in list(active_abilities):
            abi.OnSelectionChanged(player)
        
else:
    # Do not overlap the predicted ID range
    @receiver(playerspawned)
    def AbilitiesClientActive(sender, player, **kwargs):
        global abilityid, abilityidmin, abilityidmax
        idx = player.entindex()
        assert(idx > 0)
        abilityidmin = 16384 * idx
        abilityidmax = abilityidmin + 16384
        abilityid = abilityidmin 

    @concommand('wars_ability_print_clientidrange')
    def AbilitiesPrintIDRange(args):
        print('Ability id range %d - %d. Current id: %d' % (abilityidmin, abilityidmax, abilityid))
    
isabiprecached = set()
def PrecacheAbility(abi_name):
    """ Precache the ability by calling the static Precache method 
        of the ability
        
        Only calls Precache once per map for each ability that is being used.
        
        Args:
            abi_name (string): The name of the ability to be precached
    """
    # Avoid double precaching (and also avoid infinitive loops)
    if abi_name in isabiprecached:
        return
    isabiprecached.add(abi_name)

    # Get info
    info = GetAbilityInfo(abi_name)
    if not info:
        PrintWarning("core.abilities.info.PrecacheAbility: No registered ability named %s\n" % (abi_name) )
        return
        
    # Precache
    info.Precache()

def CreateAbility(abi_info, player, ischeat=False, unittype=None, id=-1, skipcheck=False, 
                  forcedserveronly=False, clientonly=False, autocasted=False, **kwargs):
    """ Create/execute an ability. 
    
        This will return None in case creating the ability fails.
        Note that it may also return an already stopped/completed/canceled ability.
        For example this might be the case when the ability is instantaneous.
        
        Args:
           abi_info (class): Ability class
           player (entity): the player executing the ability
           
        Kwargs:
           ischeat (bool): indicates the ability is executed as a cheat. Skips checking requirements.
           unittype (string): Associates an unit type with the ability
           id (int): the ability unique identifier. In case -1, a new identifier will be assigned
           skipcheck (bool): Skips requirements check
           forcedserveronly (bool): Force execution on server only. This is for CPU players.
           clientonly (bool): Indicates the ability is client only (e.g. a sub menu)
           autocasted (bool): Indicates the ability was autocasted (behavior of ability might vary in this case)
    """
    if isinstance(abi_info, str):
        abi_info = dbabilities.get(abi_info, None)
        if not abi_info:
            PrintWarning("core.abilities.info.CreateAbility: No registered ability named %s\n" % (abi_info) )
            return None
        
    # Check can do
    if isserver and not skipcheck and (len(abi_info.GetRequirementsUnits(player)) != 0):
        if wars_ability_debug.GetBool():
            DevMsg(1, '%s core.abilities.info.CreateAbility: failed to create ability (requirements not met -> %s)\n' % (isserver, abi_info.GetRequirementsUnits(player)))
        if isserver and id != -1:
            recv_filter = CSingleUserRecipientFilter(player)
            recv_filter.MakeReliable()
            ClientAbilityCanceled(id, filter=recv_filter) # Cancel predicted ability
        return None      # FAIL

    # Get ID
    predicted = False
    if id == -1:
        newID = GetNewAbilityID()
        if isclient: 
            predicted = True
    else:
        newID = id
            
    # OK, we got a module. Create new ability instance.
    abi = abi_info()
    abi.InitAbility(newID, player, ischeat=ischeat, unittype=unittype, 
                   forcedserveronly=forcedserveronly, autocasted=autocasted, **kwargs)

    if not abi.stopped:
        if predicted:
            abi.SetPredicted()
            
    if wars_ability_debug.GetBool():
        DevMsg(1, '%s core.abilities.info.CreateAbility: created ability %s with id %s, predicted: %s, stopped: %d\n' % 
                  ('Server' if isserver else 'Client', abi.name, abi.abilityid, predicted, abi.stopped))
        
    return abi
    

def DoAbility(player, abiname, unittype=None, predictedid=-1, clientonly=False, **kwargs):
    """ Given an unit type, create the ability.
        
        It will search the selection of the player for a candidate to execute the ability.
        
        Args:
            player (entity): the player executing the ability.
            abiname (str): Ability name to be executed.
            
        Kwargs:
            unittype (str): 
            predictedid (int): Ability ID provided by client.
            clientonly (bool): Whether or not the ability only exists on the client executing it (e.g. menu abilities).
    """
    # Get info
    abiinfo = GetAbilityInfo(abiname)
    if not abiinfo:
        if wars_ability_debug.GetBool():
            DevMsg(1, 'core.abilities.info.DoAbility: invalid ability specified\n')
        return None
    
    return CreateAbility(abiinfo, player, unittype=unittype, id=predictedid, clientonly=clientonly, **kwargs)

@serveronly_assert
def DoAbilitySimulated(simulatedplayer, abiname, unittype=None, mouse_inputs=[], autocasted=False, **kwargs):
    """ Execute an ability given a sequence of mouse inputs.
    
        This method is for cpu players and auto casting.
        
        Args:
            player (entity): the simulated player executing the ability.
            abiname (str): Ability name to be executed.
            
        Kwargs:
            unittype (str): 
            mouse_inputs (list): List of mouse inputs to be inserted. Each entry is a tuple containing the type and mouse data.
            autocasted (bool): Indicates the ability is autocasted or not, used as a hint to the unit AI.
    """
    abi = CreateAbility(abiname, player=simulatedplayer, unittype=unittype, 
                        forcedserveronly=True, autocasted=autocasted, **kwargs)
    if not abi:
        return None
    for mi in mouse_inputs:
        simulatedplayer.mousedata = mi[1]
        if mi[0] == 'leftpressed':
            simulatedplayer.leftmousepressed = mi[1]
            abi.OnLeftMouseButtonPressed()
        elif mi[0] == 'leftdoublepressed':
            simulatedplayer.leftmousedoublepressed = mi[1]
            abi.OnLeftMouseButtonDoublePressed()
        elif mi[0] == 'leftreleased':
            simulatedplayer.leftmousereleased = mi[1]
            abi.OnLeftMouseButtonReleased()
        elif mi[0] == 'rightpressed':
            simulatedplayer.rightmousepressed = mi[1]
            abi.OnRightMouseButtonPressed()
        elif mi[0] == 'rightdoublepressed':
            simulatedplayer.rightmousedoublepressed = mi[1]
            abi.OnRightMouseButtonDoublePressed()
        elif mi[0] == 'rightreleased':
            simulatedplayer.rightmousereleased = mi[1]
            abi.OnRightMouseButtonReleased()
    return abi

@clientonly_assert
def SendAbilityMenuChanged():
    responses = abilitymenuchanged.send_robust(None)
    for r in responses:
        if isinstance(r[1], Exception):
            PrintWarning('Error in receiver %s (module: %s): %s\n' % (r[0], r[0].__module__, r[1]))

@clientonly_assert
def ClientDoAbility(player, abiname, unittype='', **kwargs):
    """ Starts an ability from the client side. Depending on the abilty type,
        this will either keep the ability client side, start a predicted ability or
        just tells the server to create the ability.
    """
    # Get info
    if type(abiname) == str:
        info = GetAbilityInfo(abiname)
        if not info:
            if wars_ability_debug.GetBool():
                DevMsg(1, 'core.abilities.info.ClientDoAbility: invalid ability specified\n')
            return None
    else:
        info = abiname
        
    abi = None
    if info.clientonly:
        abi = DoAbility(player, info.name, unittype, clientonly=True, **kwargs)
    elif not info.predict or info.serveronly or info.unitserveronly:
        engine.ServerCommand('player_ability %s %s' % (info.name, unittype))
    else:
        abi = DoAbility(player, info.name, unittype, **kwargs)
        if abi and not abi.stopped:
            engine.ServerCommand('player_ability %s %s %d' % (info.name, unittype, abi.abilityid ))
    return abi
        
# Shutdown/new clients
@receiver(postlevelshutdown)
def AbilitiesShutdown(sender, **kwargs):
    isabiprecached.clear()
    
if isserver:
    @concommand('wars_abi', 'Execute an ability as cheat.', completionfunc=AutoCompletion(lambda: dbabilities.keys()))
    def cc_wars_abi(args):
        if not sv_cheats.GetBool() and not GameRules().info.name == 'sandbox':
            print("Can't use cheat command wars_abi in multiplayer, unless the server has sv_cheats set to 1 or game is in sandbox mode.")
            return
        if args.ArgC() < 2:
            print('wars_abi: not enough arguments')
            return
        player = UTIL_GetCommandClient()
        
        subargs = {}
        abiargs = args.ArgS().split()
        for argument in abiargs[1:]:
            try:
                k, v = argument.split('=', 1)
                subargs[k] = v
            except ValueError:
                print('wars_abi %s: invalid formatted argument %s. Ignoring...' % (args[1], argument))
                
        CreateAbility(args[1], player, ischeat=True, skipcheck=True, **subargs)
    
# Messages
@usermessage()
def ClientCreateAbility(abi_name, id, ischeat, **kwargs):
    # The ability might be predicted
    # In that case copy the unit value (in case wrongly predicted)
    for abi in active_abilities:
        if abi.abilityid == id:
            abi._predicting = False
            return

    # Message is only send to the player executing the ability
    # So we can get the local player
    player = CHL2WarsPlayer.GetLocalHL2WarsPlayer()
    
    CreateAbility(abi_name, player, ischeat=ischeat, id=id)
    
@usermessage()
def ClientAbilityCompleted(id, **kwargs):
    for abi in active_abilities:
        if abi.abilityid == id:
            abi.clearedbyclientmsg = True
            abi.Completed()
            if wars_ability_debug.GetBool():
                DevMsg(1, 'core.abilities.base.ClientAbilityCompleted: Completed ability %d\n' % (id))
            return
    PrintWarning("Client Message Ability Completed: invalid ability ID %d\n" %(id))
    
@usermessage()
def ClientAbilityCanceled(id, **kwargs):
    for abi in active_abilities:
        if abi.abilityid == id:
            abi.clearedbyclientmsg = True
            abi.Cancel()
            if wars_ability_debug.GetBool():
                DevMsg(1, 'core.abilities.base.ClientAbilityCanceled: Canceled ability %d\n' % (id))
            return
    PrintWarning("Client Message Ability Canceled: invalid ability ID %d\n" %(id))
    
@usermessage()
def ClientAbilitySetAttr(id, name, value, **kwargs):
    for abi in active_abilities:
        if abi.abilityid == id:
            setattr(abi, name, value)
            if wars_ability_debug.GetBool():
                DevMsg(1, 'core.abilities.base.ClientAbilitySetAttr: setted attribute %s to %s of ability %d\n' % (name, str(value), id))
            return
    PrintWarning("Client Message Ability SetAttr: invalid ability ID %d\n" %(id))
        
@usermessage()
def ClientAbilityClearMouse(id, **kwargs):
    for abi in active_abilities:
        if abi.abilityid == id:
            abi.ClearMouse()
            return
    PrintWarning("Client Message Ability Clear Mouse: invalid ability ID %d\n" %(id))
        