from srcbase import *
from vmath import *
from vprof import vprofcurrentprofilee
from profiler import profile
from .info import unitlist
from fields import (IntegerField, FloatField, BooleanField, EHandleField, input, fieldtypes, OutputField, SetField,
                    ActivityField)
from playermgr import SimulatedPlayer
import traceback

import ndebugoverlay
from navmesh import GetHidingSpotsInRadius
from _recast import RecastMgr

from .base import UnitBase as BaseClass
from . import hull
from .locomotion import UnitCombatLocomotion
from .animstate import (UnitCombatAnimState, EventHandlerAnimation, EventHandlerAnimationMisc, EventHandlerGesture, 
                        EventHandlerJump, EventHandlerAnimationCustom, EventHandlerEndSpecAct)
from .orders import Order, OrderAttack, OrderAbility, AddToGroupMoveOrder, coverspotsearchradius
from core.signals import ScheduleFireSignalRobust
from core.attributes import CoverAttributeInfo, CoverDirectionalAttributeInfo
from core.decorators import clientonly
from core.units import UnitBaseShared

from entities import networked, Activity, FOWFLAG_UNITS_MASK, D_HT, MouseTraceData, entitylist, CHL2WarsPlayer
from animation import Studio_GetMass
from particles import *
from unit_helper import UnitAnimConfig, LegAnimType_t
from utils import UTIL_CalculateDirection, UTIL_ListPlayersForOwnerNumber, UTIL_GetPlayers, UTIL_FindPositionSimple
from gameinterface import CRecipientFilter, concommand, ConVar, FCVAR_CHEAT, engine
from gamerules import gamerules

if isserver:
    from utils import UTIL_Remove, UTIL_GetCommandClient
    from entities import CalculateExplosiveDamageForce, CTakeDamageInfo, CalculateMeleeDamageForce
    from .navigator import UnitCombatNavigator
    from .behavior_generic import BehaviorGeneric
    from .behavior_overrun import CreateBehaviorOverrun
    from .behavior_roaming import CreateBehaviorRoaming
    from .senses import UnitCombatSense
else:
    from materials import glowobjectmanager
    from core.signals import refreshhud

# Time methods
TIME_TO_TICKS = lambda dt: (0.5 + (dt) / gpGlobals.interval_per_tick)
TICKS_TO_TIME = lambda t: gpGlobals.interval_per_tick * (t)
ROUND_TO_TICKS = lambda t: gpGlobals.interval_per_tick * TIME_TO_TICKS(t)

unitcombatdebugoverlays = 0

