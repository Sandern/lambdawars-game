from srcbase import *
from vmath import *
import random
import traceback
from core.notifications import DoNotificationEnt, GetNotifcationFilterForOwnerAndAllies
from .cover import CoverSpot
from .info import (UnitInfo, UnitFallBackInfo, GetUnitInfo, AddUnit, RemoveUnit, ChangeUnit, unitpopulationcount,
                  ChangeUnitType, unitlist, NoSuchAbilityError, UnitListHandle, UnitListPerTypeHandle)
from core.abilities import PrecacheAbility, GetTechNode, AbilityMenuBase, SubMenu, DoAbilitySimulated
from playermgr import SimulatedPlayer, dbplayers, relationships
from core.signals import (FireSignalRobust, ScheduleFireSignalRobust, unitselected, unitdeselected, 
                          postlevelshutdown, gamepackageloaded, unitspawned, unitremoved)
from core.dispatch import receiver
import ndebugoverlay

from gameinterface import concommand, ConVar, FCVAR_CHEAT, CPVSFilter, engine, ConVarRef
from entities import (networked, Activity, ACT_INVALID, FOWFLAG_INITTRANSMIT, D_LI, D_HT, CHL2WarsPlayer,
                      SendProxyAlliesOnly)
from animation import (ADD_ACTIVITY, ActivityList_IndexForName, EventList_RegisterPrivateEvent, 
                       ResetActivityIndexes, ResetEventIndexes, VerifySequenceIndex)
from unit_helper import TranslateActivityMap
from particles import *

if __debug__:
    import mem_debug

if isclient:
    from core.signals import refreshhud, minimapupdateunit
    from entities import C_UnitBase as BaseClass, C_HL2WarsPlayer, DATA_UPDATE_CREATED
    from vgui import cursors
    from vgui.entitybar import UnitBarScreen
else:
    from gameinterface import GameEvent, FireGameEvent
    from core.signals import (unitkilled, unitkilled_by_victim, unitkilled_by_attacker, unitkilled_by_inflictor,
                              unitchangedownernumber, prelevelinit)
    from unit_helper import AnimEventMap
    from entities import CUnitBase as BaseClass, CTakeDamageInfo
    from utils import UTIL_SetSize, UTIL_PlayerByIndex, UTIL_GetCommandClient
    
from fields import (GenericField, EHandleField, ListField, DictField, IntegerField, FloatField, BooleanField,
                    StringField, ObjectField, OutputField, input)

from collections import defaultdict
from math import floor
from navmesh import CreateHidingSpot, DestroyHidingSpotByID
from utils import trace_t, UTIL_TraceLine, UTIL_ListPlayersForOwnerNumber

if isserver:
    unit_nodamage = ConVar('unit_nodamage', '0', FCVAR_CHEAT)
    unit_debugoverlay = ConVar('unit_debugoverlay', '', FCVAR_CHEAT)
else:
    cl_unit_disable_order_sounds = ConVarRef('cl_unit_disable_order_sounds')
    
# Reset per level variables
@receiver(postlevelshutdown)
def Reset(*args, **kwargs):
    UnitBaseShared.nextplayselectsound = 0.0
    UnitBaseShared.nextordersound = 0.0
    UnitBaseShared.lasttakedamageperowner.clear()
    UnitBaseShared.used_cover_spots.clear()
    UnitBaseShared.cover_spots_info.clear()
    
@receiver(gamepackageloaded)
def OnLoadGamepackage(*args, **kwargs):
    for l in unitlist.values():
        for unit in l:
            unit.BuildAttributeProperties()
    
if isclient:
    class UnitHealthBarScreen(UnitBarScreen):
        """ Draws the unit health bar. """
        def __init__(self, unit):
            super().__init__(unit,
                Color(), Color(40, 40, 40, 250), Color(150, 150, 150, 250))
            
        def Draw(self):
            if not self.unit or not self.unit.IsAlive() or self.unit.IsDormant():
                return
            panel = self.GetPanel()
            panel.weight = self.unit.HealthFraction()
            panel.barcolor = Color(int(255 - (panel.weight * 200.0)),
                    int(panel.weight * 220.0),
                    20+int(panel.weight*20.0),
                    250)
                    
            super().Draw()
            
    class UnitEnergyBarScreen(UnitBarScreen):
        """ Draws the unit health bar. """
        def __init__(self, unit):
            super().__init__(unit,
                Color(0, 0, 255, 250), Color(40, 40, 40, 250), Color(150, 150, 150, 250),
                offsety=4.0 )
            
        def Draw(self):
            if not self.unit or not self.unit.IsAlive() or self.unit.IsDormant():
                return
            panel = self.GetPanel()
            panel.weight = self.unit.energy/float(self.unit.maxenergy)
                    
            super().Draw()
            
    class UnitChannelBarScreen(UnitBarScreen):
        """ Draws the unit health bar. """
        def __init__(self, unit):
            super().__init__(unit,
                barcolor=Color(10, 239, 235, 250), fillcolor=Color(100, 100, 100, 250), outlinecolor=Color(180, 180, 180, 0), offsety=16.0, worldsizey=7.0, worldbloatx=14.0)
            
        def Draw(self):
            if not self.unit or not self.unit.IsAlive() or self.unit.IsDormant():
                return
            if not self.unit.ShouldShowChannelTimeBar():
                return
            channelstarttime, channelendtime = self.unit.channeltime
            duration = channelendtime - channelstarttime
            panel = self.GetPanel()
            panel.weight = min(1.0, (gpGlobals.curtime - channelstarttime) / duration) if duration > 0 else 1.0
            super().Draw()
        
class UnitListObjectField(ObjectField):
    def __init__(self, *objectargs, **objectkwargs):
        super().__init__(UnitListHandle, *objectargs, **objectkwargs)
        
    def InitField(self, inst):
        h = self.objectcls(inst, *self.objectargs, **self.objectkwargs)
        inst._unitlisthandles.append(h)
        setattr(inst, self.name, h)

    def Restore(self, instance, restorehelper):
        ''' Restores the object. '''
        super().Restore(instance, restorehelper)
        
        h = getattr(instance, self.name)
        owner = h.ownernumber
        h.ownernumber = -1
        h.Update(owner)
        
class UnitListPerTypeObjectField(ObjectField):
    def __init__(self, *objectargs, **objectkwargs):
        super().__init__(UnitListPerTypeHandle, *objectargs, **objectkwargs)
        
    def InitField(self, inst):
        h = self.objectcls(inst, *self.objectargs, **self.objectkwargs)
        inst._unitpertypelisthandles.append(h)
        setattr(inst, self.name, h)
        
    def Restore(self, instance, restorehelper):
        ''' Restores the object. '''
        super().Restore(instance, restorehelper)
        
        h = getattr(instance, self.name)
        owner = h.ownernumber
        unittype = h.unittype
        h.ownernumber = -1
        h.unittype = ''
        h.Update(owner, unittype)
        
