import random
from srcbase import *
from vmath import *
from core.attributes import CoverAttributeInfo
from core.units import (UnitInfo, UnitBaseCombatHuman as BaseClass, EventHandlerAnimation, CreateUnitNoSpawn,
                        PrecacheUnit, GroupMoveOrder, CoverSpot)
from core.abilities import AbilityBase
from core.units.abilities import AbilityTransformUnit
from entities import entity, Activity, CBaseAnimating as BaseClassShield
from fields import ListField, BooleanField, FloatField, EHandleField
from utils import UTIL_PrecacheOther

if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    from utils import UTIL_Remove


@entity('metropolice_shield', networked=True)
class MetroPoliceShield(BaseClassShield):
    shieldmodel = 'models/pg_props/pg_weapons/pg_cp_shield_w.mdl'
    cantakecover = False

    if isserver:
        def Precache(self):
            super().Precache()

            self.PrecacheModel(self.shieldmodel)

        def Spawn(self):
            self.Precache()

            super().Spawn()

            self.SetModel(self.shieldmodel)
    else:
        __last_owner_ent = None

        def OnDataChanged(self, type):
            super().OnDataChanged(type)

            if self.__last_owner_ent != self.GetOwnerEntity():
                self.__last_owner_ent = self.GetOwnerEntity()
                self.UpdateTeamColor()

        def UpdateTeamColor(self):
            owner = self.GetOwnerEntity()
            if owner:
                self.SetTeamColor(owner.GetTeamColor())


