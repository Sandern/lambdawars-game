from vmath import Vector, QAngle, vec3_origin
from core.abilities import AbilityTarget
from playermgr import OWNER_ENEMY, OWNER_LAST
from fields import FloatField, StringField, IntegerField
from fow import FogOfWarMgr
from navmesh import NavMeshGetPositionNearestNavArea

if isserver:
    from entities import CreateEntityByName, DispatchSpawn, variant_t, g_EventQueue
    from core.units import CreateUnitNoSpawn, PlaceUnit
    from utils import UTIL_RemoveImmediate

class AbilityCanister(AbilityTarget):
    """ Launches a headcrab canister
    """
    name = 'launch_headcrabcanister'
    displayname = "#AbilityLaunchHeadcrabCanister_Name"
    description = "#AbilityLaunchHeadcrabCanister_Description"
    image_name = 'vgui/combine/abilities/combine_launch_headcrab'
    rechargetime = 12.0
    maxrange = FloatField(value=8192.0)
    costs = [('requisition', 12), ('power', 5)]
    overrunmode = False
    headcrabtype = StringField(value='unit_headcrab')
    headcrabcount = IntegerField(value=5)
    ability_owner_enemy = True
    recharge_other_abilities = [
        'launch_headcrabcanister',
        'launch_headcrabcanister_fasttype',
        'launch_headcrabcanister_poisontype',
        'launch_headcrabcanister_emptytype',
    ]

    @classmethod 
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)
        if not info.overrunmode and not unit.powered:
            requirements.add('powered')
        return requirements
    
    if isserver:
        spotid = 0

        def PreSpawnHeadcrab(self, headcrab):
            headcrab.BehaviorGenericClass = headcrab.BehaviorRoamingClass

        def LaunchHeadcrabCanister(self, startpos, endpos, owner):
            launch_headcrabcanister_spotname = 'launch_headcrabcanister_spot%d' % (AbilityCanister.spotid)
            AbilityCanister.spotid += 1
            
            # Create a launch spot
            spot = CreateEntityByName("info_target")
            spot.KeyValue("targetname", launch_headcrabcanister_spotname)
            spot.SetAbsOrigin(startpos)
            spot.SetAbsAngles(QAngle(60, 0, 0))
            DispatchSpawn(spot)
    
            # Create and setup the canister
            can = CreateUnitNoSpawn("unit_headcrabcanister")
            can.launcher_owner = self.ownernumber
            can.SetOwnerNumber(owner)
            can.KeyValue("name", "head")
            try:
                can.KeyValue("HeadcrabType", str(can.headcrabclass.index(self.headcrabtype)))
            except ValueError:
                can.KeyValue("HeadcrabType", "0")
            can.KeyValue("HeadcrabCount", str(self.headcrabcount))
            can.KeyValue("FlightSpeed", "512")
            can.KeyValue("FlightTime", "2")
            can.KeyValue("Damage", "150")
            can.KeyValue("DamageRadius", "250")
            can.KeyValue("LaunchPositionName", launch_headcrabcanister_spotname)
            can.lifetime = 30.0
            can.SetAbsOrigin(endpos)
            can.SetAbsAngles(QAngle(-90, 0, 0))
            can.fnprespawnheadcrab = self.PreSpawnHeadcrab
            if not PlaceUnit(can, endpos, maxradius=256.0):
                UTIL_RemoveImmediate(can)
                return False
            DispatchSpawn(can)
            can.Activate()
            
            launcheta = 1.0
            g_EventQueue.AddEvent(can, "FireCanister", variant_t(), launcheta, None, None, 0)
            g_EventQueue.AddEvent(spot, "kill", variant_t(), launcheta + 1.0, None, None, 0)

            return True
                
        def DoAbility(self):
            data = self.mousedata
            targetpos = data.endpos
            owner = self.ownernumber
            
            adjustedtargetpos = NavMeshGetPositionNearestNavArea(targetpos, beneathlimit=2048.0)
            if adjustedtargetpos != vec3_origin:
                targetpos = adjustedtargetpos
            
            if self.ischeat:
                startpos = self.player.GetAbsOrigin() + Vector(512.0, 90.0, 712.0)
                self.LaunchHeadcrabCanister(startpos, targetpos, owner)
                self.Completed()
                return
                
            if FogOfWarMgr().PointInFOW(targetpos, owner):
                self.Cancel(cancelmsg='#Ability_NoVision', debugmsg='Player has no vision at target point')
                return
                
            if not self.overrunmode and not self.unit.powered:
                self.Cancel(cancelmsg='#Ability_NotPowered', debugmsg='Not in power generator range')
                return
                
            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources', debugmsg='not enough resources')
                return
                
            startpos = self.unit.GetAbsOrigin()
            dist = startpos.DistTo(targetpos)
            if dist > self.maxrange:
                self.Cancel(cancelmsg='#Ability_OutOfRange', debugmsg='must be fired within range')
                return
            ability_owner = OWNER_ENEMY if self.ability_owner_enemy else OWNER_LAST+14
            self.unit.DoLaunchAnimation(launchendtime=2.0)
            if not self.LaunchHeadcrabCanister(startpos, targetpos, ability_owner):
                self.Cancel(cancelmsg='#Ability_InvalidPosition', debugmsg='must be fired within range')
                return
            self.SetRecharge(self.unit)
            self.Completed()
        
    def UpdateParticleEffects(self, inst, targetpos):
        if not self.unit:
            return
        inst.SetControlPoint(0, self.unit.GetAbsOrigin() + self.particleoffset)
        inst.SetControlPoint(2, Vector(self.maxrange, self.maxrange, 0))
        inst.SetControlPoint(4, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
        
    infoparticles = ['range_radius']

class AbilityCanisterFastType(AbilityCanister):
    name = 'launch_headcrabcanister_fasttype'
    headcrabtype = 'unit_headcrab_fast'
    headcrabcount = 4
    #maxrange = FloatField(value=5120.0)
    costs = [('requisition', 15), ('power', 5)]
    image_name = 'vgui/combine/abilities/combine_launch_fast_headcrab'
    displayname = "#AbilityLaunchHeadcrabFastCanister_Name"
    description = "#AbilityLaunchHeadcrabFastCanister_Description"

class AbilityCanisterPoisonType(AbilityCanister):
    name = 'launch_headcrabcanister_poisontype'
    headcrabtype = 'unit_headcrab_poison'
    headcrabcount = 6
    #maxrange = FloatField(value=5120.0)
    costs = [('requisition', 12), ('power', 5)]
    image_name = 'vgui/combine/abilities/combine_launch_poison_headcrab'
    displayname = "#AbilityLaunchHeadcrabPoisonCanister_Name"
    description = "#AbilityLaunchHeadcrabPoisonCanister_Description"

class AbilityCanisterPoisonBossType(AbilityCanister):
    name = 'launch_headcrabcanister_poisonbosstype'
    headcrabtype = 'unit_headcrab_poison_boss'
    headcrabcount = 1
    costs = [('requisition', 150), ('power', 300)]

class AbilityCanisterEmptyType (AbilityCanister):
    name = 'launch_headcrabcanister_emptytype'
    headcrabcount = 0
    costs = [('requisition', 10), ('power', 5)]
    #costs = [('power', 5)]
    #maxrange = FloatField(value=7680.0)
    image_name = 'vgui/combine/abilities/combine_launch_empty_shell'
    displayname = "#AbilityLaunchHeadcrabEmptyCanister_Name"
    description = "#AbilityLaunchHeadcrabEmptyCanister_Description"
    rechargetime = 10

    def UpdateParticleEffects(self, inst, targetpos):
        if not self.unit:
            return
        inst.SetControlPoint(0, self.unit.GetAbsOrigin() + self.particleoffset)
        inst.SetControlPoint(2, Vector(self.maxrange, self.maxrange, 0))
        inst.SetControlPoint(4, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
        
    infoparticles = ['range_radius']




class OverrunAbilityCanister(AbilityCanister):
    name = 'overrun_launch_headcrabcanister'
    costs = []
    overrunmode = True
    rechargetime = 30
    ability_owner_enemy = False
    recharge_other_abilities = [
        'overrun_launch_headcrabcanister',
        'overrun_launch_headcrabcanister_fasttype',
        'overrun_launch_headcrabcanister_poisontype',
        'overrun_launch_headcrabcanister_emptytype',
    ]
class OverrunAbilityCanisterFastType(AbilityCanisterFastType):
    name = 'overrun_launch_headcrabcanister_fasttype'
    costs = []
    overrunmode = True
    rechargetime = 45
    ability_owner_enemy = False
    recharge_other_abilities = [
        'overrun_launch_headcrabcanister',
        'overrun_launch_headcrabcanister_fasttype',
        'overrun_launch_headcrabcanister_poisontype',
        'overrun_launch_headcrabcanister_emptytype',
    ]
class OverrunAbilityCanisterPoisonType(AbilityCanisterPoisonType):
    name = 'overrun_launch_headcrabcanister_poisontype'
    costs = []
    overrunmode = True
    rechargetime = 30
    ability_owner_enemy = False
    recharge_other_abilities = [
        'overrun_launch_headcrabcanister',
        'overrun_launch_headcrabcanister_fasttype',
        'overrun_launch_headcrabcanister_poisontype',
        'overrun_launch_headcrabcanister_emptytype',
    ]
class OverrunAbilityCanisterEmptyType (AbilityCanisterEmptyType):
    name = 'overrun_launch_headcrabcanister_emptytype'
    costs = []
    rechargetime = 20
    overrunmode = True
    ability_owner_enemy = False
    recharge_other_abilities = [
        'overrun_launch_headcrabcanister',
        'overrun_launch_headcrabcanister_fasttype',
        'overrun_launch_headcrabcanister_poisontype',
        'overrun_launch_headcrabcanister_emptytype',
    ]