# This shared class is needed because there are two types of units:
# Brush based and model based.
# Model based are dervied from CBaseAnimating (or CUnitBase here).
# Brush based from CBaseEntity.
# This class implements shared stuff.
class UnitBaseShared(object):
    """ Base class for units. Shared between buildings, soldiers, vehicles, etc. """
    def __init__(self):
        super().__init__()

        self.selected_by_players = set()
        self.drawselection = 0
        
        self._unitlisthandles = []
        self._unitpertypelisthandles = []

        self.abilities = {}
        self.abilitiesbyname = {}
        self.abilitycheckautocast = {}
        self.attributes = {}
        self.statuseffects = []
        self.rangebonus = {}
        
        self.unitinfo = self.unitinfofallback

    def PrecacheAbilities(self, abilities):
        for k, abi in abilities.items():
            try:
                if isinstance(abi, SubMenu):
                    self.PrecacheAbilities(abi.abilities)
                    continue
                PrecacheAbility(abi)
                GetTechNode(abi, self.GetOwnerNumber())
            except:
                print('#%d: An exception occurred while preaching ability %s in slot %s in unit %s (%s):' % (self.entindex(), abi, k, self.unitinfo.name, 'server' if isserver else 'client'))
                traceback.print_exc()
                continue

    def Restore(self, save):
        ret_value = super().Restore(save)
        # Need to retrieve unit info here because Precache is called next in the restore process
        self.UpdateUnitInfo()
        return ret_value
            
    def Precache(self):
        """ Precaches this unit.
        
            Calls precache on each ability this unit is able to do.
        """
        info = self.unitinfo

        # One time unit precache
        if info.name not in self.precacheregister:
            self.PrecacheUnitType(info)
            self.precacheregister.add(info.name)
        
        # Precache abilities
        self.PrecacheAbilities(info.abilities)
            
        for s in self.abilitysounds.values():
            self.PrecacheScriptSound(s)

        super().Precache()
        
    @classmethod
    def PrecacheUnitType(cls, info):
        """ Precaches the unit type.
            This is only once in a level for unit type per entity class.
            It's called on both server and clients.
        """
        # Precache particle system for selection
        PrecacheParticleSystem('unit_circle')
        PrecacheParticleSystem('unit_circle_ground')
        PrecacheParticleSystem('unit_square')
        
        # Precache sounds (if any)
        if info.sound_select:
            cls.PrecacheScriptSound(info.sound_select)
        if info.sound_move:
            cls.PrecacheScriptSound(info.sound_move)
        if info.sound_attack:
            cls.PrecacheScriptSound(info.sound_attack)
        if info.sound_jump:
            cls.PrecacheScriptSound(info.sound_jump)
        if info.sound_death:
            cls.PrecacheScriptSound(info.sound_death)
            
    @classmethod    
    def InitEntityClass(cls):
        """ Called upon the first time an entity class is defined or
            on level init for each entity class. """
        super().InitEntityClass()
        
        # Reset precache register for PrecacheUnitType
        cls.precacheregister = set()
            
    def Spawn(self):
        """ Called when the unit is spawned into the world.
        
            Copies the health and energy settings from the info class.
            Adds the unit to the unit list.
        """
        self.Precache()
        
        unitinfo = self.unitinfo
        if isserver:
            if self.health == 0:
                self.health = unitinfo.health 
            self.maxhealth = self.health
            self.energy = unitinfo.unitenergy_initial if unitinfo.unitenergy_initial != -1 else unitinfo.unitenergy
            # UpgradeFields may modify maxenergy, so prefer that over this. TODO: improvement desirable. Not very clear.
            if self.maxenergy == 0:
                self.maxenergy = unitinfo.unitenergy

            # Add to the global unit list
            self.handlesactive = True
            AddUnit(self)
        
        if isserver and self.fowflags:
            self.AddFOWFlags(self.fowflags)
    
        super().Spawn()

        if isserver:
            self.UpdateAbilities()
            self.SetInitialAbilityRechargeTimes()

            self.RebuildAttackInfo()
            self.BuildAttributeProperties()
            
            self.OnTeamColorChanged()

            FireSignalRobust(unitspawned, unit=self)
            
    def OnRestore(self):
        super().OnRestore()
        
        # Needed to ensure mins/maxs are calculated
        if self.unitinfo.requiresetup:
            self.unitinfo.Setup()
        
        # Add to the global unit list
        self.handlesactive = True
        AddUnit(self)

        self.RebuildAttackInfo()
        self.UpdateAbilities()
        self.BuildAttributeProperties()
           
    if isclient:
        def OnDataChanged(self, type):
            super().OnDataChanged(type)
            
            if type == DATA_UPDATE_CREATED:
                self.OnDataUpdateCreated()
                    
        def OnDataUpdateCreated(self):
            """ Convenient method for doing something on being created.
                At this point most of the initially data is valid on 
                the client (like the origin).
            """
            # Add to the global unit list
            self.handlesactive = True
            AddUnit(self)
            
            self.UpdateAbilities()
            self.RebuildAttackInfo()
            self.BuildAttributeProperties()
            
            self.OnTeamColorChanged()
            
            FireSignalRobust(unitspawned, unit=self)
            
            if self.ShouldAlwaysShowBars():
                self.ShowBars()
                
            self.UpdateTeamColorGlow()
               
    def UpdateOnRemove(self):
        """ Cleans up the unit when removed.
        
            Removes the unit from the unit list.
            Shutsdown the selection circle in case active.
        """
        # Remove from the global unit list
        if self.handlesactive:
            RemoveUnit(self)
            
            self.handlesactive = False

        self.attributes.clear()
        self.attacks = []

        self.RemoveFromParticipatingAbilities()
        self.DestroyCoverSpots()
            
        FireSignalRobust(unitremoved, unit=self)

        if isclient:
            self.ClearSelectionCircle()
            self.HideBars()
            self.HideChannelBar()
            
        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()

        if __debug__:
            mem_debug.CheckRefDebug(self)

    def GetIndexForAbility(self, abi_name):
        """ Returns the slot index of the given ability.
        
            If the unit does not have this ability, it returns None.
            
            Args:
                abi_name (str): ability name
        """
        assert(self.GetUnitType() != None)
        info = GetUnitInfo(self.GetUnitType(), fallback=None)
        if not info:
            return None
        for k, v in info.abilities.items():
            try:
                abiinfo = info.GetAbilityInfo(info, v, self.GetOwnerNumber())
            except NoSuchAbilityError:
                continue
            if abiinfo and abiinfo.name == abi_name:
                return k
        return None
        
    def DoAbility(self, abi_name, mouse_inputs=[], autocasted=False, queueorder=False, **kwargs):
        """ Execute an ability given a sequence of mouse inputs.
        
            This method is for cpu players, auto casting or order overriding.
            
            Args:
                abi_name (str): ability name
                
            Kwargs:
                mouse_inputs (list): mouse inputs to be inserted to the ability
                autocasted (bool): mark as autocasted
                queueorder (bool): whether or not to cancel the other active orders
                player (entity): optional player to be used as input for ability
        """
        assert not isclient, 'DoAbility can only be executed from Server'
        buttons = IN_SPEED if queueorder else 0
        player = SimulatedPlayer(self.GetOwnerNumber(), selection=[self.GetHandle()], buttons=buttons)
        return DoAbilitySimulated(player, abi_name, unittype=self.GetUnitType(), mouse_inputs=mouse_inputs,
                                  autocasted=autocasted, **kwargs)
                    
    def UpdateAbilities(self, abilitiesmap=None):
        """ Creates an optimized map of abilities.
        
            The map contains direct references to the abilities, 
            so we don't need to look them up.
            It also creates a list of abilities that require autocast checking.
            
            This method must be called on change.
            
            Kwargs:
                abilitiesmap (dict): used for recursive building abilities (i.e. sub menus)
        """
        if not self.handlesactive:
            return
            
        unitinfo = self.unitinfo

        if not abilitiesmap:
            abilitiesmap = unitinfo.abilities
            self.abilities = {}
            self.abilitiesbyname = {}
            
        for slot, abi_name in abilitiesmap.items():
            try:
                info = unitinfo.GetAbilityInfo(abi_name, self.GetOwnerNumber())
            except NoSuchAbilityError:
                print('#%d: Invalid ability %s in slot %s in unit %s ability dict!' % (self.entindex(), abi_name, slot,
                                                                                       unitinfo.name))
                continue
            except:
                print('#%d: An exception occurred while importing ability %s in slot %s in unit %s (%s):' % (
                    self.entindex(), abi_name, slot, unitinfo.name, 'server' if isserver else 'client'))
                traceback.print_exc()
                continue
                
            if not info:
                continue
                
            if not info.ShouldShowAbility(self):
                continue
                
            # Special case. Note that it just inserts all abilities
            # into our map. Sub menus only exist hud technically.
            if issubclass(info, AbilityMenuBase):
                self.UpdateAbilities(info.abilities)

            self.abilities[info.uid] = info
            self.abilitiesbyname[info.name] = info
            
            try:
                info.SetupOnUnit(self)
            except:
                print('#%d: An exception occurred while setting up ability %s in slot %s on unit %s (%s):' % (
                    self.entindex(), abi_name, slot, unitinfo.name, 'server' if isserver else 'client'))
                traceback.print_exc()
                continue
                
            if info.supportsautocast and info.uid not in self.abilitycheckautocast:
                self.abilitycheckautocast[info.uid] = info.defaultautocast

        self.UpdateAutocastLists()
        
        if isclient and self.selected:
            ScheduleFireSignalRobust(refreshhud)

    def SetInitialAbilityRechargeTimes(self):
        """ Set initial recharge for abilities that require it
            Should be called upon Spawn of unit.

            In some cases this may be called at a later point, like when the building is constructed.
            It's up to the unit implementation to call this when the unit type changes, that requires this to retrigger.
        """
        for uid, ability in self.abilities.items():
            if ability.set_initial_recharge:
                self.abilitynexttime[uid] = gpGlobals.curtime + ability.rechargetime

    def IsAbilityRecharging(self, name):
        return self.abilitynexttime[name] > gpGlobals.curtime

    def RemoveFromParticipatingAbilities(self):
        for abi in self.participating_abilities:
            abi.OnUnitRemoved(self)
    
    # TODO: Move this into Basecombat, it's pretty much specific to basecombat only
    def UpdateAutocastLists(self):
        self.checkautocastonidle = []
        self.checkautocastonenemy = []
        self.checkabilities = []
        for uid, info in self.abilities.items():
            if hasattr(info, 'OnUnitThink'):
                self.checkabilities.append(info)
            if not info.supportsautocast:
                continue
            if uid not in self.abilitycheckautocast or not self.abilitycheckautocast[uid]:
                continue
            if info.autocastcheckonidle:
                self.checkautocastonidle.append(info)
            if info.autocastcheckonenemy:
                self.checkautocastonenemy.append(info)
                if info.checkautocastinenemyrange and self.senses:
                    self.senses.AddEnemyInRangeCallback(self.CheckAutCastOnEnemyCallback, int(info.checkautocastinenemyrange), 3.0)
                    
    def AllowAutoCast(self):
        return True
                    
    def CheckAutCastOnEnemyCallback(self):
        if not self.AllowAutoCast():
            return
        for abi in self.checkautocastonenemy:
            if abi.CheckAutoCast(self):
                return
                
    def TargetOverrideOrder(self, unit, data, selection, angle=None, player=None):
        """ Allows overriding the order of an unit targeting this unit.
            Note: Might not be the active order. 
            
            Args:
               unit (entity): The unit targeting this unit.
               data (MouseTraceData): Mouse data containing the target position + other information.
               selection (list): Selection of the unit is part during the order.
               
            Kwargs:
                angle (QAngle): Angle between the pressed and released order position. Might be None.
               player (entity): Player ordering the unit. Might be None
               
            Returns True if a new order was inserted. False to indicate the default unit order rules should be used.
        """
        return False
        
    def TargetOverrideGroupOrder(self, player, data):
        """ Allows overriding the default group order.
        
            Args:
                player (entity): the player executing the group order
                data (MouseTraceData): Mouse data containing the target position + other information
        
            Returns a new group order instance to override the default.
        """
        return None
                
    def IsStatusEffectActive(self, name):
        return next((se for se in self.statuseffects if se.name == name), None) is not None

    def GetStatusEffect(self, name):
        return next((se for se in self.statuseffects if se.name == name), None)

    def StatusEffectsThink(self, think_freq):
        for se in self.statuseffects:
            se.Update(think_freq)
                
    @property
    def activeability(self):
        return False
    
    def GetRequirements(self, requirements, info, player):
        # Add cloaked requirement
        if self.cloaked and not getattr(info, 'cloakallowed', False):
            requirements.add('cloaked')
        # Should not be stunned
        if self.stunned:
            requirements.add('stunned')
                
    def OnChangeOwnerNumber(self, oldownernumber):
        """ Called when the unit ownernumber changes. 
            Updates unit list.
        """
        super().OnChangeOwnerNumber(oldownernumber)
    
        # Change in the global unit list
        if self.handlesactive:
            ChangeUnit(self, oldownernumber) 
            
        # Update handles
        [ h.Update(self.GetOwnerNumber()) for h in self._unitlisthandles ]
        [ h.Update(self.GetOwnerNumber(), self.GetUnitType()) for h in self._unitpertypelisthandles ]
            
        # Precache abilities
        info = GetUnitInfo(self.GetUnitType(), fallback=None)
        if info:
            for k, abi in info.abilities.items():
                GetTechNode(abi, self.GetOwnerNumber())
                
        self.UpdateAbilities()
                    
        # On the client, update our team color stored in (used by shaders that do team coloring)
        self.OnTeamColorChanged()
        
        # Notify fields that want to know this
        for field in self.ownernumberchangemap.values():
            try:
                field.OnChangeOwnerNumber(self, oldownernumber)
            except:
                traceback.print_exc()
            
        if isserver and (self.GetFOWFlags() & FOWFLAG_INITTRANSMIT) != 0:
            # Force this entity to send at least one transmission to the old players to update correctly.
            # Otherwise it will show on the client as the old owner still owning this point (until the owner discovered it again).
            # Only done for FOWFLAG_INITTRANSMIT right now (which is for neutral buildings/control points).
            for i in range(0, MAX_PLAYERS):
                player = UTIL_PlayerByIndex(i)
                if not player or not player.IsConnected():
                    continue
                if self.IsInFOW(player.GetOwnerNumber()):
                    continue
                self.FOWForceUpdate(i)
           
        if isserver:
            FireSignalRobust(unitchangedownernumber, unit=self, oldownernumber=oldownernumber)

    if isserver:
        def OnPlayerDefeated(self):
            """ Called by game rules when the player owning this unit is defeated. """
            pass
        
    def OnUnitTypeChanged(self, oldunittype):
        """ Called when the unit type changes. Updates population. """
        super().OnUnitTypeChanged(oldunittype)

        self.UpdateUnitInfo()
        
        info = self.unitinfo

        if self.handlesactive:
            unitpopulationcount[self.GetOwnerNumber()] -= self.population
            unitpopulationcount[self.GetOwnerNumber()] += info.population
            ChangeUnitType(self, oldunittype)
        self.population = info.population

        [ h.Update(self.GetOwnerNumber(), self.GetUnitType()) for h in self._unitpertypelisthandles ]
        
        self.selectionpriority = info.selectionpriority
        self.attackpriority = info.attackpriority
        self.accuracy = info.accuracy
        if isserver:
            self.viewdistance = info.viewdistance
        
        if self.handlesactive:
            self.UpdateAbilities()
            self.BuildAttributeProperties()

    def UpdateUnitInfo(self):
        self.unitinfo = GetUnitInfo(self.GetUnitType(), fallback=self.unitinfofallback)
        if not issubclass(self.unitinfo, self.unitinfovalidationcls):
            PrintWarning('#%d: Unit %s at %s has invalid unit type %s! Using fallback instead.\n' % (self.entindex(), self.GetClassname(), self.GetAbsOrigin(), self.GetUnitType()))
            self.unitinfo = self.unitinfofallback
        
    def AddAttribute(self, attr):
        try:
            self.attributes[attr.name] = attr(self)
        except AttributeError:
            return # Contains string, so not initialized yet
            
    def RemoveAttribute(self, attr):
        try:
            del self.attributes[attr.name]
        except KeyError:
            PrintWarning('UnitBaseShared.RemoveAttribute: Unit has no attribute %s\n' % (attr.name))
                
    def BuildAttributeProperties(self):
        """ Build dictionary of attributes of this unit.
        
            When changing the attributes dictionary format, also update core.units.info.UnitInfo.AttackBase). 
        """
        info = self.unitinfo
        self.attributes.clear()
        for order, attr in enumerate(info.attributes):
            attr.order = order + 1
            self.AddAttribute(attr)

    def InitializeAttributes(self, info_attributes):
        """ Turns list of attributes into dictionary with instantiated attributes. """
        attributes = {}
        for order, attr in enumerate(info_attributes):
            attr.order = order + 1
            attributes[attr.name] = attr(self)
        return attributes
            
    def GetActiveAttributes(self):
        """ Returns the active set of attributes on this unit.
            For combat units, this returns the combined attributes of the unit and attacks.
            Mainly used for displaying the attributes in the hud.
        """
        return self.attributes
                
    def OnTeamColorChanged(self):
        if isclient:
            c = dbplayers[self.GetOwnerNumber()].color if self.overrideteamcolor is None else self.overrideteamcolor
            self.SetTeamColor(Vector(c.r()/255.0, c.g()/255.0, c.b()/255.0))
            
            if self.selectionparticle:
                self.selectionparticle.SetControlPoint(self.selectionparticlecolorcp, self.GetTeamColor())

    def CanPlayerControlUnit(self, player):
        """ Base method for checking if a player can control this unit. """
        if player.GetOwnerNumber() != self.GetOwnerNumber():
            return False
        return not self.uncontrollable
        
    def IsTargetable(self, ownernumber):
        """ Is this unit targetable by the given ownernumber?. """
        if self.cloaked and not self.detected:
            if relationships[(ownernumber, self.GetOwnerNumber())] != D_LI:
                return False
        return self.IsAlive()
        
    def IsSelectableByPlayer(self, player, target_selection):
        """ By default we are always selectable. target_selection is a list of units we are targeted to be added to. """
        if not self.IsTargetable(player.GetOwnerNumber()):
            return False
        if not self.IsAlive():
            return False
        if len(target_selection) == 1:
            if target_selection[0].GetOwnerNumber() != player.GetOwnerNumber():
                return False
            if target_selection[0].GetOwnerNumber() != self.GetOwnerNumber():
                return False
        elif len(target_selection) > 0:
            # Don't mix units of other players into the selection
            if self.GetOwnerNumber() != player.GetOwnerNumber():
                return False
            # Does not make sense to mix uncontrollable in the selection
            if len(target_selection) > 1 and self.uncontrollable:
                return False
        return True
            
    def OnSelected(self, player):
        """ Called when the unit is selected by the given player.
            When selected always create a selection circle if projectedtexturepath is set.
        """
        super().OnSelected(player)
        
        self.selected = True
        self.selected_by_players.add(player)
        self.drawselection += 1
        self.CheckDrawSelection()
        if isclient and len(player.GetSelection()) == 1:
            self.PlaySelectedSound()
        
        responses = unitselected.send_robust(None, player=player, unit=self)
        for r in responses:
            if isinstance(r[1], Exception):
                PrintWarning('Error in receiver %s (module: %s): %s\n' % (r[0], r[0].__module__, r[1]))
                
        if isserver:
            if unit_debugoverlay.GetString():
                overlays = unit_debugoverlay.GetString().split()
                for overlay in overlays:
                    try:
                        self.debugoverlays = self.debugoverlays | getattr(self, overlay)
                    except AttributeError:
                        continue

    def OnDeSelected(self, player):
        """ Called when the unit is deselected by the given player.
            Shutdown selection circle.
        """
        super().OnDeSelected(player)
        self.selected = False
        self.selected_by_players.remove(player)
        self.drawselection -= 1
        self.CheckDrawSelection()
        
        responses = unitdeselected.send_robust(None, player=player, unit=self)
        for r in responses:
            if isinstance(r[1], Exception):
                PrintWarning('Error in receiver %s (module: %s): %s\n' % (r[0], r[0].__module__, r[1]))
                
        if isserver:
            if unit_debugoverlay.GetString():
                self.debugoverlays = 0
                
    if isclient:
        @property
        def order_sounds_disabled(self):
            return cl_unit_disable_order_sounds.GetBool()

        def PlaySelectedSound(self):
            """ Plays selected soundscript using the setting from the info class. """
            if not self.unitinfo.sound_select or self.order_sounds_disabled:
                return
            if UnitBaseShared.nextplayselectsound < gpGlobals.curtime:
                self.EmitAmbientSound(-1, self.GetAbsOrigin(), self.unitinfo.sound_select)
                UnitBaseShared.nextplayselectsound = gpGlobals.curtime + 7.0
                
        def PlayOrderSound(self, soundscript, nextsounddelay=4.5, force=False):
            if not soundscript or self.order_sounds_disabled:
                return
            if UnitBaseShared.nextordersound < gpGlobals.curtime or force:
                self.EmitAmbientSound(-1, self.GetAbsOrigin(), soundscript)
                UnitBaseShared.nextordersound = gpGlobals.curtime + nextsounddelay
                
    def GetAbilitySound(self, soundscriptdesired):
        """ Translates soundscript symbol to desired soundscript.
            This is used in case different units should use a different soundscript. 
        """
        return self.abilitysounds.get(soundscriptdesired, '')
        
    def CreateParticleSelectionEffect(self):
        self.selectionparticle = self.ParticleProp().Create(self.selectionparticlename, PATTACH_ABSORIGIN_FOLLOW)
        self.selectionparticle.SetControlPoint(self.selectionparticlecolorcp, self.GetTeamColor())
        radius = self.CollisionProp().BoundingRadius2D()
        self.selectionparticle.SetControlPoint(2, Vector(radius*self.scaleprojectedtexture, radius*self.scaleprojectedtexture, 0))
        
    def CheckDrawSelection(self):
        if not isclient or not self.selectionparticlename:
            return
        if not self.IsAlive():
            self.ClearSelectionCircle()
            return
        if self.handlesactive and self.drawselection > 0:
            if not self.selectionparticle:
                self.CreateParticleSelectionEffect()
        elif self.drawselection <= 0:
            self.ClearSelectionCircle()
                
    def ClearSelectionCircle(self):
        if self.selectionparticle:
            self.ParticleProp().StopEmission(self.selectionparticle, False, False, True)
            self.selectionparticle = None
                
    if isclient:
        def OnInSelectionBox(self):
            self.drawselection += 1
            self.CheckDrawSelection()
            
        def OnOutSelectionBox(self):
            self.drawselection -= 1
            self.CheckDrawSelection()
    
    def Order(self, player):
        """ Called on right click when the unit is selected by the player.

            Args:
                player (entity): handle to entity of player.
        """
        pass
        
    # Energy management
    def UpdateEnergy(self, interval):
        """ Regenerates energy based on the interval argument and energy settings.

            Args:
                interval (float): update interval (i.e. 0.1 seconds)
        """
        if self.energy >= self.maxenergy and not self.energyregenrate < 0:
            return

        self.energyregenim += interval*self.energyregenrate
        
        if self.energyregenim > 1:
            adde = int(floor(self.energyregenim))
            self.energyregenim -= adde
            self.energy = max(0, min(self.maxenergy, self.energy + adde))
        elif self.energyregenim < -1:
            adde = int(floor(abs(self.energyregenim)))
            self.energyregenim += adde
            self.energy = max(0, min(self.maxenergy, self.energy - adde))
        
    def TakeEnergy(self, energy):
        """ Takes energy from unit.

            Args:
                energy (int): energy to take

            Returns:
                bool: True if successful, False otherwise.
        """
        assert(energy >= 0)
        if energy > self.energy:
            return False
        self.energy = int(min(self.maxenergy, self.energy - energy))
        return True
        
    def GiveEnergy(self, energy):
        """ Give energy to unit.

            Args:
                energy (int): energy to give
        """
        self.energy = int(min(self.maxenergy, self.energy + energy))
        
    # Cloaking support
    def Cloak(self):
        if self.cloaked:
            return
        self.cloaked = True
        self.SetUseCustomCanBeSeenCheck(True)
        self.energyregenrate -= self.cloakenergydrain
        
    def UnCloak(self):
        if not self.cloaked:
            return
        self.cloaked = False
        self.SetUseCustomCanBeSeenCheck(False)
        self.energyregenrate += self.cloakenergydrain
        
    def CustomCanBeSeen(self, unit=None):
        if self.cloaked:
            if unit:
                if unit.IRelationType(self) == D_HT and getattr(unit, 'detector', False):
                    self.SetThink(self.DetectedEndThink, gpGlobals.curtime + 0.5, 'DetectedEndThink')
                    self.detected = True
            return self.detected
        return True
        
    def DetectedEndThink(self):
        self.detected = False
        
    def OnCloakChanged(self):
        """ Triggered when client side cloaked variable changes. """
        # TODO: Push update for hud
        if self.cloaked:
            self.ForceUseFastPath(False) # ForcedMaterialOverride does not work if fast path model rendering is used
            self.ForcedMaterialOverride(self.cloakmaterial)
        else:
            self.ForceUseFastPath(True)
            self.ForcedMaterialOverride(None)
            
        self.UpdateTeamColorGlow()
        
        FireSignalRobust(minimapupdateunit, unit=self)
            
    def OnDetectedChanged(self):
        self.OnCloakChanged()
        self.ForcedMaterialOverride(self.detectedmaterial if self.detected else self.cloakmaterial)
        
    def OnStunnedChanged(self):
        if self.stunned:
            maxs = self.CollisionProp().OBBMaxs()
            self.stunnedparticle = self.ParticleProp().Create(self.stunnedparticlename, 
                PATTACH_CUSTOMORIGIN_FOLLOW, -1, Vector(0,0,maxs.z+self.barsoffsetz))
            self.stunnedparticle.SetControlPoint(1, self.GetTeamColor())
            radius = self.CollisionProp().BoundingRadius2D() * 1.4
            self.stunnedparticle.SetControlPoint(2, Vector(radius, 0, 0))
        else:
            if self.stunnedparticle:
                self.ParticleProp().StopEmission(self.stunnedparticle, False, False, True)
                self.stunnedparticle = None

    if isserver:
        def Event_Killed(self, info):
            super().Event_Killed(info)
            
            # Stop displaying stunned effect
            self.stunned = False

            self.RemoveFromParticipatingAbilities()
            self.DestroyCoverSpots()
            
            attacker = info.GetAttacker()
            self.onkilled.Set('', attacker if attacker else self, self)
            FireSignalRobust(unitkilled, unit=self, dmginfo=info)
            
            FireSignalRobust(unitkilled_by_victim[self.unitinfo.name], unit=self, dmginfo=info)
            if attacker and attacker.IsUnit():
                FireSignalRobust(unitkilled_by_attacker[attacker.unitinfo.name], unit=self, dmginfo=info)
                
            inflictor = info.GetInflictor()
            if inflictor and inflictor.IsUnit():
                FireSignalRobust(unitkilled_by_inflictor[inflictor.unitinfo.name], unit=self, dmginfo=info)
        
        # Count kills
        def Event_KilledOther(self, victim, info):
            super().Event_KilledOther(victim, info)
            
            self.kills += 1
            
        # Generic suicide method
        def Suicide(self):
            self.health= 0
            info = CTakeDamageInfo(self, self, 0, DMG_BLAST|DMG_ALWAYSGIB)
            self.Event_Killed(info)
            # Only classes that specifically request it are gibbed
            if self.ShouldGib(info):
                self.Event_Gibbed(info)
            else:
                self.Event_Dying()
    
        # Direct Control methods
        def OnUserControl(self, player):
            """ Called when a player takes control of this unit. """
            super().OnUserLeftControl(player)
            self.controllerplayer = player # Note: None on the client side except for the local player
            self.controlledbyplayer = player.entindex()
            
        def OnUserLeftControl(self, player):
            """ Called when a player leaves control of this unit. """
            super().OnUserLeftControl(player)
            self.controllerplayer = None
            self.controlledbyplayer =  None
    else:
        # Direct Control methods on client
        def OnUserControl(self, player):
            """ Called when a player takes control of this unit. """
            super().OnUserLeftControl(player)
            self.controllerplayer = player # Note: None on the client side except for the local player
            
        def OnUserLeftControl(self, player):
            """ Called when a player leaves control of this unit. """
            super().OnUserLeftControl(player)
            self.controllerplayer = None
            
        def OnButtonsChanged(self, buttons, buttonschanged):
            ''' The player controlling this unit changed
                button states. '''
            if buttonschanged & IN_SPEED:
                if buttons & IN_SPEED:
                    self.controllerplayer.SetForceShowMouse(True)
                else:
                    self.controllerplayer.SetForceShowMouse(False)
                    
    def AddRangeBonus(self, key, bonus):
        """ Adds a range bonus to the unit.
            This increases the weapon range + sensing range.
            Automatically removes the existing named bonus if
            it already exists.

            Args:
                key (str): Identifier for range bonus.
                bonus (float): range bonus to apply
        """
        if key in self.rangebonus:
            self.RemoveRangeBonus(key)
        self.rangebonus[key] = bonus
        
        self.RebuildAttackInfo()
        self.UpdateSensingDistance()
        
    def RemoveRangeBonus(self, key):
        """ Removes a range bonus.

            Args:
                key (str): Identifier for range bonus.
        """
        try:
            del self.rangebonus[key]
        except KeyError:
            DevMsg(1, 'UnitBaseCombat.RemoveRangeBonus: no range bonus %s\n' % (key))
            
        self.RebuildAttackInfo()
        self.UpdateSensingDistance()
        
    def UpdateSensingDistance(self):
        pass
        
    # Used by the ai to find out how close we need to be to attack
    def RebuildAttackInfo(self):
        if not self.IsAlive() or self.cloaked:
            self.attacks = []
            self.UpdateAttackInfo()
            return

        h = self.GetHandle()
        # Instantiate each attack, so we can modify damage
        self.attacks = [a(unit=h) for a in self.unitinfo.attacks]

        # Add weapon attacks
        weapon = self.activeweapon
        if weapon:
            if weapon.AttackPrimary:
                attack = weapon.AttackPrimary(unit=h)
                attack.weapon = weapon
                self.attacks.append(attack)
            if weapon.AttackSecondary:
                attack = weapon.AttackSecondary(unit=h)
                attack.weapon = weapon
                self.attacks.append(attack)

        # Add ability autocast attacks (if the autocast is active)
        for uid, info in self.abilities.items():
            if not info.supportsautocast or not info.autocast_attack:
                continue
            if uid not in self.abilitycheckautocast or not self.abilitycheckautocast[uid]:
                continue
            self.attacks.append(info.autocast_attack(unit=self))

        # Apply range bonus
        for attack in self.attacks:
            for rangebonus in self.rangebonus.values():
                attack.maxrange += rangebonus

            if attack.weapon:
                attack.weapon.UpdateAttackSettings(attack)
        
        self.UpdateAttackInfo()
        
    def GetAttack(self, name):
        for att in self.attacks:
            if att.__class__.__name__ == name:
                return att
        return None
            
    def UpdateAttackInfo(self):
        self.maxattackrange = 0.0
        self.minattackrange = float('inf')
        self.minattackcone = 10.0
        
        if not self.attacks:
            return
            
        for attack in self.attacks:
            if attack.ShouldUpdateAttackInfo(self):
                self.maxattackrange = max(self.maxattackrange, attack.maxrange)
                self.minattackrange = min(self.minattackrange, attack.minrange)
                self.minattackcone = min(self.minattackcone, attack.cone)
                
        if self.unitinfo.engagedistance:
            self.engagedistance = self.unitinfo.engagedistance
        elif self.maxattackrange < 200.0: # For typical melee units, default to the view distance
            self.engagedistance = self.unitinfo.viewdistance
        else: # For range units, default to the max attack distance
            self.engagedistance = self.maxattackrange
            
    # Damage taking
    def ScaleDamageToAttributes(self, dmg_info, my_attributes):
        """ Modify damage according to the attributes of these units. """
        attacker = dmg_info.GetAttacker()
        if not attacker.IsUnit():
            attacker = None

        att_attributes = dmg_info.attributes or (attacker and attacker.attributes) or None
        if not att_attributes:
            # Nothing to do. Could be that attacker died. Above system with relying on attacker won't work
            # correctly with projectiles that take time to reach a target...
            return dmg_info

        # print('#%d my attributes: %s' % (self.entindex(), str(my_attributes)))
        # print('#%d attacker attributes: %s' % (self.entindex(), str(att_attributes)))

        # Apply damage bonus modifiers
        for attattr in att_attributes.values():
            dmgmodifiers = attattr.dmgmodifiers
            if None in dmgmodifiers:  # vs ALL
                dmgmodifiers[None](dmg_info)

            for attr in my_attributes.values():
                if attr.name in dmgmodifiers:
                    # print('#%d Att Applying %s to %s' % (self.entindex(), attattr.name, attr.name))
                    dmgmodifiers[attr.name](dmg_info)

            # Let the attribute do whatever it wants (if anything)
            if attattr.ApplyToTarget is not None:
                attattr.ApplyToTarget(self, dmg_info)

        # Apply recv damage modifiers
        for attr in my_attributes.values():
            dmgrecvmodifiers = attr.dmgrecvmodifiers
            if None in dmgrecvmodifiers:  # vs ALL
                dmgrecvmodifiers[None](dmg_info)

            for attattr in att_attributes.values():
                if attattr.name in dmgrecvmodifiers:
                    # print('#%d Recv Applying %s to %s' % (self.entindex(), attr.name, attattr.name))
                    dmgrecvmodifiers[attattr.name](dmg_info)

            # Let the attribute do whatever it wants (if anything)
            if attr.ApplyToReceiver is not None:
                attr.ApplyToReceiver(self, dmg_info)
        
        # reduce damage if attacker is lower tier
        if attacker and attacker.unitinfo.tier is not 0 and self.IsUnit() and self.unitinfo.tier is not 0 and attacker.unitinfo.tier < self.unitinfo.tier:
            dmg_info.ScaleDamage(0.5)
        
        return dmg_info
          

    def OnTakeDamage(self, dmg_info):
        """ Applies damage to the unit.
            Scales the damage depending on unit attributes.
        """
        if unit_nodamage.GetBool():
            return 0

        self.lasttakedamage = gpGlobals.curtime
        if not getattr(self, 'isbuilding', False):
            DoNotificationEnt('unit_underattack', self, filter=GetNotifcationFilterForOwnerAndAllies(self.GetOwnerNumber())) 
        else:
            DoNotificationEnt('building_underattack', self, filter=GetNotifcationFilterForOwnerAndAllies(self.GetOwnerNumber())) 

        return super().OnTakeDamage(self.ScaleDamageToAttributes(dmg_info, self.attributes))
        
    # Inputs
    @input(inputname='MakeImmortal', helpstring='Make the unit immortal')
    def InputMakeImmortal(self, inputdata):
        self.takedamage = DAMAGE_NO
        
    @input(inputname='MakeMortal', helpstring='Make the unit mortal')
    def InputMakeMortal(self, inputdata):
        self.takedamage = DAMAGE_YES
        
    @input(inputname='MakeUncontrollable', helpstring='Make the unit uncontrollable')
    def InputMakeUncontrollable(self, inputdata):
        self.uncontrollable = True
        
    @input(inputname='MakeControllable', helpstring='Make the unit controllable again')
    def InputMakeControllable(self, inputdata):
        self.uncontrollable = False

    #: Contains the used cover spot ids as keys and the values with an handle of the unit using the spot.
    used_cover_spots = dict()
    #: Contains additional information of a created cover spot
    cover_spots_info = dict()
    #: Map created cover spots are always of type 1 for now.
    default_cover_spot = CoverSpot(1)

    def CreateCoverSpots(self, cover_spots):
        """ Creates hiding/cover spots if any.

            Args:
                cover_spots (CoverSpot): Information of the cover spot (offset, type, angle). Updated with the spot id.
        """
        # Bug out if we already have cover spots. Call DestroyCoverSpots if this is not desired.
        if self.cover_spots:
            return

        origin = self.GetAbsOrigin()
        offset = Vector()
        yaw = self.GetAbsAngles().y
        for cover_spot in cover_spots:
            VectorYawRotate(cover_spot.offset, yaw, offset)
            targetpos = origin + offset
            tr = trace_t()
            UTIL_TraceLine(targetpos, targetpos - Vector(0, 0, MAX_TRACE_LENGTH), MASK_SOLID, self, COLLISION_GROUP_NONE, tr)
            targetpos = tr.endpos
            spotid = CreateHidingSpot(targetpos, True, False)
            if spotid != -1:
                cover_spot.id = spotid
                self.cover_spots_info[spotid] = cover_spot
                self.cover_spots.append((spotid, targetpos))

    def DestroyCoverSpots(self):
        """ Destroys hiding/cover spots created by unit.
        """
        if not self.cover_spots:
            return
        for spotid, position in self.cover_spots:
            unit = self.used_cover_spots.get(spotid, None)
            if unit:
                unit.FreeCoverSpot()
            del self.cover_spots_info[spotid]
            DestroyHidingSpotByID(position, spotid)
        self.cover_spots = []
        
    if isserver:
        # Debug (Use bits in range 0x00001000 - 0x00800000)
        OVERLAY_UNITSAI = 0x00010000
        
        def DrawDebugGeometryOverlays(self):
            super().DrawDebugGeometryOverlays()
            
            if self.debugoverlays & self.OVERLAY_UNITSAI:
                if self.sai_group: self.sai_group.DrawDebugUnit(self)
        
    if isclient:
        # See overrideaccuracy
        def OnAccuracyChanged(self):
            self.accuracy = self.overrideaccuracy
            if self.selected:
                ScheduleFireSignalRobust(refreshhud)
            
        def OnCheckAutocastChanged(self):
            self.RebuildAttackInfo()
            if self.selected:
                ScheduleFireSignalRobust(refreshhud)
            
        def ShouldShowChannelTimeBar(self):
            if not self.channeltime:
                return False
                
            player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
            if relationships[(player.GetOwnerNumber(), self.GetOwnerNumber())] != D_LI:
                return False
                
            return True
            
        def OnChannelTimeChanged(self):
            if self.ShouldShowChannelTimeBar():
                self.ShowChannelBar()
            else:
                self.HideChannelBar()
                
        channelbarscreen = None
        def ShowChannelBar(self):
            if self.channelbarscreen:
                return
                
            self.channelbarscreen = UnitChannelBarScreen(self)
        
        def HideChannelBar(self):
            if not self.channelbarscreen:
                return
                
            self.channelbarscreen.Shutdown()
            self.channelbarscreen = None
            
        healthbarscreen = None
        energybarscreen = None
        barsvisible = False
        
        def ShouldAlwaysShowBars(self):
            ''' In case this returns False, bars are only shown when the mouse hovers on the unit or when selected.
                In the other case it's always shown.
            '''
            return cl_alwaysshowhealthbars.GetBool()
            
        def ShowBars(self):
            if self.barsvisible:
                return
            self.healthbarscreen = UnitHealthBarScreen(self)
            
            if self.maxenergy > 0:
                self.energybarscreen = UnitEnergyBarScreen(self)
            
            self.barsvisible = True
            
        def HideBars(self):
            if not self.barsvisible:
                return
            if self.ShouldAlwaysShowBars():
                return
            self.healthbarscreen.Shutdown()
            self.healthbarscreen = None
            
            if self.energybarscreen:
                self.energybarscreen.Shutdown()
                self.energybarscreen = None
                
            self.barsvisible = False
        
        def OnCursorEntered(self, player):
            if not self.IsTargetable(player.GetOwnerNumber()):
                return # Do not shown bars in this care
            self.ShowBars()
            
        def OnCursorExited(self, player):
            self.HideBars()
            
        # What cursor should we show on hover?    
        def GetCursor(self):
            player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
            if not self.IsTargetable(player.GetOwnerNumber()):
                return cursors.GetCursor("resource/arrows/default_cursor.cur")
            if relationships[(player.GetOwnerNumber(), self.GetOwnerNumber())] == D_HT:
                return cursors.GetCursor("resource/arrows/attack_cursor.cur")
            return cursors.GetCursor("resource/arrows/select_cursor.cur")
            
        def UseTeamColorGlow(self):
            if not self.useteamcolorglow:
                return False
                
            # No team color glow while cloaked on enemy player screen!
            player = CHL2WarsPlayer.GetLocalHL2WarsPlayer()
            if self.cloaked and not self.detected and self.IRelationType(player) == D_HT:
                return False
                
            return True
            
        def UpdateTeamColorGlow(self):
            if self.UseTeamColorGlow():
                self.EnableTeamColorGlow()
            else:
                self.DisableTeamColorGlow()
                
        def ShowOnMinimap(self):
            # Don't show unit if cloaked and the player is an enemy
            if self.cloaked:
                player = CHL2WarsPlayer.GetLocalHL2WarsPlayer()
                if self.IRelationType(player) == D_HT:
                    return False
                    
            return True
        
    #: Access the unit info object.
    unitinfo = UnitFallBackInfo
    unitinfofallback = UnitFallBackInfo
    unitinfovalidationcls = UnitInfo # unitinfo should be of this type, otherwise fallback will be used!

    nextplayselectsound = 0.0
    nextordersound = 0.0
    lasttakedamageperowner = defaultdict(lambda: None)
    
    # Ability sound translate map (see GetAblitySound)
    abilitysounds = {}
    
    # Outputs
    onkilled = OutputField(keyname='OnUnitKilled')
    
    # Fields
    #: Index of the player that controls us directly
    controlledbyplayer = EHandleField(value=None, networked=True)
    controllerplayer = None
    #: List of next times we can do the ability in the slot
    abilitynexttime = DictField(networked=True, default=0.0)
    #: List of abilities for which we should check autocast
    abilitycheckautocast = DictField(networked=True, default=False, clientchangecallback='OnCheckAutocastChanged')
    #: Abilities in which we are participating in some way (but may not be the active ability).
    #: See core.abilities.base.AbilityBase.AddUnit and RemoveUnit.
    participating_abilities = ListField()
    #: Makes the unit uncontrollabe (i.e. can't give orders or do abilities, even if the player owns the unit)
    uncontrollable = BooleanField(value=False, networked=True, keyname='Uncontrollable')

    #: Energy regeneration per second .
    energyregenrate = FloatField(value=1)
    energyregenim = FloatField(value=0.0)
    
    #: Kill count of this unit
    kills = IntegerField(networked=True, value=0, cppimplemented=True)
    
    #: True if the unit is cloaked.
    cloaked = BooleanField(value=False, networked=True, clientchangecallback='OnCloakChanged')
    #: Energy drained while cloaked.
    cloakenergydrain = 2
    #: Material used when cloaked.
    cloakmaterial = 'models/cloak'
    #: Material used when detected while cloaked
    detectedmaterial = 'models/cloak_detected'
    #: True if detected while cloaked
    detected = BooleanField(value=False, networked=True, clientchangecallback='OnDetectedChanged')
    #: Detects cloaked units in sensing range.
    detector = BooleanField(value=False)
    #: Whether or not team color glow is allowed on this unit
    useteamcolorglow = BooleanField(value=False)
    #: Overrides the default team color
    overrideteamcolor = GenericField(value=None, networked=True, clientchangecallback='OnTeamColorChanged')
    #: True if stunned
    stunned = BooleanField(value=False, networked=True, clientchangecallback='OnStunnedChanged')
    #: Stunned particle reference
    stunnedparticle = None
    #: Particle effect for stunned system name
    stunnedparticlename = 'unit_stun'
    
    #: Overrides client accuracy. Normally we read the accuracy from the unit info, but sometimes we change it at other
    #: points.
    overrideaccuracy = FloatField(networked=True, value=1.0, clientchangecallback='OnAccuracyChanged')
    
    #: Tuple with start and end time channeling (shows a progress bar above the head of the unit)
    channeltime = GenericField(value=None, networked=True, clientchangecallback='OnChannelTimeChanged',
                               sendproxy=SendProxyAlliesOnly())
    
    # Data
    #: True in case this unit is selected by the player
    selected = False
    #: Set of players that have this unit selected
    selected_by_players = None
    #: Reference to the selection particle effect instance
    selectionparticle = None
    #: Selection Effect Particle Effect System name
    selectionparticlename = 'unit_circle'
    #: Control point of color for selection particle effect
    selectionparticlecolorcp = 1
    #: Scales the selection circle. By default it sizes to the units bounding radius
    scaleprojectedtexture = 1.0
    #: Changes the default unit bars y offset. Normally this shown just above the max unit height.
    barsoffsetz = FloatField(value=0.0)
    #: The amount of population this unit is taking, derived from the unit info definition.
    population = 0
    #: Used to determine if a building.
    isbuilding = False 
    #: Is a mountable turret
    ismountableturret = False
    #: Possible to garrison this unit
    garrisonable = False
    #: If this entity can capture control points
    cancappcontrolpoint = True
    #: Used by repair abilities to determine if we can repair this unit/building
    repairable = False 
    #: Fog of war flags applied in the init method
    fowflags = 0 
    #: Unit type
    unittype = StringField(value='unit_unknown', keyname='unittype', cppimplemented=True,
                           displayname='Unit Type', helpstring='Unit Type',
                           choices=[('unit_unknown', 'unit_unknown')])
    #: Auto calculated value based on attack ranges and weapon attack ranges.
    maxattackrange = 0.0
    #: Strategic AI group (if any)
    sai_group = None
    #: Last time taken damage by an attacker
    lasttakedamage = FloatField(value=0.0)
    #: Cover spots created by unit.
    cover_spots = ListField(value=[], save=False)
    
    if isclient:
        # Called when this is the only selected unit
        # Allows the unit panel class to be changed
        def UpdateUnitPanelClass(self):
            from core.hud.units import BaseHudSingleUnit
            self.unitpanelclass = BaseHudSingleUnit
    
        # A reference to the class of a panel
        # Shown when this is the only selected unit
        # Defaults to the panel that shows the selected units
        #unitpanelclass = BaseHudSingleUnit
        
    #: Used to determine if we can add the unit to the unit list.
    handlesactive = False
            