@entity('unit_metropolice', networked=True)
class UnitMetroPolice(BaseClass):    
    """ Combine metro police. """
    def Spawn(self):
        super().Spawn()
        
        self.animstate.usecombatstate = True

        if isserver:
            if self.unitinfo.useshield:
                self.AddShield()
                #self.SetThink(self.AddShieldThink, gpGlobals.curtime + 5, 'Test')

    def AddShieldThink(self):
        self.AddShield()

    def UpdateOnRemove(self):
        super().UpdateOnRemove()

        if isserver and self.shield:
            UTIL_Remove(self.shield)
            self.shield = None

    #def OnUnitTypeChanged(self, oldunittype):
    #    super().OnUnitTypeChanged(oldunittype)
    #
    #    self.cantakecover = bool('weapon_stunstick' in self.unitinfo.weapons)

    if isserver:
        def Precache(self):
            super().Precache()
            
            PrecacheUnit('unit_manhack')
            PrecacheUnit('char_scanner')
            UTIL_PrecacheOther('metropolice_shield')
            self.PrecacheScriptSound("unit_metropolice_hurt")

        def UnitThink(self):
            super().UnitThink()

            abi_deploymanhack = self.abilitiesbyname.get('deploymanhack', None)
            self.SetBodygroup(self.METROPOLICE_BODYGROUP_MANHACK,
                              int(bool(abi_deploymanhack and abi_deploymanhack.CanDoAbility(None, unit=self))))
            abi_deployscanner = self.abilitiesbyname.get('deployscanner', None)
            self.SetBodygroup(self.METROPOLICE_BODYGROUP_SCANNER,
                              int(bool(abi_deployscanner and abi_deployscanner.CanDoAbility(None, unit=self))))

        def AddShield(self):
            if self.shield:
                return
            self.shield = CreateEntityByName('metropolice_shield')

            self.shield.SetOwnerEntity(self)
            self.shield.SetOwnerNumber(self.GetOwnerNumber())
            DispatchSpawn(self.shield)
            self.shield.Activate()
            self.shield.FollowEntity(self)

        def Event_Killed(self, info):
            super().Event_Killed(info)

            self.DropShield()

        def DropShield(self):
            if not self.shield:
                return

            gib = CreateEntityByName("gib")
            gib.Spawn(self.shield.GetModelName(), 10.0)
            gib.InitGib(self, 0.0, 0)
            gib.SetAbsOrigin(self.shield.GetAbsOrigin())
            gib.SetAbsAngles(self.shield.GetAbsAngles())

            self.shield.AddEffects(EF_NODRAW)
            self.shield.Remove()
            self.shield = None

    if isclient:
        def OnTeamColorChanged(self):
            super().OnTeamColorChanged()

            if self.shield:
                self.shield.UpdateTeamColor()

        def OnShieldChanged(self):
            if self.shield:
                self.shield.UpdateTeamColor()

    '''if isserver:
        def GrenadeInRangeLOSCheck(self, targetpos, target=None):
            startpos = Vector()
            self.GetAttachment("lefthand", startpos)

            handler = self.aetable[self.COMBINE_AE_GREN_TOSS]

            tossvel = Vector()
            if not handler.GetTossVector(self, startpos, targetpos, self.CalculateIgnoreOwnerCollisionGroup(), tossvel):
                return False

            return True

        class CombineThrowGrenade(TossGrenadeAnimEventHandler):
            def HandleEvent(self, unit, event):
                abi = unit.grenadeability
                if not abi:
                    return

                if abi.grenadeclassname:
                    self.SetGrenadeClass(abi.grenadeclassname)

                startpos = Vector()
                unit.GetAttachment("righthand", startpos)

                targetpos = abi.throwtarget.GetAbsOrigin() if abi.throwtarget else abi.throwtargetpos

                grenade = self.TossGrenade(unit, startpos, targetpos, unit.CalculateIgnoreCollisionGroup())

                if grenade:
                    abi.OnGrenadeThrowed(unit, grenade)
                    grenade.SetVelocity(grenade.GetAbsVelocity(), Vector(0, 0, 0))
                    grenade.SetTimer( 2.5, 2.5 - grenade.FRAG_GRENADE_WARN_TIME )'''

    def GetRequirements(self, requirements, info, player):
        if info.name == 'deploymanhack':
            self.activemanhacks[:] = list(filter(bool, self.activemanhacks))
            if self.activemanhacks:
                requirements.add('maxoneactive')

        if info.name == 'deployscanner':
            self.activescanners[:] = list(filter(bool, self.activescanners))
            if self.activescanners:
                requirements.add('maxoneactive')

    def ReleaseManhacks(self):
        for manhack in self.manhacks:
            # Make us physical
            manhack.RemoveSpawnFlags(manhack.SF_MANHACK_CARRIED)

            # Release us
            manhack.RemoveSolidFlags(FSOLID_NOT_SOLID)
            manhack.SetParent(None)
            
            # Fix pitch/roll
            angles = manhack.GetAbsAngles()
            angles.x = 0.0
            angles.z = 0.0
            manhack.SetAbsAngles(angles)

            # Make us active
            manhack.DispatchEvent('Release')

    def ReleaseScanners(self):
        for scanner in self.scanners:
            #scanner.RemoveSpawnFlags(scanner.SF_MANHACK_CARRIED)

            scanner.RemoveSolidFlags(FSOLID_NOT_SOLID)
            scanner.SetParent(None)

            angles = scanner.GetAbsAngles()
            angles.x = 0.0
            angles.z = 0.0
            scanner.SetAbsAngles(angles)

            scanner.DispatchEvent('Release')
    
    def StartDeployManhackHandler(self, event):
        # TODO
        '''
        if self.nummanhacks <= 0:
            DevMsg("Error: Throwing manhack but out of manhacks!\n")
            return

        self.nummanhacks -= 1

        # Turn off the manhack on our body
        if self.nummanhacks <= 0:
            SetBodygroup(METROPOLICE_BODYGROUP_MANHACK, false)
        '''
        
        self.manhacks = []
        
        for i in range(0, 1):
            # Create the manhack to throw
            manhack = CreateUnitNoSpawn("unit_manhack", owner_number=self.GetOwnerNumber())
            
            vecOrigin = Vector()
            vecAngles = QAngle()

            handAttachment = self.LookupAttachment("LHand")
            self.GetAttachment(handAttachment, vecOrigin, vecAngles)

            manhack.SetLocalOrigin(vecOrigin)
            manhack.SetLocalAngles(vecAngles)
            manhack.AddSpawnFlags(manhack.SF_MANHACK_PACKED_UP|manhack.SF_MANHACK_CARRIED)

            manhack.Spawn()
            manhack.behaviorgeneric.StartingAction = manhack.behaviorgeneric.ActionPreDeployed
            
            # Make us move with his hand until we're deployed
            manhack.SetParent(self, handAttachment)

            self.manhacks.append(manhack)
            self.activemanhacks.append(manhack)

    def StartDeployScannerHandler(self, event):
        self.scanners = []

        for i in range(0, 1):
            # Create the scanner to throw
            scanner = CreateUnitNoSpawn("char_scanner", owner_number=self.GetOwnerNumber())

            vecOrigin = Vector()
            vecAngles = QAngle()

            handAttachment = self.LookupAttachment("LHand")
            self.GetAttachment(handAttachment, vecOrigin, vecAngles)

            scanner.SetLocalOrigin(vecOrigin)
            scanner.SetLocalAngles(vecAngles)
            #scanner.AddSpawnFlags(scanner.SF_MANHACK_PACKED_UP|scanner.SF_MANHACK_CARRIED)

            scanner.Spawn()
            scanner.behaviorgeneric.StartingAction = scanner.behaviorgeneric.ActionPreDeployed

            scanner.SetParent(self, handAttachment)

            self.scanners.append(scanner)
            self.activescanners.append(scanner)
        
    def DeployManhackHandler(self, event):
        self.ReleaseManhacks()
        
        # todo
        for manhack in self.manhacks:
            forward = Vector()
            right = Vector()
            
            self.GetVectors(forward, right, None)
            
            yawOff = right * random.uniform(-1.0, 1.0)

            forceVel = (forward + yawOff * 16.0) + Vector(0, 0, 250)

            manhack.SetAbsVelocity(manhack.GetAbsVelocity() + forceVel)
            
            # Follow the metrocop by default
            manhack.MoveOrder(self.GetAbsOrigin(), target=self)

        self.manhacks = []

    def DeployScannerHandler(self, event):
        self.ReleaseScanners()

        for scanner in self.scanners:
            forward = Vector()
            right = Vector()

            self.GetVectors(forward, right, None)

            yawOff = right * random.uniform(-1.0, 1.0)

            forceVel = (forward + yawOff * 16.0) + Vector(0, 0, 250)

            scanner.SetAbsVelocity(scanner.GetAbsVelocity() + forceVel)

            scanner.MoveOrder(self.GetAbsOrigin(), target=self)

        self.scanners = []

    def UpdateTranslateActivityMap(self):
        if self.insteadyposition or self.steadying:
            tablename = 'stationed'
            if self.activeweapon:
                tablename = self.activeweapon.GetClassname() + '_' + tablename

            if tablename in self.acttransmaps:
                self.animstate.SetActivityMap(self.acttransmaps[tablename])
                return

        if self.defensive_mode:
            tablename = 'shield'
            if self.activeweapon:
                tablename = self.activeweapon.GetClassname() + '_' + tablename

            if tablename in self.acttransmaps:
                self.animstate.SetActivityMap(self.acttransmaps[tablename])
                return
        super().UpdateTranslateActivityMap()

    __active_defensive_attribute = None
    __defensive_mode_applied = False

    def OnInCoverChanged(self):
        if self.in_cover:
            # Will apply again after in cover ended
            if self.__active_defensive_attribute:
                self.RemoveAttribute(self.__active_defensive_attribute)
                self.__active_defensive_attribute = None
        else:
            # Reapply attributes
            self.OnDefensiveModeChanged()

        super().OnInCoverChanged()

    def OnDefensiveModeChanged(self):
        self.UpdateTranslateActivityMap()
        self.UpdateAbilities()

        if self.__active_defensive_attribute:
            self.RemoveAttribute(self.__active_defensive_attribute)
            self.__active_defensive_attribute = None

        if self.defensive_mode:
            self.cover_spot_override = CoverSpot(type=3, angle=self.GetAbsAngles().y)
            self.__active_defensive_attribute = self.cover_type_attributes.get(self.cover_spot_override.type, CoverAttributeInfo)
            self.AddAttribute(self.__active_defensive_attribute)

        # Make sure to apply speed changes ones (make this nicer. Need some general system to apply speed mods?)
        if self.__defensive_mode_applied != self.defensive_mode:
            self.__defensive_mode_applied = self.defensive_mode
            self.mv.maxspeed = self.CalculateUnitMaxSpeed()

            #if self.defensive_mode:
                #self.defensive_mode_speed_redux = 0.35
                #self.mv.maxspeed = self.CalculateUnitMaxSpeed()# * self.defensive_mode_speed_redux
            #else:
                #self.mv.maxspeed = self.CalculateUnitMaxSpeed()# / self.defensive_mode_speed_redux
                #self.defensive_mode_speed_redux = 0

    def CalculateUnitMaxSpeed(self):
        # The base speed
        speed = self.base_max_speed

        # Apply speed modifiers
        for mod in self.speed_modifiers:
            speed_mod = 1 + mod.speed_mod/speed
            speed *= speed_mod
        if self.defensive_mode:
            speed *= self.defensive_mode_speed_redux

        return speed

    def OnSteadyPositionChanged(self):
        self.UpdateTranslateActivityMap()

        if self.insteadyposition:
            if isserver:
                self.locomotion.LockFacing(self.GetAbsAngles().y, 25.0)
                #self.Weapon_Switch(self.Weapon_OwnsThisType('weapon_pistol'))
                #if len(self.attacks) > 0:
                #    self.attacks[0].cone = 0.7
                #    self.minattackcone = min(self.minattackcone, self.attacks[0].cone)

            cover_spots_conf = [
                CoverSpot(type=2, offset=Vector(-48.0, 0, 0), angle=self.GetAbsAngles().y)
            ]
            self.CreateCoverSpots(cover_spots_conf)
        else:
            if isserver:
                self.locomotion.ReleaseFacingLock()
                #self.RebuildAttackInfo()  # Restore cone
                #self.Weapon_Switch(self.Weapon_OwnsThisType('weapon_stunstick'))
            self.DestroyCoverSpots()

            # Was maybe in defensive mode. Restore it.
            self.OnDefensiveModeChanged()

    def TargetOverrideGroupOrder(self, player, data):
        """ Allows overriding the default group order.

            Args:
                player (entity): the player executing the group order
                data (MouseTraceData): Mouse data containing the target position + other information

            Returns a new group order instance to override the default.
        """
        if not self.insteadyposition:
            return None
        # Prevent from doing follow order on unit
        groupmoveorder = GroupMoveOrder(player, data.groundendpos, findhidespot=True)
        groupmoveorder.coverspotsearchradius = 300.0
        return groupmoveorder

    def OnTakeDamage(self, dmginfo):
        if self.lasttakedamage and self.health > 0 and dmginfo.GetDamage() > 0:
            self.EmitSound("unit_metropolice_hurt")

        '''if self.defensive_mode or self.insteadyposition:
            angles = self.GetAbsAngles()
            forward = Vector()
            AngleVectors(angles, forward)

            vec_damage_force = dmginfo.GetDamageForce()
            VectorNormalize(vec_damage_force)
            dot = DotProduct(forward, -vec_damage_force)

            # Scale damage when shield is facing about 45 degrees
            if dot > 0.70:
                dmginfo.ScaleDamage(0.4)

        return super().OnTakeDamage(dmginfo)'''
        return super().OnTakeDamage(dmginfo)
        
    cantakecover = True
    shield = EHandleField(value=None, networked=True, clientchangecallback='OnShieldChanged')
    defensive_mode = BooleanField(value=False, networked=True, helpstring='indicates the police has it\'s shield up',
                                  clientchangecallback='OnDefensiveModeChanged')
    defensive_mode_speed_redux = FloatField(value=0.35)
    
    activemanhacks = ListField(networked=True)
    activescanners = ListField(networked=True)
    insteadyposition = BooleanField(value=False, networked=True, clientchangecallback='OnSteadyPositionChanged')
    steadying = BooleanField(value=False, networked=True, clientchangecallback='OnSteadyPositionChanged')
    hidespots = ListField()

    METROPOLICE_BODYGROUP_MANHACK = 1
    METROPOLICE_BODYGROUP_SCANNER = 1
        
    # Activity translation table
    acttables = dict(BaseClass.acttables)
    acttables.update({
        'default': {
            Activity.ACT_MP_JUMP: Activity.ACT_JUMP,
            Activity.ACT_CROUCH: Activity.ACT_COVER_PISTOL_LOW,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
        },
        'weapon_pistol': {
            Activity.ACT_IDLE: Activity.ACT_IDLE_PISTOL,
            Activity.ACT_WALK: Activity.ACT_WALK_PISTOL,
            Activity.ACT_RUN: Activity.ACT_RUN_PISTOL,
            
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_RANGE_ATTACK_PISTOL,
            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_RANGE_ATTACK_PISTOL,
            Activity.ACT_WALK_AIM: Activity.ACT_WALK_AIM_PISTOL,
            Activity.ACT_RUN_AIM: Activity.ACT_RUN_AIM_PISTOL,
            
            Activity.ACT_MP_JUMP: Activity.ACT_JUMP,
            Activity.ACT_CROUCH: Activity.ACT_COVER_PISTOL_LOW,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_WALK_AIM,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_AIM,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_ATTACK_PISTOL,
        },
        'weapon_smg1': {
            Activity.ACT_IDLE: Activity.ACT_IDLE_SMG1,
            Activity.ACT_WALK: Activity.ACT_WALK_RIFLE,
            Activity.ACT_RUN: Activity.ACT_RUN_RIFLE,
            
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_RANGE_ATTACK_SMG1,
            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_RANGE_ATTACK_SMG1,
            Activity.ACT_WALK_AIM: Activity.ACT_WALK_AIM_RIFLE,
            Activity.ACT_RUN_AIM: Activity.ACT_RUN_AIM_RIFLE,
            
            Activity.ACT_MP_JUMP: Activity.ACT_JUMP,
            Activity.ACT_CROUCH: Activity.ACT_COVER_SMG1_LOW,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_WALK_AIM,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_AIM,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,
        },
        'weapon_stunstick': {
            Activity.ACT_MELEE_ATTACK1 : Activity.ACT_MELEE_ATTACK_SWING,
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_MELEE_ATTACK_SWING,
            Activity.ACT_CROUCH: Activity.ACT_COVER_PISTOL_LOW,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_IDLE,
            Activity.ACT_RUN_AIM: Activity.ACT_RUN,

        },
        'weapon_stunstick_shield': {
            Activity.ACT_IDLE: 'ACT_IDLE_ANGRY_HOLD_SHIELD',
            Activity.ACT_WALK: 'ACT_WALK_SHIELD_ANGRY',
            Activity.ACT_RUN: 'ACT_WALK_SHIELD_ANGRY',

            Activity.ACT_MELEE_ATTACK1: 'ACT_MELEE_ATTACK_SWING_SHIELD',
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_MELEE_ATTACK_SWING,
            Activity.ACT_CROUCH: 'ACT_SHIELD_STATIONED_CROUCH',
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_IDLE_AIM_AGITATED,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_IDLE_AIM_AGITATED: 'ACT_IDLE_ANGRY_HOLD_SHIELD',
            Activity.ACT_WALK_AIM: 'ACT_WALK_SHIELD_ANGRY',
            Activity.ACT_RUN_AIM: 'ACT_WALK_SHIELD_ANGRY',
        },
        'weapon_stunstick_stationed': {
            Activity.ACT_IDLE: 'ACT_SHIELD_STATIONED',
            Activity.ACT_WALK: 'ACT_WALK_SHIELD_ANGRY',
            Activity.ACT_RUN: 'ACT_WALK_SHIELD_ANGRY',

            Activity.ACT_MELEE_ATTACK1: 'ACT_MELEE_ATTACK_SWING_STATIONED_CROUCH',
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_MELEE_ATTACK_SWING,
            Activity.ACT_CROUCH: 'ACT_SHIELD_STATIONED_CROUCH',
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: 'ACT_SHIELD_STATIONED_CROUCH',
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_IDLE_AIM_AGITATED: 'ACT_SHIELD_STATIONED_CROUCH',
            Activity.ACT_WALK_AIM: 'ACT_WALK_SHIELD_ANGRY',
            Activity.ACT_RUN_AIM: 'ACT_WALK_SHIELD_ANGRY',
        },
    })
    
    # Custom activities
    activitylist = list(BaseClass.activitylist)
    activitylist.extend([
        'ACT_METROPOLICE_DRAW_PISTOL',
        'ACT_METROPOLICE_DEPLOY_MANHACK',
        'ACT_METROPOLICE_FLINCH_BEHIND',
        'ACT_METROPOLICE_POINT',

        'ACT_WALK_BATON',
        'ACT_IDLE_ANGRY_BATON',
        'ACT_PUSH_PLAYER',
        'ACT_MELEE_ATTACK_THRUST',
        'ACT_ACTIVATE_BATON',
        'ACT_DEACTIVATE_BATON',

        'ACT_IDLE_HOLD_SHIELD',
        'ACT_RUN_SHIELD',
        'ACT_MELEE_ATTACK_SWING_SHIELD',
        'ACT_IDLE_ANGRY_HOLD_SHIELD',
        'ACT_WALK_SHIELD_ANGRY',
        'ACT_SHIELD_STATIONED',
        'ACT_SHIELD_STATIONED_CROUCH',
        'ACT_MELEE_ATTACK_SWING_STATIONED_CROUCH',
        'ACT_SHIELD_STATIONED_SETUP',
    ])
    
    constructactivity = 'ACT_MELEE_ATTACK_THRUST'
    
    # Events
    events = dict(BaseClass.events)
    events.update({
        'ANIM_DEPLOYMANHACK': EventHandlerAnimation('ACT_METROPOLICE_DEPLOY_MANHACK'),
        'ANIM_DEPLOYSCANNER': EventHandlerAnimation('ACT_METROPOLICE_DEPLOY_MANHACK'),
        'ANIM_SHIELD_STATIONED_SETUP': EventHandlerAnimation('ACT_SHIELD_STATIONED_SETUP'),
        'ANIM_TOSS_GRENADE' : EventHandlerAnimation('ACT_MELEE_ATTACK_SWING_SHIELD'),
    })
    
    # Ability sounds
    abilitysounds = {
        'attackmove': 'ability_comb_mp_attackmove',
        'holdposition': 'ability_comb_mp_holdposition',
        'grenade': 'ability_combine_grenade',
        'deployturret': 'ability_combine_deployturret',
        'deploymine': 'ability_combine_deploymine',
        'deploymanhacks': 'ability_combine_deploymanhacks',
        'deployscanners': 'ability_combine_deploymanhacks',
    }

    if isserver:
        # Animation Events
        #COMBINE_AE_GREN_TOSS = 7

        aetable = {
            'AE_METROPOLICE_BATON_ON': None,
            'AE_METROPOLICE_BATON_OFF': None,
            'AE_METROPOLICE_SHOVE': None,
            'AE_METROPOLICE_START_DEPLOY': StartDeployManhackHandler,
            'AE_METROPOLICE_START_DEPLOY_SCANNER': StartDeployScannerHandler,
            'AE_METROPOLICE_DRAW_PISTOL': None,
            'AE_METROPOLICE_DEPLOY_MANHACK': DeployManhackHandler,
            #'AE_METROPOLICE_DEPLOY_SCANNER': DeployScannerHandler,
            #'COMBINE_AE_GREN_TOSS' : CombineThrowGrenade('grenade_frag', COMBINE_GRENADE_THROW_SPEED),
        }
    
    class AnimStateClass(BaseClass.AnimStateClass):
        def __init__(self, outer, animconfig):
            super().__init__(outer, animconfig)
            self.newjump = False
            
        def OnNewModel(self):
            super().OnNewModel()
            
            studiohdr = self.outer.GetModelPtr()
            
            self.bodyyaw = self.outer.LookupPoseParameter("body_yaw")
            self.bodypitch = self.outer.LookupPoseParameter("aim_pitch")
            
            aimyaw = self.outer.LookupPoseParameter(studiohdr, "aim_yaw")
            if aimyaw < 0:
                return
            self.outer.SetPoseParameter(studiohdr, aimyaw, 0.0)
            
            headpitch = self.outer.LookupPoseParameter(studiohdr, "head_pitch")
            if headpitch < 0:
                return
            headyaw = self.outer.LookupPoseParameter(studiohdr, "head_yaw")
            if headyaw < 0:
                return
            headroll = self.outer.LookupPoseParameter(studiohdr, "head_roll")
            if headroll < 0:
                return
                
            self.outer.SetPoseParameter(studiohdr, headpitch, 0.0)
            self.outer.SetPoseParameter(studiohdr, headyaw, 0.0)
            self.outer.SetPoseParameter(studiohdr, headroll, 0.0)
            
            spineyaw = self.outer.LookupPoseParameter(studiohdr, "spine_yaw")
            if spineyaw < 0:
                return
                
            self.outer.SetPoseParameter(studiohdr, spineyaw, 0.0)