@networked
class UnitBaseCombat(BaseClass):
    """ Base class for movable/attackable units with simple animations/attacks """
    def __init__(self):
        super().__init__()
        
        self.orders = [] 
        self.behaviors = []
        
        self.SetBlocksLOS(False)

        if isserver:
            self.debugoverlays = unitcombatdebugoverlays
            
            self.UseClientSideAnimation()
            
            self.viewdistance = 1024.0
            
            self.items = []
            self.chargehitunits = set()

    if isserver:
        def OnPlayerDefeated(self):
            self.Suicide()

    def UpdateOnRemove(self):
        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()
        
        if isserver:
            # If a player controls us, then leave.
            if self.controllerplayer:
                self.controllerplayer.SetControlledUnit(None)
                
            self.RemoveItems()
                
        # Clear all orders
        self.ClearAllOrders(notifyclient=False)
            
        # The components hold a reference to the entity. 
        # This means they must be deleted to allow the entity to free it's memory
        self.DestroyComponents()
        self.mv = None

        if isserver:
            self.fn_perform_movement = lambda: None
            self.fn_perform_navigation = lambda: None
        
    def CreateComponents(self):
        self.locomotion = self.LocomotionClass(self)
        self.animstate = self.AnimStateClass(self, self.animconfig)

        # Server only
        if isserver:
            self.navigator = self.NavigatorClass(self)
            self.senses = self.SensesClass(self)
            self.CreateBehaviors()
            
        # Components that receive events
        if isserver:
            self.eventcomponents = [self.locomotion, self.navigator, self.animstate]
        else:
            self.eventcomponents = [self.locomotion, self.animstate]
            
        self.componentsinitalized = True
        
    def DestroyComponents(self):
        if self.componentsinitalized:
            if isserver:
                self.DestroyBehaviors() # Destroy AI first, in case the OnEnd methods of actions still access other components
            self.locomotion = None
            self.animstate = None
            if isserver:
                self.navigator = None
                self.senses = None
            self.eventcomponents = []
        
    def CreateBehaviors(self):
        self.AddBehavior('behaviorgeneric', self.BehaviorGenericClass(self))
        
    def DestroyBehaviors(self):
        for behavior in self.behaviors:
            delattr(self, behavior.name)
            behavior.Destroy()
        self.behaviors = []
        
    def AddBehavior(self, name, behavior):
        self.behaviors.append(behavior)
        setattr(self, name, behavior)
        behavior.name = name
    
    def RunBehaviors(self):
        for behavior in self.behaviors:
            behavior.Run()
            
    def RemoveItems(self, dmginfo=None):
        if not self.items:
            return
            
        self.items = list(filter(bool, self.items))
        for item in list(self.items):
            try:
                item.OnUnitDetach(self, dmginfo)
            except:
                traceback.print_exc()
        
    @classmethod
    def PrecacheUnitType(cls, info):
        """ Precaches the unit type.
            This is only called one time per unit type in a level.
            It's called on both server and client one time.
        """
        super().PrecacheUnitType(info)
        
        PrecacheParticleSystem('pg_heal')
        PrecacheParticleSystem(cls.incoverparticlename)
        
    def GetActiveAttributes(self):
        attrs = dict(self.attributes)
        for at in self.attacks:
            if at.attributes:
                attrs.update(at.attributes)
        return attrs

    cover_type_attributes = {
        1: CoverAttributeInfo,
        2: CoverDirectionalAttributeInfo,  # Based on cover spot direction (static)
        3: CoverDirectionalAttributeInfo,  # Different way of applying compared to 2 (based on unit direction)
    }

    __active_cover_attribute = None

    def OnInCoverChanged(self):
        if self.__active_cover_attribute:
            self.RemoveAttribute(self.__active_cover_attribute)
            self.__active_cover_attribute = None

        if self.in_cover:
            self.__active_cover_attribute = self.cover_type_attributes.get(self.in_cover, CoverAttributeInfo)
            self.AddAttribute(self.__active_cover_attribute)
            self.AddRangeBonus('coverrange', 128)
            if isclient and not self.incoverparticle:
                maxs = self.CollisionProp().OBBMaxs()
                self.incoverparticle = self.ParticleProp().Create(self.incoverparticlename,
                                                                  PATTACH_CUSTOMORIGIN_FOLLOW, -1,
                                                                  Vector(0, 0, maxs.z/1.5))
                self.incoverparticle.SetControlPoint(1, self.GetTeamColor())
                radius = self.CollisionProp().BoundingRadius2D() * 1.4
                self.incoverparticle.SetControlPoint(2, Vector(radius, 0, 0))
        else:
            self.RemoveRangeBonus('coverrange')
            if isclient and self.incoverparticle:
                self.ParticleProp().StopEmission(self.incoverparticle, False, False, True)
                self.incoverparticle = None
            
        if isclient and self.selected:
            ScheduleFireSignalRobust(refreshhud)

    def OnGarrisonedChanged(self):
        if self.garrisoned:
            self.AddRangeBonus('bunkerrange', 128)
        else:
            self.RemoveRangeBonus('bunkerrange')

    def OnIsNavObstacleChanged(self):
        """ Detects on client and server if entity should be added as obstacle
        """
        if self.is_nav_obstacle:
            RecastMgr().AddEntRadiusObstacle(self, self.CollisionProp().BoundingRadius2D(),
                                             self.CollisionProp().OBBSize().z)
        else:
            RecastMgr().RemoveEntObstacles(self)

    def EnableAsNavObstacle(self):
        """ Makes this entity a navigation mesh obstacle.
            Should not move after enabling (i.e. won't update the navigation mesh).
        """
        if self.is_nav_obstacle:
            return
        self.is_nav_obstacle = True
        self.OnIsNavObstacleChanged()

    def DisableAsNavObstacle(self):
        """ Removes this entity from being a navigation mesh obstacle. """
        if not self.is_nav_obstacle:
            return
        self.is_nav_obstacle = False
        self.OnIsNavObstacleChanged()

    def OnConstructingChanged(self):
        """ Starts or stops the constructing animation of this unit/builder. """
        if self.constructing:
            self.DoAnimation(self.ANIM_CONSTRUCT)
        else:
            self.animstate.RestartMainSequence()

    def UpdateLocomotionSettings(self):
        if not self.mv:
            return
        unitinfo = self.unitinfo
        
        self.mv.maxspeed = self.CalculateUnitMaxSpeed()
        self.mv.yawspeed = self.yawspeed if unitinfo.turnspeed == 0 else unitinfo.turnspeed

    class SpeedModification(object):
        def __init__(self, speed_mod):
            self.speed_mod = speed_mod

    def AddSpeedModifier(self, speed_mod, apply_instantly=True):
        """ Applies a speed modification.

            Args:
                speed_mod (float): The speed to add.

            Kwargs:
                apply_instantly (bool): Updates unit maxspeed directly. If False, expects caller to update it.

            Returns:
                SpeedModification: object used as reference for the active speed modification.
        """
        speed_mod_object = self.SpeedModification(speed_mod)
        self.speed_modifiers.add(speed_mod_object)
        if apply_instantly:
            self.mv.maxspeed = self.CalculateUnitMaxSpeed()
        return speed_mod_object

    def RemoveSpeedModifier(self, speed_mod_object, apply_instantly=True):
        """ Remove the speed mod.

            Args:
                speed_mod_object (object): object created for the speed modification.

            Kwargs:
                apply_instantly (bool): Updates unit maxspeed directly. If False, expects caller to update it.
        """
        self.speed_modifiers.discard(speed_mod_object)
        if apply_instantly:
            self.mv.maxspeed = self.CalculateUnitMaxSpeed()

    @property
    def base_max_speed(self):
        """ Returns the base max speed of the unit, without any speed modifiers applied. """
        unitinfo = self.unitinfo
        return self.maxspeed if unitinfo.maxspeed == 0 else unitinfo.maxspeed

    def CalculateUnitMaxSpeed(self):
        # The base speed
        speed = self.base_max_speed

        # Apply speed modifiers
        for mod in self.speed_modifiers:
            speed += mod.speed_mod

        return speed

    if isserver:
        #def PostConstructor(self, clsname):
        #    super().PostConstructor(clsname)
            
            # Could opt to create components here, but it changes the initialization order...
            #self.CreateComponents()
            
        def Spawn(self):
            self.CreateComponents()
            
            self.UpdateSensingDistance()
            
            self.SetSolid(SOLID_BBOX)
            self.AddSolidFlags(FSOLID_NOT_STANDABLE)
            
            super().Spawn()
            
            # Must have an unit type
            if not self.GetUnitType():
                PrintWarning('UnitBaseCombat.Spawn: No unit type set. Setting to unknown.')
                self.SetUnitType('unit_unknown')
                
            # Create default movecommand
            self.mv = self.locomotion.CreateMoveCommand()

            # TODO: Need to move this somewhere else
            self.UpdateLocomotionSettings()
            self.mv.jumpheight = self.jumpheight
            
            self.mv.idealviewangles = self.GetAbsAngles()   
            
            self.UpdateMoveMethods()

            self.AddFlag(FL_AIMTARGET|FL_NPC) 
            self.SetCollisionGroup(self.CalculateOwnerCollisionGroup())
            self.SetMoveType(MOVETYPE_STEP)
            
            self.lifestate = LIFE_ALIVE
            self.takedamage = DAMAGE_YES
            self.InitBoneControllers()

            self.CreateVPhysics()
            
            # Set the main think loop
            if UnitBaseCombat.timelastspawn != gpGlobals.curtime:
                UnitBaseCombat.spawnedthisframe = 0
                UnitBaseCombat.timelastspawn = gpGlobals.curtime
                
            self.SetThink(self.UnitThink, 
                    gpGlobals.curtime + self.nextthinktimes[UnitBaseCombat.spawnedthisframe % len(self.nextthinktimes)])

            UnitBaseCombat.spawnedthisframe += 1 
            
        def OnUnitTypeChanged(self, oldunittype):
            super().OnUnitTypeChanged(oldunittype)
            
            self.cantakecover = self.unitinfo.cantakecover
            if self.handlesactive:
                self.UpdateLocomotionSettings()
                self.RebuildAttackInfo()
                self.UpdateSensingDistance()
                    
    else:
        def Spawn(self):
            self.CreateComponents()
            
            super().Spawn()
            
            # Create default movecommand
            self.mv = self.locomotion.CreateMoveCommand()
            
            # TODO: Need to move this somewhere else
            self.UpdateLocomotionSettings()
            self.mv.jumpheight = self.jumpheight
        
            self.Blink()    # Always blink on creation
            
        def OnUnitTypeChanged(self, oldunittype):
            super().OnUnitTypeChanged(oldunittype)
            
            self.cantakecover = self.unitinfo.cantakecover
            if self.handlesactive:
                self.UpdateLocomotionSettings()
                self.RebuildAttackInfo()
            
        def OnChangeOwnerNumber(self, oldownernumber):
            super().OnChangeOwnerNumber(oldownernumber)
            
            # Update glow color if active
            if self.glowidx != None:
                glowobjectmanager.SetColor(self.glowidx, self.GetTeamColor())
                
        def OnTeamColorChanged(self):
            super().OnTeamColorChanged()
            
            # Update glow color if active
            if self.glowidx != None:
                glowobjectmanager.SetColor(self.glowidx, self.GetTeamColor())
                
    def UpdateSensingDistance(self):
        if not self.senses:
            return
            
        # Get base sensing distance (either view distance or a custom sensing distance)
        if self.unitinfo.sensedistance != -1:
            sensedistance = self.unitinfo.sensedistance
        else:
            sensedistance = self.unitinfo.viewdistance
            
        # Apply range bonus
        for rangebonus in self.rangebonus.values():
            sensedistance += rangebonus
            
        self.senses.sensedistance = sensedistance
        
    def Restore(self, save):
        self.CreateComponents()
        
        # Create default movecommand
        self.mv = self.locomotion.CreateMoveCommand()
    
        return super().Restore(save)
        
    def OnRestore(self):
        super().OnRestore()

        # TODO: Need to move this somewhere else
        self.UpdateLocomotionSettings()
        self.mv.jumpheight = self.jumpheight
        
        self.UpdateMoveMethods()
        
        self.animstate.OnNewModel()

    def GetHullMins(self):
        return hull.Mins(self.unitinfo.hulltype)

    def GetHullMaxs(self):
        return hull.Maxs(self.unitinfo.hulltype)

    def GetHullWidth(self):
        return hull.Width(self.unitinfo.hulltype)

    def GetHullHeight(self):
        return hull.Height(self.unitinfo.hulltype)
    
    def CreateVPhysics(self):
        if self.IsAlive() and self.VPhysicsGetObject() == None:
            self.SetupVPhysicsHull()
        return True
            
    def SetupVPhysicsHull(self):
        """ Called to initialize or re-initialize the vphysics hull when the size of the Unit changes """
        if self.GetMoveType() == MOVETYPE_VPHYSICS or self.GetMoveType() == MOVETYPE_NONE:
            return

        if self.VPhysicsGetObject():
            # Disable collisions to get 
            self.VPhysicsGetObject().EnableCollisions(False)
            self.VPhysicsDestroyObject()
        self.VPhysicsInitShadow(True, False)
        self.physobj = self.VPhysicsGetObject()
        if self.physobj:
            self.physobj.SetMass(Studio_GetMass(self.GetModelPtr()))
            controller = self.physobj.GetShadowController()
            avgsize = self.CollisionProp().BoundingRadius2D()
            controller.SetTeleportDistance(avgsize * 0.5)
            
    # Allows disabling locomotion
    __locomotionenabled = True
    @property
    def locomotionenabled(self):
        return self.__locomotionenabled
    @locomotionenabled.setter
    def locomotionenabled(self, locomotionenabled):
        if self.__locomotionenabled == locomotionenabled:
            return # The move command is no longer updated, so clear it.
        if not locomotionenabled:
            self.mv.Clear()
        self.__locomotionenabled = locomotionenabled
        self.UpdateMoveMethods()
        
    # Allows only running facing code locomotion
    __locomotionfacingonly = False
    @property
    def locomotionfacingonly(self):
        return self.__locomotionfacingonly
    @locomotionfacingonly.setter
    def locomotionfacingonly(self, locomotionfacingonly):
        if self.__locomotionfacingonly == locomotionfacingonly:
            return # The move command is no longer updated, so clear it.
        if not locomotionfacingonly:
            self.mv.Clear()
        self.__locomotionfacingonly = locomotionfacingonly
        self.UpdateMoveMethods()
        
    #debugmoving = 0.0
    def PerformLocomotion(self):
        """if self.mv.forwardmove > 0.0:
            if not self.debugmoving:
                print('Unit moving! %f' % (gpGlobals.curtime))
                self.debugmoving = True
        else:
            self.debugmoving = False"""
            
        self.mv.interval = gpGlobals.curtime - self.GetLastThink()
        self.locomotion.PerformMovement(self.mv)
        self.simulationtime = gpGlobals.curtime
        
    def PerformLocomotionFacingOnly(self):
        self.mv.interval = gpGlobals.curtime - self.GetLastThink()
        self.locomotion.PerformMovementFacingOnly(self.mv)
        self.simulationtime = gpGlobals.curtime
        
    if isserver:
        def AutoMovement(self, interval=None):
            """ Uses the unit animation to move. """
            if not interval: interval = self.GetAnimTimeInterval()

            newpos = Vector()
            newangles = QAngle()
            success, finished = self.GetIntervalMovement(interval, newpos, newangles)
            #print('Success: %s, finished: %s, interval: %s, oldpos: %s, newpos: %s, newangles: %s' % (success, finished, interval, self.GetAbsOrigin(), newpos, newangles))
            if success and not finished:
                if self.GetMoveType() == MOVETYPE_STEP:
                    if not (self.GetFlags() & FL_FLY):
                        dist = newpos - self.GetLocalOrigin()

                        VectorScale(dist, 1.0 / interval, dist)

                        self.SetLocalVelocity(dist*1000.0)
                        return True
                    else:
                        self.SetLocalOrigin(newpos)
                        self.SetLocalAngles(newangles)
                        return True
                elif self.GetMoveType() == MOVETYPE_FLY:
                    dist = newpos - self.GetLocalOrigin()

                    VectorScale(dist, 1.0 / interval, dist)

                    self.SetLocalVelocity(dist)
                    return True
            return False
        
    def PerformNavigation(self):
        self.navigator.Update(self.mv)

    def PerformNavigationAnglesOnly(self):
        self.navigator.UpdateIdealAngles(self.mv)
            
    def PerformSensing(self):
        self.senses.PerformSensing()
        
    def UpdateMoveMethods(self):
        """ Updates the locomotion and navigation methods.

            Depending on our state, we could for example not move, only face a direction, etc.
        """
        if not self.IsAlive() or not self.locomotionenabled:
            self.fn_perform_movement = lambda: None
            self.fn_perform_navigation = lambda: None
            return

        if not self.locomotionfacingonly:
            self.fn_perform_movement = self.PerformLocomotion
        else:
            self.fn_perform_movement = self.PerformLocomotionFacingOnly
        if not self.aimoving:
            self.fn_perform_navigation = self.PerformNavigation
        else:
            self.fn_perform_navigation = self.PerformNavigationAnglesOnly
    
    @profile('ServerUnits')
    def UnitThink(self):
        """ Main think loop on server """
        vprofcurrentprofilee.EnterScope("ServerUnits", 0, "ServerUnits", False)
        
        self.UpdateServerAnimation()
        
        self.PerformSensing()
        self.UpdateActiveEnemy()
                
        if self.controllerplayer is None:
            if not self.unit_ai_disable.GetBool():
                self.RunBehaviors()
                
            # Update abilities if they want to be updated
            for abi in self.checkabilities:
                abi.OnUnitThink(self)
                
            # Update navigation and movement
            self.fn_perform_navigation()
            self.fn_perform_movement()

        self.StatusEffectsThink(self.think_freq)

        # Update energy if any
        if self.maxenergy > 0:
            self.UpdateEnergy(self.think_freq)

        if self.cloaked:
            if self.cloakenergydrain > 0 and self.energy == 0:
                self.UnCloak()
        
        self.SetNextThink(gpGlobals.curtime + self.think_freq)
        
        vprofcurrentprofilee.ExitScope()
        
    @property
    def activeability(self):
        if self.curorder:
            return self.curorder.ability
        return None
        
    def AllowAutoCast(self):
        if self.curorder and not self.curorder.AllowAutoCast(self):
            return False
        return True
            
    def CheckAutoCast(self, autocastlist):
        if not self.AllowAutoCast():
            return False
            
        for abi in autocastlist:
            if abi.CheckAutoCast(self):
                return True
        return False
            
    #
    # Moving
    #        
    __aimoving = False

    @property
    def aimoving(self):
        """ Disables updating movement by the navigator class. """
        return self.__aimoving

    @aimoving.setter
    def aimoving(self, aimoving):
        if aimoving:
            self.mv.Clear() # Clear, in case the ai will do nothing with it.
        self.__aimoving = aimoving
        self.UpdateMoveMethods()

    def StartMeleeAttack(self, enemy):
        """ Start a melee attack. Return true if the ai should wait for the animation to finish

            The target enemy is passed as argument. Usually the same as self.enemy. Depending on type
            of attack this may be used or not.
        """
        self.nextattacktime = gpGlobals.curtime + self.unitinfo.AttackMelee.attackspeed
        
        # If we have a weapon, it overrides the default
        if self.activeweapon is not None:
            return self.activeweapon.StartMeleeAttack(enemy)
            
        # By default, assume the attack animation fires
        # an event which does the actually attack
        self.DoAnimation(self.ANIM_MELEE_ATTACK1)
        return True
       
    def StartRangeAttack(self, enemy):
        """ Start a range attack. Return true if the ai should wait for the animation to finish

            The target enemy is passed as argument. Usually the same as self.enemy. Depending on type
            of attack this may be used or not.
        """
        self.nextattacktime = gpGlobals.curtime + self.unitinfo.AttackRange.attackspeed
    
        # If we have a weapon, it overrides the default
        if self.activeweapon is not None:
            return self.activeweapon.StartRangeAttack(enemy)

        # By default, assume the attack animation fires
        # an event which does the actually attack
        self.DoAnimation(self.ANIM_RANGE_ATTACK1)
        return True
     
    if isserver:
        def Weapon_Equip(self, weapon):
            super().Weapon_Equip(weapon)
            
            self.RebuildAttackInfo()
            self.UpdateTranslateActivityMap()
            self.UpdateAbilities()
            
        def Weapon_Switch(self, weapon, view_model_index=0):
            rv = super().Weapon_Switch(weapon, view_model_index)
            if not rv:
                return False
            
            self.RebuildAttackInfo()
            self.UpdateTranslateActivityMap()
            self.UpdateAbilities()

            if self.garrisoned:
                weapon.AddEffects(EF_NODRAW)

            return True
    else:
        def OnActiveWeaponChanged(self):
            self.RebuildAttackInfo()
            self.UpdateTranslateActivityMap()
            self.UpdateAbilities()
            
    def UpdateAttackInfo(self):
        super().UpdateAttackInfo()
        
        self.DispatchEvent('OnAttackInfoUpdated')
        
    def WeaponLOSCondition(self, ownerpos, targetpos, target):
        if not self.activeweapon:
            return False
        return self.activeweapon.WeaponLOSCondition(ownerpos, targetpos, target)

    def CanRangeAttack(self, target):
        if self.activeweapon:
            return self.activeweapon.nextprimaryattack < gpGlobals.curtime and self.HasRangeAttackLOSTarget(target)
        return self.HasRangeAttackLOSTarget(target)
        
    def CanMeleeAttack(self, target):
        return True
            
    #
    # User control
    #
    def UserCmd(self, cmd):
        self.mv.forwardmove = cmd.forwardmove
        self.mv.sidemove = cmd.sidemove
        self.mv.upmove = cmd.upmove
        self.mv.idealviewangles = cmd.viewangles
        self.mv.jump = ((cmd.buttons & IN_JUMP) != 0) #and ((cmd.oldbuttons & IN_JUMP) == 0)
        
        if not self.canjump and self.mv.jump:
            self.mv.upmove = 500.0
        
        #self.eyepitch = cmd.viewangles.x
        self.eyeyaw = cmd.viewangles.y
        
        self.mv.interval = gpGlobals.frametime
        self.locomotion.PerformMovement(self.mv)
        
        if self.nextattacktime < gpGlobals.curtime:
            if (cmd.buttons & IN_ATTACK):
                if len(self.attacks) > 0:
                    self.attacks[0].Attack(None, None)
            elif (cmd.buttons & IN_ATTACK2):
                if len(self.attacks) > 1:
                    self.attacks[1].Attack(None, None)

    def OnUserControl(self, player):
        super().OnUserControl(player)
        
        self.RebuildAttackInfo()

        if isserver:
            self.mv.Clear()
            self.SetMoveType(MOVETYPE_WALK)

    def OnUserLeftControl(self, player):
        super().OnUserLeftControl(player)
        
        self.RebuildAttackInfo()
    
        self.SetMoveType(MOVETYPE_STEP)
        self.mv.Clear()
        
    #
    # Hiding/Cover Spots
    #
    hidingspotid = None
    hidingspotpos = None
    cover_spot_override = None

    @property
    def cover_spot(self):
        """ Returns the information for the active cover spot.
        """
        return self.cover_spot_override or self.cover_spots_info.get(self.hidingspotid, self.default_cover_spot)

    def TakeCoverSpot(self, spotid, spotpos):
        """ Takes an hiding/cover spots.

            Args:
                spotid (int): ID of spot to take.
                spotpos (Vector): position of spot
        """
        if self.hidingspotid == spotid:
            return True  # Already claimed this one
        if spotid in self.used_cover_spots:
            return False
        if self.hidingspotid is not None:
            self.FreeCoverSpot()  # Free old, undesired though
            PrintWarning('%%d TakeCoverSpot: Old hiding spot was not cleared!\n' % (self.entindex()))
        self.hidingspotid = spotid
        self.hidingspotpos = spotpos
        self.used_cover_spots[spotid] = self.GetHandle()
        return True
            
        #print('#%d Unit taking hiding spot #%d' % (self.entindex(), spotid))
        
    def FreeCoverSpot(self, dispatch_event=True):
        if self.hidingspotid is None:
            return
        #print('#%d Unit freeing hiding spot #%d' % (self.entindex(), self.hidingspotid))
        del self.used_cover_spots[self.hidingspotid]
        self.hidingspotid = None

        if dispatch_event:
            self.DispatchEvent(self.OnCoverSpotCleared)
    #    
    # Selection and Orders
    #
    @profile('OrderUnit')
    def Order(self, player):
        """ Main method for player ordering an unit.
        
            All logic for the actual order processing goes in ProcessOrder, 
            which can be called without the player entity and just a mouse 
            data instance.
            
            Args:
                player (entity): The player entity
        """
        # The player ordering should be able to do so
        if not self.CanPlayerControlUnit(player):
            return
    
        data = player.GetMouseDataRightPressed()
        
        # Clear orders if player does not hold shift
        # NOTE: Do not dispatch an event. This might directly
        #       lead to a new order being inserted before the
        #       the order we are now processing.
        if (player.buttons & IN_SPEED) == False:
            clearedallorders = True
            self.ClearAllOrders(False, dispatchevent=False)
        else:
            clearedallorders = False
            
        # Process the actual order
        orderproccessed = self.ProcessOrder(data, player)
         
        # Only dispatch the event if we still have no new order
        if clearedallorders and not orderproccessed:
            self.DispatchEvent(self.OnAllOrdersCleared)
        
        if isclient:
            if data.ent and data.ent.IsUnit():
                data.ent.Blink(1.0)

    def ProcessOrder(self, data, player=None):
        """ Received a new order. Process it. 
            Note: Might not be the active order. 
        
            Args:
               data (MouseTraceData): Mouse data containing the target position + other information.
               
            Kwargs:
               player (entity): Player ordering the unit. Might be None
               
            Returns True if a new order was inserted.
        """
        # Create a simulated player instance with the mouse data as right click
        if not player:
            player = SimulatedPlayer(self.GetOwnerNumber(), selection=[self.GetHandle()], mousedata=data,
                rightmousepressed=data, rightmousereleased=data)

        # May be overriden by an ability (context aware ordering of abilities, such as salvage)
        for abi in self.abilities.values():
            if abi.OverrideOrder(self, data, player):
                return True
        
        ent = data.ent
        selection = player.GetSelection()
        angle = self.CalculateArrivalAngle(data, player.GetMouseDataRightReleased())
            
        if ent and ent.IsUnit():
            # When target is an unit, first check if it overrides the order in some way
            if not ent.TargetOverrideOrder(self, data, selection, angle, player):
                # If not, check if the unit is an enemy and attack it. In the other case
                # perform a move order on the unit (resulting in the unit following the other unit).
                if ent.IsAlive() and ent.CanBeSeen(self) and self.IRelationType(ent) == D_HT:
                    self.AttackOrder(ent, selection)
                else:
                    self.MoveOrder(data.groundendpos, angle, selection, target=ent)
        else:
            # Default to move order to position
            self.MoveOrder(data.groundendpos, angle, selection)
        return True
        
    def CalculateArrivalAngle(self, pressed, released):
        """ Calculates the arrival angles based on two mouse positions
        
            Args:
                pressed (MouseTraceData): Initial pressed mouse position
                released (MouseTraceData): Released mouse position
        """
        if (pressed.groundendpos-released.groundendpos).Length2D() < 16.0:
            return None
        return UTIL_CalculateDirection(pressed.groundendpos, released.groundendpos)
        
    def FindCoverSpot(self, position, searchradius=coverspotsearchradius, testclosestpos=None):
        """ Returns closest free cover spot at the position if available. 
        
            Args:
               position (Vector): Search position
               
            Kwargs:
               searchradius (float): Max search radius around position
               testclosestpos (Vector|None): Position used for determining the "best" cover spot.
        """
        coverspot = None
        
        #ndebugoverlay.Box(position, -Vector(8, 8, 8), Vector(8, 8, 8), 255, 0, 0, 255, 5.0)
        #if testclosestpos:
        #    ndebugoverlay.Box(testclosestpos, -Vector(8, 8, 8), Vector(8, 8, 8), 255, 255, 0, 255, 5.0)
        
        coverspots = GetHidingSpotsInRadius(position, searchradius, self, sortpos=testclosestpos)
        if coverspots:
            coverspots = [hs for hs in coverspots if hs[0] not in self.used_cover_spots]
            if coverspots:
                coverspot = coverspots[0]
                
        #for hs in coverspots:
        #    ndebugoverlay.Box(hs[1], -Vector(8, 8, 8), Vector(8, 8, 8), 255, 0, 0, 255, 5.0)
        
        #if coverspot:
        #    ndebugoverlay.Box(coverspot[1], -Vector(12, 12, 8), Vector(12, 12, 8), 0, 255, 0, 255, 5.0)
        
        return coverspot
        
    def MoveOrderInternal(self, position, angle=None, selection=[], target=None, originalposition=None, 
                                findhidespot=True, coverspotsearchradius=coverspotsearchradius, repeat=False):
        """ Performs a move order on the unit. 
        
            This is split from MoveOrder, so it can be called from other places too. This is mainly used to execute
            a group move order.
            
            Args:
                position (Vector): target order position
                
            Kwargs:
                angle (Qangle): Order arrival angles
                selection (list): selection of units also receiving this order
                target (entity): target entity of this order
                originalposition (Vector): the unmodified order position
                findhidespot (bool): whether or not to test for finding a cover spot
                coverspotsearchradius (float): the search radius when finding a cover spot
                repeat (bool): whether or not to repeat this order (for patrol like commands)
        """
        coverspot = None
        if findhidespot and self.cantakecover:
            coverspot = self.FindCoverSpot(position, searchradius=coverspotsearchradius)
            if coverspot:
                if self.hidingspotid == coverspot[0]:
                    # Don't need to insert an order if the spot we have is the same as the target spot!
                    return None
            
                coverspotpos = coverspot[1]
                
                if self.hidingspotid:
                    curdist = (self.hidingspotpos - position).LengthSqr()
                    otherdist = (coverspotpos - position).LengthSqr()
                    if curdist < otherdist:
                        return None # Bug out, current hiding spot is closer!
                        
                # Modify target position to the cover spot
                position = coverspotpos

        o = Order(type=Order.ORDER_MOVE,
                  position=Vector(position),
                  originalposition=originalposition,
                  angle=angle,
                  selection=selection,
                  target=target,
                  repeat=repeat)
        o.hidespot = coverspot
            
        self.InsertOrder(o)
            
        if (isclient and len(self.orders) == 1 and
                (not selection or selection[0] == self)):
            self.MoveSound()
            
        return o
        
    def MoveOrder(self, position, angle=None, selection=[], target=None, repeat=False):
        """ Issues a move order to a position.
        
            Args:
                position (Vector): Move position
                
            Kwargs:
                angle (QAngle): Optional arrival angles.
                selection (list): Selection of which the unit is part.
                target (entity): Optional target entity for following.
                repeat (bool): Whether or not to repeat the order after it's done.
                               This re-inserts the order at the back of the queue.
                               This is used for the patrol ability.
        """
        # In case we are processing a selection move order, then we first collect all units
        # Afterwards the move order is processed in one go
        # Only the unit is added, the caller will already setup the right arguments for the group move order
        if AddToGroupMoveOrder(self):
            return None
        return self.MoveOrderInternal(position, angle, selection, target=target, repeat=repeat)
        
    def AttackOrder(self, enemy, selection=[], ability=None, repeat=False):
        """ Issues an attack order on an enemy.
        
            Args:
                enemy (entity): Target unit (or any entity) to attack
                
            Kwargs:
                selection (list): Selection of which the unit is part.
                ability (object): Ability associated with the attack order.
                repeat (bool): Whether or not to repeat the order after it's done.
                               This re-inserts the order at the back of the queue.
                               This is used for the patrol ability.
            
        """
        o = OrderAttack(type=Order.ORDER_ENEMY,
                  target=enemy,
                  selection=selection,
                  repeat=repeat)
        o.ability = ability
        self.InsertOrder(o)
        if (isclient and len(self.orders) == 1 and
                (not selection or selection[0] == self)):
            self.AttackSound()
        return o
        
    def AttackMove(self, position, target=None, player=None, selection=None):
        """ Shortcut for doing attack move ability on an enemy. 
        
            Args:
                position (Vector): attack position
                
            Kwargs:
                target (entity): optional target entity for attacking
                player (entity): player entity. In case None, a simulated player is created
                                 with the unit as selection (unless selection is specified).
                selection (list): Optional unit selection. Does nothing if player is specified.
        """
        if isclient:
            return False
        if not 'attackmove' in self.abilitiesbyname:
            return False
        if not selection:
            selection = [self.GetHandle()]
        if not player:
            player = SimulatedPlayer(self.GetOwnerNumber(), selection=selection)
        leftpressed = MouseTraceData()
        leftpressed.endpos = position
        leftpressed.groundendpos = position
        leftpressed.ent = target
        mouse_inputs=[('leftpressed', leftpressed)]
        self.DoAbility('attackmove', mouse_inputs)
        return True
            
    def AbilityOrder(self, target=None, position=None, angle=None, ability=None, 
                    alwaysqueue=False, idx=None, notifyclient=False, dispatchevent=True, repeat=False):
        """ Creates a new ability order.
        
            Kwargs:
                target (entity): 
                position (Vector):
                angle (QAngle): 
                ability (object):
                alwaysqueue (bool):
                idx (object): 
                notifyclient (bool):
                dispatchevent (bool):
                repeat (bool):
        """
        # Clear orders if player does not hold shift or when explicit said to queue the order 
        if not alwaysqueue and ability and ability.player and not (ability.player.buttons & IN_SPEED):
            self.ClearAllOrders(True, dispatchevent=False) # Don't dispatch an event, since insert order will already do so (if desired)
            
        o = OrderAbility(type=Order.ORDER_ABILITY, position=position, angle=angle, 
                       target=target, repeat=repeat)
        o.ability = ability
        self.InsertOrder(o, idx=idx, notifyclient=notifyclient, dispatchevent=dispatchevent)
        
        if o.ability:
            o.ability.attachedtoorder = True
            
        return o
            
    @classmethod
    def SpreadUnits(cls, units, clearorders=True):
        """ Spreads the units. 
        
            Args:
                units (list): List of units to be spreaded, using their group origin as reference.
                clearorders (bool): Clears orders of units being spreaded.
        """
        if not units:
            return
            
        origin = Vector(vec3_origin)
        for unit in units:
            origin += unit.GetAbsOrigin()
        origin /= len(units)
        
        for unit in units:
            if clearorders:
                unit.ClearAllOrders(False, dispatchevent=False)
        
            pos = unit.GetAbsOrigin()
            if origin == pos:
                dir = RandomVector(0, 1)
            else:
                dir = pos - origin
            dir.z = 0
            VectorNormalize(dir)
            
            targetpos = UTIL_FindPositionSimple(pos + dir * 200.0, 1024.0)
            if targetpos != vec3_origin:
                unit.MoveOrder(targetpos)
            else:
                PrintWarning('Could not find a spread spot for unit #%d\n' % (unit.entindex()))
            #unit.DispatchEvent('OnRequestMoveAway', origin, 200.0)
            
    def StartNewOrder(self, dispatchevent=True):
        """ Starts a new order. This is always the order in the front of the queue. """
        if not self.orders:
            return
            
        # New order, send an event
        self.curorder = self.orders[0]
        if dispatchevent:
            self.DispatchEvent(self.OnNewOrder, self.curorder)
        if isserver:
            self.onneworder.FireOutput(self, self)

    def InsertOrder(self, order, idx=None, notifyclient=False, dispatchevent=True):
        """ Inserts a new order.
        
            Args:
                order (Order): the order to be inserted
                
            Kwargs:
                idx (object): index at which to insert the order, or None to insert at end.
                notifyclient (bool):
                dispatchevent (bool): Whether or not to dispatch a queue order event
        """
        # Don't accept new orders when being removed, could happen due clearing orders resulting in new orders.
        if self.IsMarkedForDeletion():
            return

        order.unit = self
        
        # Special case: This functionality is intended for patrol
        # If appending to the end, and the last orders are "repeat" and this order is not "repeat", then
        # add the order before the repeat order. 
        if self.orders and not order.repeat and idx is None:
            if self.orders[-1].repeat:
                idx = 0
                for idx in range(-1, -len(self.orders)-1, -1):
                    if not self.orders[idx].repeat:
                        break
                if idx == -len(self.orders):
                    idx = 0
        
        # Insert order
        if idx is not None:
            self.orders.insert(idx, order)
        else:
            self.orders.append(order)
            idx = len(self.orders)-1
            
        if idx == 0 or len(self.orders) == 1:
            # Start the new order if in front of the queue
            self.StartNewOrder(dispatchevent=dispatchevent)
        else:
            # Order is queued, send an event
            if dispatchevent:
                self.DispatchEvent(self.OnOrderQueued, order)
                
        if len(self.orders) == 2:
            self.UpdateRallyLines()
        else:
            # Get previous and next order
            prev_order = self.orders[idx-1] if idx-1 >= 0 else None
            next_order = self.orders[idx+1] if idx+1 < len(self.orders) else None
            
            # Notify the new order changed
            # If we have a next order, we were inserted in between some orders
            # Also let this next order known the previous order changed
            order.OnPrevOrderChanged(prev_order)
            if next_order:
                next_order.OnPrevOrderChanged(order)
            
    def ClearOrder(self, idx=0, notifyclient=True, dispatchevent=True, allowrepeat=False):
        """ Clears an order from the unit.
        
            Kwargs:
                idx (int): Index at which to clear an order. Defaults to the first order.
                notifyclient (bool): Sends clear order event to client.
                dispatchevent (bool): Dispatchs event to AI about the order change.
                allowrepeat (bool): If orders may be repeated after clearing.
        """
        if not self.orders:
            return False
        
        # Remember the next order, requires an update at the end if it still exists
        nextorder = self.orders[idx+1] if idx+1 < len(self.orders) else None

        order = self.orders.pop(idx)
        self.curorder = None
        
        if isserver:
            self.onorderperformed.FireOutput(self, self)

        # Tell order it is removed
        order.OnRemove()
        order.unit = None
            
        if isserver and notifyclient:
            players = UTIL_ListPlayersForOwnerNumber(self.GetOwnerNumber())
            filter = CRecipientFilter()
            filter.MakeReliable()
            [filter.AddRecipient(player) for player in players]
            self.SendEvent(filter, self.ORDER_CLEAR if not allowrepeat else self.ORDER_CLEAR_AREPEAT, idx)
            
        if allowrepeat and order.repeat and self.orders:
            order.unit = self
            self.orders.append(order)
            if len(self.orders) > 1:
                order.OnPrevOrderChanged(self.orders[-2])
        
        if not self.orders:
            # If no orders are left, dispatch events all orders are cleared
            self.curorder = None
            if dispatchevent:
                self.DispatchEvent(self.OnAllOrdersCleared)
            if isserver:
                self.onallorderscanceled.FireOutput(self, self)
        elif idx == 0:
            # If idx==0 it means we have a new order
            # The original order at idx 0 (if any) gets pushed back
            self.StartNewOrder(dispatchevent=dispatchevent)
            
        # Tell next order the previous order changed
        if nextorder and nextorder in self.orders:
            idx = self.orders.index(nextorder)
            prevorder = self.orders[idx-1] if idx-1 >= 0 else None
            nextorder.OnPrevOrderChanged(prevorder)

        return True
           
    def ClearAllOrders(self, notifyclient=True, dispatchevent=True, maxclear=-1):
        """ Clears all or multiple orders, starting from idx 0.
        
            Kwargs:
                notifyclient (bool): Sync to client
                dispatchevent (bool): dispatches an event.
                maxclear (int): clears up to n orders. NOTE: This is really intended for the client when using ORDER_CLEARALL.
                                This is to prevent unintentional clearing the wrong orders (although it still doesn't guarantee
                                it goes right).
        """
        if not self.orders or maxclear == 0:
            return False
            
        countcleared = 0
        while self.ClearOrder(notifyclient=False, dispatchevent=False):
            countcleared += 1
            if maxclear != -1 and countcleared >= maxclear:
                break
        assert maxclear != -1 or (not self.orders and not self.curorder), 'cleared all orders, but still got orders'
        
        if isserver and notifyclient:
            players = UTIL_ListPlayersForOwnerNumber(self.GetOwnerNumber())
            msg_filter = CRecipientFilter()
            msg_filter.MakeReliable()
            [msg_filter.AddRecipient(player) for player in players]
            self.SendEvent(msg_filter, self.ORDER_CLEARALL, countcleared)
            
        if dispatchevent:
            self.DispatchEvent(self.OnAllOrdersCleared)
        return True
        
    def EventHandlerClearOrder(self, data):
        self.ClearOrder(idx=data)
        
    def EventHandlerClearOrderAllowRepeat(self, data):
        self.ClearOrder(idx=data, allowrepeat=True)
        
    def EventHandlerClearAllOrders(self, data):
        self.ClearAllOrders(maxclear=data)
        
    def EventHandlerOrderInsert(self, data):
        pass # TODO?
        
    def EventHandlerDeSelect(self, data):
        players = UTIL_GetPlayers()
        for p in players:
            p.RemoveUnit(self)
            
    def EventHandlerStub(self, data):
        pass
        
    def EventHandlerDoHeal(self, data):
        if isclient:
            healfx = self.ParticleProp().Create("pg_heal", PATTACH_ABSORIGIN_FOLLOW)
            healfx.SetControlPoint(1, self.GetTeamColor())
            healfx.SetControlPoint(2, Vector(self.CollisionProp().BoundingRadius2D(), 1.0, 0.0))
            
    if isclient:
        def MoveSound(self):
            self.PlayOrderSound(self.unitinfo.sound_move)
                
        def AttackSound(self):
            self.PlayOrderSound(self.unitinfo.sound_attack)
            
    def DeathSound(self):
        if self.unitinfo.sound_death:
            self.EmitSound(self.unitinfo.sound_death)
            
    def JumpSound(self):
        if self.nextjumpsound < gpGlobals.curtime and self.unitinfo.sound_jump:
            self.EmitSound(self.unitinfo.sound_jump)
            self.nextjumpsound = gpGlobals.curtime + 5.0
            
    def Event_Killed(self, info):
        """ Killed :)"""
        self.lifestate = LIFE_DYING
        
        canbecomeragdoll = self.CanBecomeRagdoll()
        shouldgib = self.ShouldGib(info)
        
        self.StopLoopingSounds()
        if (self.GetFlags() & FL_DISSOLVING) == 0:
            self.DeathSound()
        
        self.RemoveItems(info)
        
        # If a player controls us, then leave.
        if self.controllerplayer:
            self.controllerplayer.SetControlledUnit(None)
            
        # Remove all our weapons (prevents active weapon from being dropped)
        self.RemoveAllWeapons()

        super().Event_Killed(info)

        if not canbecomeragdoll and not shouldgib:
            self.DispatchEvent('OnKilled')
        
    def Event_Gibbed(self, info):
        gibbed = self.CorpseGib(info)

        if gibbed:
            # don't remove players!
            UTIL_Remove(self)
            self.SetThink(None) # We're going away, so don't think anymore.
        else:
            self.CorpseFade()

        return gibbed
        
    def Dissolve(self, *args, **kwargs):
        super().Dissolve(*args, **kwargs)
        
        # Just destroy the AI, so it won't try to do anything
        self.SetCanBeSeen(False)
        self.DestroyBehaviors()
        
    def StopLoopingSounds(self):
        pass

    # 
    # Events
    #     
    def DispatchEvent(self, eventname, *args):
        if not self.eventcomponents:
            return
            
        for c in self.eventcomponents:
            handler = getattr(c, eventname, None)
            if handler and handler(*args):
                return
                  
        if isserver:
            for behavior in self.behaviors:
                if behavior.DispatchEvent(eventname, *args):
                    return
        if isclient:
            DevMsg(2, '#%d CLIENT %s (%f) No component responded to event %s\n' % (self.entindex(), self.__class__.__name__, gpGlobals.curtime, eventname))
        else:
            DevMsg(2, '#%d SERVER %s (%f) No component responded to event %s\n' % (self.entindex(), self.__class__.__name__, gpGlobals.curtime, eventname))
            
    def Touch(self, other):
        """ This breaks the behavior of SetTouch, but it is preferable to use the event system """ 
        self.DispatchEvent(self.OnTouch, other)
            
    @classmethod
    def PostParseActivities(cls):
        """ Called after parsing the activities of a class. """
        super().PostParseActivities()
        
        if type(cls.attackmelee1act) == str:
            cls.attackmelee1act = getattr(cls, cls.attackmelee1act, 'Could not find activity for %s' % (cls.attackmelee1act))
        if type(cls.attackrange1act) == str:
            cls.attackrange1act = getattr(cls, cls.attackrange1act, 'Could not find activity for %s' % (cls.attackrange1act))
        if type(cls.constructactivity) == str:
            cls.constructactivity = getattr(cls, cls.constructactivity, 'Could not find activity for %s' % (cls.constructactivity))
        
    @classmethod    
    def InitEntityClass(cls):
        super().InitEntityClass()
        
        if isserver:
            cls.BehaviorOverrunClass = CreateBehaviorOverrun(cls.BehaviorGenericClass)
            cls.BehaviorRoamingClass = CreateBehaviorRoaming(cls.BehaviorGenericClass)
        
    # 
    # Enemy selection
    #
    def UpdateActiveEnemy(self):
        """ Updates self.enemy target. Dispatches events when the enemy changes. """
        if self.disable_update_active_enemy:
            return

        if self.forcedenemy and self.enemy:
            self.CheckEnemyLost()
        else:
            self.UpdateEnemy(self.senses)

    def IsValidEnemy(self, target, require_alive=True):
        return (target and
                (not require_alive or target.IsAlive()) and
                (not target.IsUnit() or target.CanBeSeen(self)) and
                self.IRelationType(target) == D_HT)
        
    def OnTakeDamage_Alive(self, info):
        attacker = info.GetAttacker()
        if self.enemy:
            if self.enemy == attacker:
                self.lastenemyattack = gpGlobals.curtime
            elif gpGlobals.curtime - self.lastenemyattack > 10.0:
                if not self.curorder or (self.curorder.type != Order.ORDER_ENEMY):
                    self.UpdateActiveEnemy()
                    self.lastenemyattack = gpGlobals.curtime
            
        return super().OnTakeDamage_Alive(info)
        
    # A few generic damage dealing methods
    def ImpactShock(self, origin, radius, magnitude, ignored=None):
        # Also do a local physics explosion to push objects away
        vecSpot = Vector()
        falloff = 1.0 / 2.5

        entity = None

        # Find anything within our radius
        while True:
            entity = entitylist.FindEntityInSphere(entity, origin, radius)
            if entity == None:
                break
                
            # Don't affect the ignored target
            if entity == ignored:
                continue
            if entity == self:
                continue

            # UNDONE: Ask the object if it should get force if it's not MOVETYPE_VPHYSICS?
            origin = self.GetAbsOrigin()
            if entity.GetMoveType() == MOVETYPE_VPHYSICS or (entity.VPhysicsGetObject() and entity.IsPlayer() == False):
                vecSpot = entity.BodyTarget(origin)
                
                # decrease damage for an ent that's farther from the bomb.
                flDist = (origin - vecSpot).Length()

                if radius == 0 or flDist <= radius:
                    adjustedDamage = flDist * falloff
                    adjustedDamage = magnitude - adjustedDamage

                    if adjustedDamage < 1:
                        adjustedDamage = 1

                    info = CTakeDamageInfo( self, self, adjustedDamage, DMG_BLAST )
                    CalculateExplosiveDamageForce(info, (vecSpot - origin), origin)

                    entity.VPhysicsTakeDamage(info)

    # Charge stubs
    def ChargeLookAhead(self):
        pass
        
    def HandleChargeImpact(self, vecImpact, pEntity):
        return 1
        
    # Cloaking support
    def Cloak(self):
        if self.cloaked:
            return
        super().Cloak()
        self.RebuildAttackInfo()
        
    def UnCloak(self):
        if not self.cloaked:
            return
        super().UnCloak()
        self.RebuildAttackInfo()
        
    def OnCloakChanged(self):
        super().OnCloakChanged()
        
        if self.activeweapon:
            self.activeweapon.ForceUseFastPath(not self.cloaked)
            self.activeweapon.ForcedMaterialOverride(self.cloakmaterial if self.cloaked else None)
        
    if isserver:
        # Debug (Use bits in range 0x00001000 - 0x00800000)
        OVERLAY_UNITROUTE = 0x00001000
        OVERLAY_UNITACTIONS = 0x00002000
        OVERLAY_UNITINFO = 0x00004000
        OVERLAY_UNITACTIONSDEBUG = 0x00008000

        # 0x00010000 is used by UnitBaseShared
        def DrawDebugGeometryOverlays(self):
            super().DrawDebugGeometryOverlays()

            if self.debugoverlays & self.OVERLAY_UNITROUTE:
                self.navigator.DrawDebugRouteOverlay()
            if self.debugoverlays & self.OVERLAY_UNITACTIONS:
                self.EntityText(0, '#%d' % (self.entindex()), 0.1)
                i = 1
                for behavior in self.behaviors:
                    behavior.DrawActions(i, bool(self.debugoverlays & self.OVERLAY_UNITACTIONSDEBUG))
                    i += 1
            if self.debugoverlays & self.OVERLAY_UNITINFO:
                self.navigator.DrawDebugInfo()

        unit_ai_disable = ConVar('unit_ai_disable', '0', FCVAR_CHEAT)

        def OnNewModel(self):
            super().OnNewModel()
            #self.SetDefaultEyeOffset()
            self.animstate.OnNewModel()
            
    else:
        def EnableGlow(self, enable=True):
            if self.glowidx != None:
                glowobjectmanager.UnregisterGlowObject(self.glowidx)
                self.glowidx = None
                
            if enable:
                self.glowidx = glowobjectmanager.RegisterGlowObject(self, self.GetTeamColor(), 0.7, True, True, -1)

        def OnSelected(self, player):
            super().OnSelected(player)

            # Create rally lines
            self.UpdateRallyLines()

        def OnDeSelected(self, player):
            super().OnDeSelected(player)
            
            # Destroy rally lines
            self.UpdateRallyLines()

        def OnNewModel(self):
            super().OnNewModel()

            #self.SetDefaultEyeOffset()
            self.animstate.OnNewModel()
            
    @clientonly
    def UpdateRallyLines(self):
        prevo = None
        for o in self.orders:
            o.OnPrevOrderChanged(prevo)
            prevo = o

    def UpdateTranslateActivityMap(self):
        """ Call when we need to change our activity translation map 
            (When the weapon of the unit changes) """
        if self.activeweapon:
            name = self.activeweapon.GetClassname()
            if name in self.acttransmaps:
                self.animstate.SetActivityMap(self.acttransmaps[name])
                return 

            # No entry for this weapon. Try default weapon.
            if 'weapon_default' in self.acttransmaps:
                self.animstate.SetActivityMap(self.acttransmaps['weapon_default'])
                return
                
        # Default
        assert('default' in self.acttransmaps)
        self.animstate.SetActivityMap(self.acttransmaps['default'])
        
    @property
    def canjump(self):
        return bool(self.jumpheight)
        
    # Unit Inputs
    def SimulateOrder(self, targetpos, target=None, queueorder=False):
        right = MouseTraceData()
        right.endpos = targetpos
        right.groundendpos = targetpos
        right.ent = target
        
        player = SimulatedPlayer(self.GetOwnerNumber(), rightmousepressed=right, rightmousereleased=right, buttons=IN_SPEED if queueorder else 0)
        self.Order(player)
        
    @input(inputname='OrderUnit', helpstring='Order unit to target entity', fieldtype=fieldtypes.FIELD_STRING) # Deprecated input name
    def InputOrderUnit(self, inputdata):
        self.InputOrder(inputdata)
        
    def InputDoOrder(self, inputdata, queueorder=False):
        """ Shared code for Order and QueueOrder input methods. """
        targetname, _, abilityname = inputdata.value.String().partition(':')
        
        target = entitylist.FindEntityByName(None, targetname)
        if not target:
            PrintWarning('#%d.%s: Could not find target entity %s\n' % (self.entindex(), 'QueueOrder' if queueorder else 'Order', targetname))
            return
            
        targetpos = target.GetAbsOrigin()
        
        if abilityname:
            # Performs a target type ability. Other types of abilities will fail.
            if not abilityname in self.abilitiesbyname:
                PrintWarning('#%d.%s: Unit is unable to do ability %s\n' % (self.entindex(), 'QueueOrder' if queueorder else 'Order', abilityname))
                return
            leftpressed = MouseTraceData()
            leftpressed.endpos = targetpos
            leftpressed.groundendpos = targetpos
            leftpressed.ent = target if target.IsUnit() else None
            mouse_inputs=[('leftpressed', leftpressed)]
            self.DoAbility(abilityname, mouse_inputs, queueorder=queueorder)
        else:
            self.SimulateOrder(targetpos, target, queueorder=queueorder)
        
    @input(inputname='Order', helpstring='Order unit to target entity', fieldtype=fieldtypes.FIELD_STRING)
    def InputOrder(self, inputdata):
        self.InputDoOrder(inputdata, queueorder=False)
        
    @input(inputname='QueueOrder', helpstring='Queue an order to an unit to a target entity with optional ability specified (e.g. "targetname:grenade")', fieldtype=fieldtypes.FIELD_STRING)
    def InputQueueOrder(self, inputdata):
        self.InputDoOrder(inputdata, queueorder=True)
        
    @input(inputname='CancelOrder', helpstring='Cancel order at specified index parameter (0 is first active order)', fieldtype=fieldtypes.FIELD_INTEGER)
    def InputCancelOrder(self, inputdata):
        idx = inputdata.value.Int()
        self.ClearOrder(idx)
        
    @input(inputname='CancelAllOrders', helpstring='Cancels all orders of the unit')
    def InputCancelAllOrders(self, inputdata):
        self.ClearAllOrders(notifyclient=True)
        
    @input(inputname='EnableSensing', helpstring='Enables unit sensing (i.e. detecting enemies)')
    def InputEnableSensing(self, inputdata):
        self.senses.Enable()
        
    @input(inputname='DisableSensing', helpstring='Disables unit sensing (i.e. detecting enemies)')
    def InputDisableSensing(self, inputdata):
        self.senses.Disable()
        
    @input(inputname='PlayAnimation', helpstring='Plays an animation by activity name', fieldtype=fieldtypes.FIELD_STRING)
    def InputPlayAnimation(self, inputdata):
        actname = inputdata.value.String()
        act = self.LookupActivity(actname)
        if act == Activity.ACT_INVALID:
            PrintWarning('InputPlayAnimation: Invalid activity %s\n' % (actname))
            return
        self.DoAnimation(self.ANIM_CUSTOM, act)
        
    @input(inputname='PlayGesture', helpstring='Plays a gesture by activity name', fieldtype=fieldtypes.FIELD_STRING)
    def InputPlayGesture(self, inputdata):
        actname = inputdata.value.String()
        act = self.LookupActivity(actname)
        if act == Activity.ACT_INVALID:
            PrintWarning('InputPlayAnimation: Invalid activity %s\n' % (actname))
            return
        self.DoAnimation(self.ANIM_GESTURE, act)
        
    @input(inputname='Teleport', helpstring='Teleports the unit to the target entity', fieldtype=fieldtypes.FIELD_STRING)
    def InputTeleport(self, inputdata):
        target = entitylist.FindEntityByName(None, inputdata.value.String())
        if not target:
            PrintWarning('#%d.InputTeleport: Could not find target entity %s\n' % (self.entindex(), inputdata.value.String()))
            return
            
        unitinfo = self.unitinfo
        targetpos = UTIL_FindPositionSimple(target.GetAbsOrigin(), 1024.0, unitinfo.mins, unitinfo.maxs)
        if targetpos != vec3_origin:
            self.SetAbsOrigin(targetpos)
            self.lastidleposition = targetpos
        else:
            PrintWarning('#%d.InputTeleport: Could not find a valid position around target %s\n' % (self.entindex(), inputdata.value.String()))
            
    # Show different hud
    if isclient:
        # A reference to the class of a panel
        # Shown when this is the only selected unit
        # Defaults to the panel that shows the selected units
        def UpdateUnitPanelClass(self):
            from core.hud.units import BaseHudSingleUnitCombat
            self.unitpanelclass = BaseHudSingleUnitCombat

    # Main Components classes
    #: Locomotion class component
    LocomotionClass = UnitCombatLocomotion
    #: Animation State class component
    AnimStateClass = UnitCombatAnimState
    if isserver:
        #: Navigator class component
        NavigatorClass = UnitCombatNavigator
        #: Senses class component
        SensesClass = UnitCombatSense
        
        #: Behavior Generic class component
        BehaviorGenericClass = BehaviorGeneric
        #: Behavior Overrun class component (only for overrun)
        BehaviorOverrunClass = BehaviorGeneric
        
    # Default vars for locomotion and senses components
    # NOTE: animstate and navigator are implemented as properties in CUnitBase. Don't override them here!
    locomotion = None
    senses = None
        
    #: Dictionary containing events and their handlers.
    #: The handlers must be a callable taking two arguments (unit and data).
    #: For example this can be an unbound method or an instance of a class
    #: with a method __call__ (which makes the instance callable).
    events = {
        'ORDER_CLEAR': EventHandlerClearOrder,
        'ORDER_CLEAR_AREPEAT': EventHandlerClearOrderAllowRepeat,
        'ORDER_CLEARALL': EventHandlerClearAllOrders,
        'ORDER_INSERT': EventHandlerOrderInsert,
        'UNIT_DESELECT': EventHandlerDeSelect,
        'ANIM_MELEE_ATTACK1': EventHandlerAnimation('attackmelee1act'),
        'ANIM_MELEE_ATTACK2': EventHandlerAnimation('attackmelee1act'),
        'ANIM_RANGE_ATTACK1': EventHandlerAnimation('attackrange1act'),
        'ANIM_RANGE_ATTACK2': EventHandlerAnimation('attackrange1act'),
        'ANIM_RELOAD': EventHandlerAnimationMisc('reloadact', onlywhenstill=True),
        'ANIM_RELOAD_LOW': EventHandlerAnimationMisc('reloadact_low', onlywhenstill=True),
        'ANIM_JUMP': EventHandlerJump(),
        'ANIM_CUSTOM': EventHandlerAnimationCustom(),
        'ANIM_GESTURE': EventHandlerGesture(),
        'ANIM_REPAIR': EventHandlerAnimation('constructactivity'),
        'ANIM_CONSTRUCT': EventHandlerAnimation('constructactivity'),
        'ANIM_CLIMBDISMOUNT': EventHandlerAnimation(Activity.ACT_CLIMB_DISMOUNT),
        'ANIM_DIE': EventHandlerAnimation(Activity.ACT_DIESIMPLE),
        'ANIM_ENDSPECACT': EventHandlerEndSpecAct(),
        'ANIM_STARTCHARGE': EventHandlerStub,
        'ANIM_STOPCHARGE': EventHandlerStub,
        'ANIM_CRASHCHARGE': EventHandlerStub,
        'EFFECT_DOHEAL': 'EventHandlerDoHeal',
    }
    
    # Events for DispatchEvent
    OnNewOrder = 'OnNewOrder'
    OnOrderQueued = 'OnOrderQueued'
    OnAllOrdersCleared = 'OnAllOrdersCleared'
    OnTouch = 'OnTouch'
    OnCoverSpotCleared = 'OnCoverSpotCleared'

    # Default anim config
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=20.0,
        leganimtype=LegAnimType_t.LEGANIM_8WAY,
        useaimsequences=False,
    )
    
    # Variables
    senses = None
    curorder = None
    componentsinitalized = False
    eventcomponents = None
    physobj = None
    nextordersound = 0.0
    nextjumpsound = 0.0
    glowidx = None

    fn_perform_movement = lambda: None
    fn_perform_navigation = lambda: None

    #: Reference to move command, used by locomotion and navigator
    mv = None

    #: Set to True to disable updating the active enemy. Prevents from changing the enemy at all.
    #: No events are dispatched until this is turned back on, even when the enemy dies.
    disable_update_active_enemy = BooleanField(value=False)
    #: Set to True to prevent the enemy selection code from overriding
    #: the current enemy.
    forcedenemy = BooleanField(value=False)
    
    #: Last idle position. The unit will return to this position when too far away when in the idle action
    lastidleposition = vec3_origin
    
    # Think freqs
    think_freq = 0.1

    # Move settings
    #: Max speed this unit can move (hammer units)
    maxspeed = FloatField(value=200.0)
    #: Max turn speed in degrees
    yawspeed = FloatField(value=40.0)
    #: Max jump height (hammer units)
    jumpheight = FloatField(value=60.0)
    #: Gravity modifier
    gravity = FloatField(value=1.0)
    #: The amount we can automatically move up or down without jumping
    stepsize = FloatField(value=18.0)
    
    hulltype = None
    isusingsmallhull = True

    #: Fog of war flags of this unit.
    fowflags = FOWFLAG_UNITS_MASK
    
    #: Activity played when constructing a building. Default is ACT_INVALID.
    constructactivity = ActivityField(value=Activity.ACT_INVALID)
    #: Weapon equiped during building
    constructweapon = ''
    #: Whether this unit is busy constructing something
    constructing = BooleanField(value=False, networked=True, clientchangecallback='OnConstructingChanged')
    #: Range at which this unit constructs a building
    constructmaxrange = 0
    
    #: True if garrisoned inside a building
    garrisoned = BooleanField(value=False)
    #: Handle to garrisoned building
    garrisoned_building = EHandleField(value=None, cppimplemented=True)
    #: Amount of hp repaired per second
    repairhpps = IntegerField(value=10)

    #: Activity played when range attacking.
    attackrange1act = ActivityField(value=Activity.ACT_RANGE_ATTACK1)
    #: Activity played when melee attacking.
    attackmelee1act = ActivityField(value=Activity.ACT_MELEE_ATTACK1)
    #: Activity played when reloading.
    reloadact = ActivityField(value=Activity.ACT_RELOAD)
    #: Activity played when reloading low/crouched.
    reloadact_low = ActivityField(value=Activity.ACT_RELOAD_LOW)
    #: Can execute range attacks while moving to an ordered spot.
    canshootmove = BooleanField(value=False)
    #: Can this unit take cover? Overriden by UnitInfo.
    cantakecover = BooleanField(value=False)
    #: Indicates the unit is in a cover spot
    in_cover = IntegerField(value=0, networked=True, clientchangecallback='OnInCoverChanged')
    #: Particle effect for when the unit is in cover
    incoverparticle = None
    #: Particle effect for cover system name
    incoverparticlename = 'unit_in_cover_B'

    is_nav_obstacle = BooleanField(value=False, networked=True, clientchangecallback='OnIsNavObstacleChanged')

    speed_modifiers = SetField()
    
    useteamcolorglow = True
    
    #: Next time the unit ai will try to attack
    nextattacktime = 0.0
    #: Last time attacked by active enemy
    lastenemyattack = 0.0
    
    # Climbing settings (if the unit supports it)
    #: If true the AI will do the climbing by executing the ActionStartClimbing action.
    aiclimb = True
    #: Offset at which the dismount action should be played before reaching the top.
    climbdismountz = 24.0
    dismounttolerancez = 16.0

    # Think spreading
    timelastspawn = 0.0
    spawnedthisframe = 0
    nextthinktimes = [
        .0, .150, .075, .225, .030, .180, .120, .270, .045, .210, .105, .255, 
        .015, .165, .090, .240, .135, .060, .195, .285,
        .100, .30, .90, .250, .300, .310
    ]
    
    scaleprojectedtexture = 1.25
    
    # Output events
    onneworder = OutputField(keyname='OnNewOrder')
    onorderperformed = OutputField(keyname='OnOrderPerformed')
    onallorderscanceled = OutputField(keyname='OnAllOrdersCanceled')
    