@networked
class UnitBase(UnitBaseShared, BaseClass):
    """ Base class for model based (not a brush) units."""
    if isserver:
        def __init__(self):
            super().__init__()
            
            if self.animeventmap:
                self.SetAnimEventMap(self.animeventmap)
    else:
        def __init__(self):
            super().__init__()
            
            # Shouldn't need to draw units at this distance
            self.SetDistanceFade(5000.0, 5000.0)
    
    @classmethod
    def PrecacheUnitType(cls, info):
        """ Precaches the unit type.
            This is only called one time per unit type in a level.
            It's called on both server and client one time.

            Args:
                cls (object): the unit class
                info (UnitInfo): Unit info definition
        """
        super().PrecacheUnitType(info)
        
        PrecacheParticleSystem(cls.stunnedparticlename)
        PrecacheParticleSystem(cls.selectionparticlename)
        
        # Precache unit model
        if info.modelname:
            cls.PrecacheModel(info.modelname)
        elif info.modellist:
            for modelname in info.modellist:
                cls.PrecacheModel(modelname)
        else:
            cls.PrecacheModel('models/error.mdl')
            
    def Precache(self):
        super().Precache()
        
        modelname = self.GetModelName()
        if modelname:
            self.PrecacheModel(modelname)
        
    # dtwatchent test code
    '''def PostConstructor(self, clsname):
        super().PostConstructor(clsname)
        
        from gameinterface import engine
        engine.ServerCommand('dtwatchent %d\n' % (self.entindex()))
        #engine.ServerCommand('dtwatchvar m_vecOrigin\n')
        #engine.ServerCommand('dtwatchvar m_angRotation\n')
        #engine.ServerCommand('dtwatchvar m_fViewDistance\n')
        
        engine.ServerExecute()'''
                    
    def Spawn(self):
        """ Called when the unit is spawned into the world.
            
            Sets the model and size of the unit using the info class.
        """
        super().Spawn()

        # Setup unit from unit info
        if isserver:
            self.SetUnitModel(modelname=self.GetModelName())

    def SetUnitModel(self, modelname=None):
        unitinfo = self.unitinfo
        if modelname:
            # TODO/FIXME: This potentially changes the unit mins/maxs to the wrong values
            if not unitinfo.mins or not unitinfo.maxs or (unitinfo.mins.IsZero() and unitinfo.maxs.IsZero()):
                unitinfo.mins = self.WorldAlignMins()
                unitinfo.maxs = self.WorldAlignMaxs()
        elif unitinfo.modelname:
            modelname = unitinfo.modelname
        elif unitinfo.modellist:
            modelname = random.choice(unitinfo.modellist)
        else:
            modelname = 'models/error.mdl'
            
        try:
            self.SetModel(modelname)
        except ValueError:
            # This can happen when we make changes using the attribute editor
            PrintWarning('SetUnitModel: model %s not precached. Doing late precache...\n' % (modelname))
            self.PrecacheModel(modelname)
            self.SetModel(modelname)
            
        if self.GetModelScale() != unitinfo.scale:
            self.SetModelScale(unitinfo.scale)
    
        if unitinfo.mins:
            if unitinfo.mins.IsZero() and unitinfo.maxs.IsZero():
                UTIL_SetSize(self, self.WorldAlignMins(), self.WorldAlignMaxs())
            else:
                UTIL_SetSize(self, unitinfo.mins, unitinfo.maxs)
            
    def ReceiveEvent(self, index, data):
        """ Called on SendEvent when filter matches the client
            Can be used to send small/fast events to client. """
        self.eventhandlers[index](self, data)
        
    def DoAnimation(self, animevent, data=0, extraorigins=[]):
        """ Use the data argument for anything you like. """
        if isserver:
            filter = CPVSFilter(self.GetAbsOrigin())
            for origin in extraorigins:
                filter.AddRecipientsByPVS(origin)
            filter.UsePredictionRules()
            self.SendEvent(filter, animevent, data)
        self.ReceiveEvent(animevent, data)

    @classmethod
    def ReplenishAllUnitsEnergy(cls):
        """ Replenish the energy of all units on the map. """
        for l in unitlist.values():
            for unit in l:
                unit.energy = unit.maxenergy
        
    # Activities + translation + events
    if isserver:
        def OnNewModel(self):
            self.UpdateTranslateActivityMap()
            
            self.ResetActivityIndexes()
            self.ResetEventIndexes()
    else:
        def ParseActivities(self):
            cls = self.__class__
            # First try to lookup the activity. If it fails register as new activity.
            # The lookup is needed because if you are both server and client, the activities are
            # shared in memory. Registering a new one will create a new index, which does not
            # match the activity. This is not the case on a dedicated server.
            for act in cls.activitylist: 
                actidx = self.LookupActivity(act)
                if actidx != ACT_INVALID:
                    setattr(cls, act, Activity(actidx))
                else:
                    actidx = ActivityList_IndexForName(act)
                    if actidx == ACT_INVALID:
                        ADD_ACTIVITY(cls, act)
                    else:
                        setattr(cls, act, Activity(actidx))
                        
            # If acttables contains a single table, then we allow acttables to be that table
            # Here we convert it to the format we want.
            if not cls.acttables or not type(list(cls.acttables.values())[0]) is dict:
                cls.acttables = {'default': cls.acttables}
                        
            # Activities are parsed. Create the act translation map.
            # Convert strings to activities and then create the map
            cls.acttransmaps = {}
            for name in cls.acttables.keys():
                acttable = cls.ParseActTable(cls, cls.acttables[name])
                cls.acttransmaps[name] = TranslateActivityMap(acttable)
                
            # Parse events on client
            cls.ParseEvents(cls, cls.events)
        
        def OnNewModel(self):
            super().OnNewModel()
            
            if not engine.IsClientLocalToActiveServer():
                ResetActivityIndexes(self.GetModelPtr())
                ResetEventIndexes(self.GetModelPtr())
            
            # force animation event resolution!
            VerifySequenceIndex(self.GetModelPtr())
            
            # Per class this should be a one time initialization
            cls = self.__class__
            if not getattr(cls, '%s_activitiesparsed' % cls.__name__):
                setattr(cls, '%s_activitiesparsed' % cls.__name__, True)
                self.ParseActivities()
                self.PostParseActivities()

            self.UpdateTranslateActivityMap()

        def OnUnitBlinkChanged(self):
            if self.enableunitblink:
                self.Blink(-1)
            else:
                self.Blink(0)
                
    def PostOnNewModel(self):
        super().PostOnNewModel()
        
        self.SetDefaultEyeOffset(self.unitinfo.customeyeoffset if self.unitinfo.customeyeoffset else self.customeyeoffset)
            
    def UpdateTranslateActivityMap(self):
        """ Call when we need to change our activity translation map"""
        pass
            
    @staticmethod    
    def ParseActTable(cls, oldacttable):
        """ Replaces all activity names by the activity index."""
        acttable = {}
        for act, transact in oldacttable.items():
            try:
                if type(act) is str:
                    act = getattr(cls,act)
                if type(transact) is str:
                    transact = getattr(cls,transact)
            except AttributeError: 
                PrintWarning('Invalid Activity translation %s to %s\n' % (act, transact))
                continue
            acttable[act] = transact
        return acttable
    
    @staticmethod    
    def ParseAETable(cls, oldaetable):
        """ Scans the Animation Event dictionary and replaces
            strings with the event indices.
            Returns a new dictionary.
        """
        aetable = {}
        for ae, handler in oldaetable.items():
            if handler is None:
                continue
            try:
                if type(ae) is str:
                    ae = getattr(cls, ae)
            except AttributeError: 
                PrintWarning('Invalid Animation Event %s to Handler %s' % (ae, handler))
                continue
            try:
                if type(handler) is str:
                    handler = getattr(cls, handler)
            except AttributeError: 
                PrintWarning('Invalid Animation Event %s to Handler %s' % (ae, handler))
                continue
            aetable[ae] = handler
        return aetable
        
    # Server-Client events parsing
    @staticmethod
    def ParseEvents(cls, events):
        cls.eventhandlers = {}
        # NOTE: events indices are only valid within the entity class it is defined
        # NOTE 2: if you update this, check if units.animtate.EventHandlerMulti also needs to be updated.
        for i, e in enumerate(sorted(cls.events.keys())):
            # Lookup the handler in case it's a string
            handler = cls.events[e]
            if type(handler) == str:
                handler = getattr(cls, handler)
            cls.eventhandlers[i] = handler
            setattr(cls, e, i)
            
            # Some handlers want to do some setup here (animations)
            if hasattr(handler, 'Setup'):
                newhandler = handler.Setup(cls)
                if newhandler:
                    cls.eventhandlers[i] = newhandler
                    
    @classmethod
    def PostParseActivities(cls):
        """ Called after parsing the activities of a class. """
        pass
        
    @classmethod    
    def InitEntityClass(cls):
        """ Called upon the first time an entity class is defined or
            on level init for each entity class. """
        super().InitEntityClass()
        
        if isserver:
            # Parse the server activity list
            for act in cls.activitylist: 
                actidx = ActivityList_IndexForName(act)
                if actidx == ACT_INVALID:
                    ADD_ACTIVITY(cls, act)
                else:
                    setattr(cls, act, Activity(actidx))
                    
            # If acttables contains a single table, then we allow acttables to be that table
            # Here we convert it to the format we want.
            if not cls.acttables or not type(list(cls.acttables.values())[0]) is dict:
                cls.acttables = {'default': cls.acttables}
                    
            # Activities are parsed. Create the act translation map.
            # Convert strings to activities and then create the map
            cls.acttransmaps = {}
            for name in cls.acttables.keys():
                acttable = cls.ParseActTable(cls, cls.acttables[name])
                cls.acttransmaps[name] = TranslateActivityMap(acttable)
            
            # Parse animation events and create anim event table
            for ae in cls.aetable.keys():
                if type(ae) is str:
                    aeidx = EventList_RegisterPrivateEvent(ae)
                    setattr(cls, ae, aeidx)
            cls.animeventmap = AnimEventMap(cls.ParseAETable(cls, cls.aetable))
            
            # Events
            cls.ParseEvents(cls, cls.events)
            
            cls.PostParseActivities()
        else:
            # Reset
            setattr(cls, '%s_activitiesparsed' % cls.__name__, False)
            
    #: Custom eye offset position. In case the model one is stupid.
    customeyeoffset = None
    
    #: Activity list. Parsed in InitEntityClass on the server and OnNewModel on the client.
    #: Extend in derived classes with activitylist = list( baseclass.activitylist )
    activitylist = []
    
    #: Main Activity Translation tables.
    acttables = {
        'default': {},  # Default is selected when the unit has no weapon
        'default_weapon': {},  # default_weapon is selected when the unit has a weapon and there is no weapon entry.
    }
    
    if isserver:
        #: Anim Event map (server only).
        #: Provides handlers for animation events
        aetable = {}
        animeventmap = None
        
    #: Dictionary containing events and their handlers.
    #: The handlers must be a callable taking two arguments (unit and data).
    #: For example this can be an unbound method or an instance of a class
    #: with a method __call__ (which makes the instance callable).
    events = {
    }
    
    # Blinking
    enableunitblink = BooleanField(networked=True, value=False, clientchangecallback='OnUnitBlinkChanged')
        