class MetroPoliceInfo(UnitInfo):
    name = 'unit_metropolice'
    cls_name = 'unit_metropolice'
    hulltype = 'HULL_HUMAN'
    displayname = '#CombMetroPolice_Name'
    description = '#CombMetroPolice_Description'
    image_name = 'vgui/combine/units/unit_metropolice'
    portrait = 'resource/portraits/combineSMG.bik'
    costs = [[('requisition', 10)], [('kills', 1)]]
    buildtime = 10.0
    health = 150
    maxspeed = 232
    viewdistance = 768
    scrapdropchance = 0.0
    accuracy = 0.80
    attributes = ['light']
    sound_select = 'unit_combine_metropolice_select'
    sound_move = 'unit_combine_metropolice_move'
    sound_attack = 'unit_combine_metropolice_attack'
    sound_death = 'unit_combine_metropolice_death'
    modelname = 'models/police.mdl'
    #tier = 1
    abilities = {
        -2: 'garrison',
        -1: 'construct_floorturret',
        0: 'deploymanhack',
        1: 'floor_turret',
        5: 'comb_mp_transform_smg1',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    weapons = ['weapon_pistol']
    useshield = False
    cantakecover = True


class MetroPoliceSMG1Info(MetroPoliceInfo):
    name = 'unit_metropolice_smg1'
    displayname = '#CombMetroPoliceSMG1_Name'
    description = '#CombMetroPoliceSMG1_Description'
    image_name = 'vgui/combine/units/unit_metropolice_smg'
    weapons = ['weapon_smg1']
    costs = [[('requisition', 15)], [('kills', 1)]]
    buildtime = 23.0
    maxspeed = 224
    viewdistance = 768
    scrapdropchance = 0.0
    #techrequirements = ['build_comb_armory']
    abilities = {
        -2: 'garrison',
        -1: 'construct_floorturret',
        0: 'deploymanhack',
        1: 'floor_turret',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }


class MetroPoliceRiotInfo(MetroPoliceInfo):
    name = 'unit_metropolice_riot'
    displayname = '#CombMetroPoliceRiot_Name'
    description = '#CombMetroPoliceRiot_Description'
    image_name = 'vgui/combine/units/unit_riot_police'
    modelname = 'models/police_extended.mdl'
    #weapons = ['weapon_pistol', 'weapon_stunstick']
    weapons = ['weapon_stunstick']
    costs = [[('requisition', 15)], [('kills', 1)]]
    buildtime = 10.0
    maxspeed = 232
    health = 200
    viewdistance = 768
    scrapdropchance = 0.0
    abilities = {
        2: 'defensive_mode',
        3: 'attack_mode',
        4: 'riot_formation',
        5: 'riot_station',
        #7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    useshield = True
    cantakecover = False


class OverrunMetroPoliceInfo(MetroPoliceInfo):
    name = 'overrun_unit_metropolice'
    hidden = True
    buildtime = 0
    tier = 0
    abilities = {
        -1: 'construct_floorturret',
        0: 'overrun_combine_mine',
        1: 'overrun_floor_turret',
        2: 'overrun_deploymanhack',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }


class OverrunMetroPoliceRiotInfo(MetroPoliceRiotInfo):
    name = 'overrun_unit_metropolice_riot'
    hidden = True
    tier = 0
    buildtime = 0
    abilities = {
        -1: 'construct_floorturret',
        0: 'overrun_deploymanhack',
        1: 'overrun_floor_turret',
        2: 'defensive_mode',
        3: 'attack_mode',
        4: 'riot_formation',
        5: 'riot_station',
        #7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }


class TransformToMetropoliceSMG1(AbilityTransformUnit):
    name = 'comb_mp_transform_smg1'
    displayname = '#CombTransMPSMG1_Name'
    description = '#CombTransMPSMG1_Description'
    transform_type = 'unit_metropolice_smg1'
    transform_time = 3.0
    replaceweapons = True
    #techrequirements = ['build_comb_armory']
    costs = [('requisition', 10)]
    image_name = 'vgui/combine/abilities/combine_transform_smg'
    activatesoundscript = 'ability_combine_smg1_upgrade'


# Mission Versions
class MissionMetroPoliceInfo(MetroPoliceInfo):
    name = 'mission_unit_metropolice'
    hidden = True
    buildtime = 0
    maxspeed = 250.0
    viewdistance = 600
    sensedistance = 700
    health = 55
    abilities = {
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    weapons = ['weapon_stunstick']


class AbilityDefensiveMode(AbilityBase):
    # Info
    name = "defensive_mode"
    image_name = 'vgui/combine/abilities/combine_shield_up.vmt'
    rechargetime = 1
    displayname = "#AbilityDefensiveMode_Name"
    description = "#AbilityDefensiveMode_Description"
    hidden = True
    sai_hint = AbilityBase.sai_hint | set(['sai_raiseshield']) #TODO: change this

    # Ability Code
    def Init(self):
        super().Init()

        # Just do the ability on creation ( == when you click the ability slot )
        self.SelectGroupUnits()

        for unit in self.units:
            unit.defensive_mode = True
            unit.OnDefensiveModeChanged()
        self.SetRecharge(self.units)
        self.Completed()

    @classmethod
    def ShouldShowAbility(info, unit):
        return not unit.defensive_mode

    serveronly = True # Do not instantiate on the client


class AbilityAttackMode(AbilityBase):
    # Info
    name = "attack_mode"
    image_name = 'vgui/combine/abilities/combine_shield_down.vmt'
    rechargetime = 1
    displayname = "#AbilityAttackMode_Name"
    description = "#AbilityAttackMode_Description"
    hidden = True
    sai_hint = AbilityBase.sai_hint | set(['sai_lowershield']) #TODO: change this

    # Ability Code
    def Init(self):
        super().Init()

        # Just do the ability on creation ( == when you click the ability slot )
        self.SelectGroupUnits()

        for unit in self.units:
            unit.defensive_mode = False
            unit.OnDefensiveModeChanged()
        self.SetRecharge(self.units)
        self.Completed()

    @classmethod
    def ShouldShowAbility(info, unit):
        return unit.defensive_mode

    serveronly = True # Do not instantiate on the client

# =========================================================================================================================================
# ============================================================ Character Units ============================================================
# =========================================================================================================================================

class CharacterMetroPoliceSupport(MetroPoliceInfo):
    name = 'char_metropolice_support'
    displayname = '#CharMetroSupport_Name'
    description = '#CharMetroSupport_Description'
    maxspeed = 250
    viewdistance = 800
    health = 900
    buildtime = 0.01
    scrapdropchance = 1.0
    costs = []
    population = 1
    attributes = ['support']
    tier = 0
    abilities = {
        -2: 'garrison',
        -1: 'construct_floorturret',
        0: 'char_deploymanhack',
        1: 'char_floor_turret',
        2: 'char_combine_mine',
        3: 'build_char_comb_regenerationpost',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    recharge_other_abilities = {
        'char_combine_soldier',
        'char_combine_elite',
        'char_metropolice_support',
        'char_metropolice_tank',
        'char_metropolice_scout',
        'char_rebel_scout',
        'char_rebel_flamer',
        'char_rebel_veteran',
        'char_rebel_rpg',
        'char_rebel_engineer',
        'char_rebel_medic',
        'char_rebel_soldier',
    }
    rechargetime = 180.0

class CharacterMetroPoliceScout(MetroPoliceSMG1Info):
    name = 'char_metropolice_scout'
    displayname = '#CharMetroScout_Name'
    description = '#CharMetroScout_Description'
    maxspeed = 290
    viewdistance = 800
    unitenergy = 100
    health = 800
    buildtime = 0.01
    scrapdropchance = 1.0
    costs = []
    population = 1
    attributes = ['scout']
    tier = 0
    abilities = {
        -1: 'garrison',
        0: 'deployscanner',
        1: 'scan_char',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    weapons = ['weapon_smg1']
    recharge_other_abilities = {
        'char_combine_soldier',
        'char_combine_elite',
        'char_metropolice_support',
        'char_metropolice_tank',
        'char_metropolice_scout',
        'char_rebel_scout',
        'char_rebel_flamer',
        'char_rebel_veteran',
        'char_rebel_rpg',
        'char_rebel_engineer',
        'char_rebel_medic',
        'char_rebel_soldier',
    }
    rechargetime = 180.0

class CharacterMetroPoliceTank(MetroPoliceRiotInfo):
    name = 'char_metropolice_tank'
    displayname = '#CharMetroTank_Name'
    description = '#CharMetroTank_Description'
    maxspeed = 260
    viewdistance = 600
    health = 1200
    buildtime = 0.01
    scrapdropchance = 1.0
    accuracy = 3.0
    costs = []
    techrequirements = []
    population = 1
    attributes = ['tank']
    tier = 0
    abilities = {
        0: 'char_deploymanhack',
        1: 'char_mp_transform_smg1',
        2: 'defensive_mode',
        3: 'attack_mode',
        5: 'riot_station',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    recharge_other_abilities = {
        'char_combine_soldier',
        'char_combine_elite',
        'char_metropolice_support',
        'char_metropolice_tank',
        'char_metropolice_scout',
        'char_rebel_scout',
        'char_rebel_flamer',
        'char_rebel_veteran',
        'char_rebel_rpg',
        'char_rebel_engineer',
        'char_rebel_medic',
        'char_rebel_soldier',
    }
    rechargetime = 180.0
    useshield = True

class CharacterMetroPoliceTankSMG(CharacterMetroPoliceTank):
    name = 'char_metropolice_tank_smg1'
    maxspeed = 220
    viewdistance = 800
    health = 1200
    population = 1
    attributes = ['support']
    abilities = {
        0: 'char_deploymanhack',
        1: 'char_mp_transform_tank',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    weapons = ['weapon_smg1']
    useshield = True

class TransformToMetropoliceTankSMG1(AbilityTransformUnit):
    name = 'char_mp_transform_smg1'
    displayname = '#CombTransMPSMG1_Name'
    description = '#CombTransMPSMG1_Description'
    transform_type = 'char_metropolice_tank_smg1'
    transform_time = 6.0
    replaceweapons = True
    #techrequirements = ['build_comb_armory']
    costs = []
    image_name = 'vgui/combine/units/unit_metropolice_smg'
    activatesoundscript = 'ability_combine_smg1_upgrade'

class TransformToMetropoliceTank(AbilityTransformUnit):
    name = 'char_mp_transform_tank'
    displayname = '#CombTransMPSMG1_Name'
    description = '#CombTransMPSMG1_Description'
    transform_type = 'char_metropolice_tank'
    transform_time = 6.0
    replaceweapons = True
    #techrequirements = ['build_comb_armory']
    costs = []
    image_name = 'vgui/combine/units/unit_riot_police'
    activatesoundscript = "Weapon_StunStick.Activate"