# Commands
if isserver:
    showroute = False
    @concommand('unit_show_route', 'Show unit route', FCVAR_CHEAT)
    def cc_show_route(args):
        global showroute, unitcombatdebugoverlays
        showroute = not showroute
        if showroute:
            unitcombatdebugoverlays |= UnitBaseCombat.OVERLAY_UNITROUTE
        else:
            unitcombatdebugoverlays &= ~UnitBaseCombat.OVERLAY_UNITROUTE
        
        for ul in unitlist.values():
            for unit in ul:
                if showroute:
                    unit.debugoverlays |= UnitBaseCombat.OVERLAY_UNITROUTE
                else:
                    unit.debugoverlays &= ~UnitBaseCombat.OVERLAY_UNITROUTE

    showactions = False
    @concommand('unit_show_actions', 'Show unit actions', FCVAR_CHEAT) 
    def cc_show_actions(args):
        global showactions, unitcombatdebugoverlays
        showactions = not showactions
        if showactions:
            unitcombatdebugoverlays |= UnitBaseCombat.OVERLAY_UNITACTIONS
        else:
            unitcombatdebugoverlays &= ~UnitBaseCombat.OVERLAY_UNITACTIONS
            
        for ul in unitlist.values():
            for unit in ul:
                if showactions:
                    unit.debugoverlays |= UnitBaseCombat.OVERLAY_UNITACTIONS
                else:
                    unit.debugoverlays &= ~UnitBaseCombat.OVERLAY_UNITACTIONS
                    
    showactionsdebug = False
    @concommand('unit_show_actions_debug', 'Show unit actions with debug string', FCVAR_CHEAT) 
    def cc_show_actions_debug(args):
        global showactionsdebug, unitcombatdebugoverlays
        showactionsdebug = not showactionsdebug
        if showactionsdebug:
            unitcombatdebugoverlays |= UnitBaseCombat.OVERLAY_UNITACTIONSDEBUG
        else:
            unitcombatdebugoverlays &= ~UnitBaseCombat.OVERLAY_UNITACTIONSDEBUG
            
        for ul in unitlist.values():
            for unit in ul:
                if showactionsdebug:
                    unit.debugoverlays |= UnitBaseCombat.OVERLAY_UNITACTIONS|UnitBaseCombat.OVERLAY_UNITACTIONSDEBUG
                else:
                    unit.debugoverlays &= ~(UnitBaseCombat.OVERLAY_UNITACTIONS|UnitBaseCombat.OVERLAY_UNITACTIONSDEBUG)

    showunitinfodebug = False
    @concommand('unit_show_unitinfo', 'Show unit info', FCVAR_CHEAT) 
    def cc_show_unitinfo_debug( args ):
        global showunitinfodebug, unitcombatdebugoverlays
        showunitinfodebug = not showunitinfodebug
        if showunitinfodebug:
            unitcombatdebugoverlays |= UnitBaseCombat.OVERLAY_UNITINFO
        else:
            unitcombatdebugoverlays &= ~UnitBaseCombat.OVERLAY_UNITINFO
            
        for ul in unitlist.values():
            for unit in ul:
                if showunitinfodebug:
                    unit.debugoverlays |= UnitBaseCombat.OVERLAY_UNITINFO
                else:
                    unit.debugoverlays &= ~(UnitBaseCombat.OVERLAY_UNITINFO)
                    
                
    showsaidebug = False
    @concommand('unit_show_sai', 'Show unit cpu debug info', FCVAR_CHEAT)
    def cc_show_sai(args):
        global showsaidebug, unitcombatdebugoverlays
        showsaidebug = not showsaidebug
        if showsaidebug:
            unitcombatdebugoverlays |= UnitBaseCombat.OVERLAY_UNITSAI
        else:
            unitcombatdebugoverlays &= ~UnitBaseCombat.OVERLAY_UNITSAI
        
        for ul in unitlist.values():
            for unit in ul:
                if showsaidebug:
                    unit.debugoverlays |= UnitBaseCombat.OVERLAY_UNITSAI
                else:
                    unit.debugoverlays &= ~UnitBaseCombat.OVERLAY_UNITSAI
                    
    @concommand('kill_units', 'Kill selected units', 0)  
    def cc_kill_units(args):
        if isserver:
            if gamerules.info.name == 'destroyhq':
                return

        player = UTIL_GetCommandClient()
        if not player or player.GetTeamNumber() == TEAM_SPECTATOR:
            return
        for unit in player.GetSelection():
            if unit.GetOwnerNumber() != player.GetOwnerNumber():
                continue
            unit.Suicide()
                
    @concommand('units_spread', 'Spread the selected units', 0)  
    def cc_units_spread(args):
        if isserver:
            if gamerules.info.name == 'destroyhq':
                return

        player = UTIL_GetCommandClient()
        if not player:
            return
            
        units = player.GetSelection()
        if not units:
            return

        owner = player.GetOwnerNumber()
        combat_units = []
        for unit in units:
            if not hasattr(unit, 'DispatchEvent'):
                continue
            if unit.GetOwnerNumber() != owner:
                continue
            combat_units.append(unit)

        if not combat_units:
            return
        combat_units[0].SpreadUnits(combat_units)

    # Debug
    @concommand('wars_print_used_hidingspots', '', FCVAR_CHEAT)  
    def cc_print_used_hidingspots(args):
        print(UnitBaseCombat.used_cover_spots)