if isserver:
    @concommand('unit_replenish_energy_all', 'Replenish energy of all units', FCVAR_CHEAT)
    def cc_unit_replenish_energy_all(args):
        UnitBase.ReplenishAllUnitsEnergy()
                
    @concommand('unit_scale_selection', 'Scales models of selection', FCVAR_CHEAT)
    def cc_unit_scale_selection(args):
        player = UTIL_GetCommandClient()
        if not player:
            return
            
        newscale = float(args[1])
            
        for unit in player.GetSelection():
            unit.SetModelScale(newscale)
            
if isclient:
    # ConVar for always showing healthbars
    # Note that HideBars will do nothing in case cl_alwaysshowhealthbars is on
    def AlwaysShowHealthBarsChanged(var, old_value, f_old_value):
        for o, l in unitlist.items():
            for unit in l:
                if unit.ShouldAlwaysShowBars():
                    unit.ShowBars()
                else:
                    unit.HideBars()
    cl_alwaysshowhealthbars = ConVar('cl_alwaysshowhealthbars', '0', 0, 'Always show the healthbars of all units', AlwaysShowHealthBarsChanged)
    
    @concommand('toggle_alwaysshowhealthbars', 'Toggle always showing unit healthbars', 0)
    def cc_toggle_alwaysshowhealthbars(args):
        cl_alwaysshowhealthbars.SetValue(not cl_alwaysshowhealthbars.GetBool())
        
    # For keybinding
    @concommand('+alwaysshowhealthbars', '', 0)
    def cc_plusalwaysshowhealthbars(args):
        if cl_alwaysshowhealthbars.GetInt() != 2:
            cl_alwaysshowhealthbars.SetValue(True)

    @concommand('-alwaysshowhealthbars', '', 0)
    def cc_minalwaysshowhealthbars(args):
        if cl_alwaysshowhealthbars.GetInt() != 2:
            cl_alwaysshowhealthbars.SetValue(False)