else:
    @concommand('select_all_army', 'Selects the complete army of the player', 0)  
    def cc_select_all_army(args):
        player = CHL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
            
        ownernumber = player.GetOwnerNumber()
        targetselection = []
        for unit in unitlist[ownernumber]:
            if not isinstance(unit, UnitBaseCombat):
                continue
            targetselection.append(unit)
        player.ClearSelection(False)
        engine.ServerCommand("player_clearselection")
        player.MakeSelection(targetselection)
 
    @concommand('select_all_combat', 'Selects only the combat units of the player', 0)
    def cc_select_all_combat(args):
        player = CHL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
 
        ownernumber = player.GetOwnerNumber()
        targetselection = []
        for unit in unitlist[ownernumber]:
            if unit.unitinfo.resource_category != 'army':
                continue
            if unit.unitinfo.cls_name == 'scrap':
                continue
            if unit.unitinfo.cls_name == 'combine_mine':
                continue
            if unit.unitinfo.cls_name == 'combine_mine_cloaked':
                continue
            targetselection.append(unit)
        player.ClearSelection(False)
        engine.ServerCommand("player_clearselection") 
        player.MakeSelection(targetselection)

    @concommand('select_all_economy', 'Selects only the economy units of the player', 0)
    def cc_select_all_economy(args):
        player = CHL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
 
        ownernumber = player.GetOwnerNumber()
        targetselection = []
        for unit in unitlist[ownernumber]:
            if unit.unitinfo.resource_category != 'economy':
                continue
            targetselection.append(unit)
        player.ClearSelection(False)
        engine.ServerCommand("player_clearselection")
        player.MakeSelection(targetselection)