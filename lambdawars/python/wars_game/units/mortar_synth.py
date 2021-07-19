from srcbase import *
from vmath import *
from entities import networked, entity, Activity, FireBulletsInfo_t, CreateEntityByName
from fields import BooleanField, FlagsField, VectorField, FloatField, UpgradeField, SetField
from gameinterface import CPASAttenuationFilter, CPVSFilter, CPASFilter
from core.units import (UnitInfo, UnitBaseCombat as BaseClass, UnitBaseAirLocomotion, CreateUnitNoSpawn,
    EventHandlerAnimation, GetUnitInfo, UnitBaseAnimState, UnitCombatLocomotion, unitlistpertype)
from core.abilities import AbilityUpgradeValue, GetTechNode
from fow import FogOfWarMgr
if isserver:
    from core.units import UnitCombatAirNavigator, BaseAction, UnitCombatNavigator
    from utils import ExplosionCreate
    from sound import ATTN_NONE
    from gameinterface import CPASAttenuationFilter
    from entities import CEntityFlame, SmokeTrail
import random

@entity('unit_mortar_synth', networked=True)
class UnitMortarSynth(BaseClass):
    aiclimb = False
    LocomotionClass = UnitBaseAirLocomotion
    acttables = {
        Activity.ACT_IDLE : Activity.ACT_IDLE,
    }
    gibmodelnames = [
        'models\Gibs\mortarsynth_gib_1.mdl',
        'models\Gibs\mortarsynth_gib_2.mdl',
        'models\Gibs\mortarsynth_gib_3.mdl',
        'models\Gibs\mortarsynth_gib_4.mdl',
        'models\Gibs\mortarsynth_gib_5.mdl',
    ]
    def Precache(self):
        super().Precache()
        for gibmodelname in self.gibmodelnames:
            self.PrecacheModel(gibmodelname)
        if isserver:
            self.PrecacheScriptSound('Weapon_Mortar.Single')
    if isserver:
        NavigatorClass = UnitCombatAirNavigator
        
        __firetimeout = 0.25
        
        def StartRangeAttack(self, enemy):
            if (gpGlobals.curtime - self.nextattacktime) > self.__firetimeout:
                self.nextattacktime = gpGlobals.curtime - 0.001
        
            info = self.abilitiesbyname.get('mortarattack', None) or self.abilitiesbyname.get('overrun_mortarattack', None)
            
            while self.nextattacktime < gpGlobals.curtime and self.abilitycheckautocast.get(info.uid, False) and info.supportsautocast:
                attackinfo = self.unitinfo.AttackRange
                technode = GetTechNode('mortarsynth_upgrade', self.GetOwnerNumber())
                if technode.techenabled:
                    self.nextattacktime += attackinfo.attackspeed + self.attackspeedboost
                else:
                    self.nextattacktime += attackinfo.attackspeed
                self.DoAnimation(self.ANIM_RANGE_ATTACK1)
                #self.ThrowEnergyGrenade()
            return False
    else:
        def StartRangeAttack(self, enemy):
            self.DoAnimation(self.ANIM_RANGE_ATTACK1)
            return False
    
    def __init__(self):
        super().__init__()
        self.savedrop = 2048.0
        self.maxclimbheight = 256.0
        self.testroutestartheight = 2048.0
        
    def Spawn(self):    
        super().Spawn()
        
        self.SetBloodColor(DONT_BLEED)
        self.locomotion.maxheight = 64.0
        self.locomotion.desiredheight = 64.0
        self.locomotion.flynoiserate = 5.0
        self.locomotion.flynoisez = 10.0
    events = dict(BaseClass.events)
    events.update( {
        'ANIM_RANGE_ATTACK1' : EventHandlerAnimation(Activity.ACT_RANGE_ATTACK1),
    } )
    def MortarSynthAttack(self, event):
        if self.enemyorigin_abi:
            self.ThrowEnergyGrenade(self.enemyorigin_abi)
        elif self.enemy:
            self.ThrowEnergyGrenade(self.enemy.GetAbsOrigin())
    nextshoottime = 0
    def ThrowEnergyGrenade(self, origin):
        if FogOfWarMgr().PointInFOW(origin, self.GetOwnerNumber()):
            #Cancel(cancelmsg='#Ability_NoVision', debugmsg='Player has no vision at target point')
            self.enemyorigin_abi = None
            return
        unit = self
        enemy = unit.enemy
        grenades = self.unitinfo.grenades
        if origin and not self.nextshoottime > gpGlobals.curtime:
            info = unit.unitinfo.AttackRange
            #vGrenadePos = self.GetAbsOrigin() + Vector(0,0,20)
            vGrenadePos = Vector()
            self.GetAttachment( "gun_attach", vGrenadePos )

            #vTarget = Vector()
            #UTIL_PredictedPosition( enemy, 0.5, vTarget ) 
            #vTarget = enemy.GetAbsOrigin()

            from unit_helper import TossGrenadeAnimEventHandler #TODO: FIX THIS
            handler = TossGrenadeAnimEventHandler("grenade_energy", 522)

            for i in range(0, grenades):
                if grenades > 1:
                    position = Vector(random.randint(-90,90),random.randint(-90,90), 0)
                else:
                    position = Vector(0,0,0)
                grenade = handler.TossGrenade(unit, vGrenadePos, origin + position, unit.CalculateIgnoreOwnerCollisionGroup())
                if grenade:
                    grenade.damage = info.damage
                    grenade.damagetype = DMG_BLAST
                    grenade.damageradius = info.radiusdamage
                    grenade.SetThrower(unit)
                
                    filter = CPASAttenuationFilter(unit)

                    unit.EmitSoundFilter( filter, unit.entindex(), "Weapon_Mortar.Single" )
                    info1 = unit.abilitiesbyname.get('mortarattack', None) or self.abilitiesbyname.get('overrun_mortarattack', None)
                    technode = GetTechNode('mortarsynth_upgrade', unit.GetOwnerNumber())
                    if technode.techenabled:
                        unit.nextshoottime = gpGlobals.curtime + unit.unitinfo.AttackRange.attackspeed + unit.attackspeedboost
                        info1.SetRecharge(info1, units=unit, t=unit.attackspeedboost)
                        if self.enemyorigin_abi:
                            unit.nextattacktime += unit.unitinfo.AttackRange.attackspeed + unit.attackspeedboost
                    else:
                        unit.nextshoottime = gpGlobals.curtime + unit.unitinfo.AttackRange.attackspeed
                        info1.SetRecharge(info1, units=unit)
                        if self.enemyorigin_abi:
                            unit.nextattacktime += unit.unitinfo.AttackRange.attackspeed
        self.enemyorigin_abi = None
    def PreDetonate(self):

        self.SetTouch(None)
        self.SetThink(self.Explode)
        self.SetNextThink(gpGlobals.curtime + 0.1)
        #self.SetNextThink(gpGlobals.curtime + 1.0)


    def Explode(self):
        self.takedamage = DAMAGE_NO
        ExplosionCreate(self.WorldSpaceCenter(), self.GetLocalAngles(), self, 1, 128, True )

        info = CTakeDamageInfo(self, self, 1, DMG_GENERIC)
        self.Event_Killed(info)

        # Remove myself a frame from now to avoid doing it in the middle of running AI
        self.SetThink(self.SUB_Remove)
        self.SetNextThink(gpGlobals.curtime)

        nGib = random.randint(2,5)
        for i in range(1, nGib): 
            self.ThrowGibs(i)
    def ThrowGibs(self, i):
        ''' Character killed (only fired once) '''
        vecAbsMins = Vector();
        vecAbsMaxs = Vector()
        self.CollisionProp().WorldSpaceAABB(vecAbsMins, vecAbsMaxs)

        vecNormalizedMins = Vector();
        vecNormalizedMaxs = Vector()
        self.CollisionProp().WorldToNormalizedSpace(vecAbsMins, vecNormalizedMins)
        self.CollisionProp().WorldToNormalizedSpace(vecAbsMaxs, vecNormalizedMaxs)

        vecAbsPoint = Vector()
        filter = CPASFilter(self.GetAbsOrigin())
        self.CollisionProp().RandomPointInBounds(vecNormalizedMins, vecNormalizedMaxs, vecAbsPoint)

        # Throw a flaming, smoking chunk.
        pChunk = CreateEntityByName("gib")
        pChunk.Spawn("models/gibs/hgibs.mdl")
        pChunk.SetBloodColor(DONT_BLEED)

        vecSpawnAngles = QAngle()
        vecSpawnAngles.Random(-90, 90)
        pChunk.SetAbsOrigin(vecAbsPoint)
        pChunk.SetAbsAngles(vecSpawnAngles)

        pChunk.Spawn(self.gibmodelnames[i], random.uniform(6.0, 8.0))
        pChunk.SetOwnerEntity(self)
        pChunk.SetCollisionGroup(COLLISION_GROUP_DEBRIS)
        pPhysicsObject = pChunk.VPhysicsInitNormal(SOLID_VPHYSICS, pChunk.GetSolidFlags(), False)

        # Set the velocity
        if pPhysicsObject:
            pPhysicsObject.EnableMotion(True)
            vecVelocity = Vector()

            angles = QAngle()
            angles.x = random.uniform(-20, 20)
            angles.y = random.uniform(0, 360)
            angles.z = 0.0
            AngleVectors(angles, vecVelocity)

            vecVelocity *= random.uniform(300, 900)
            vecVelocity += self.GetAbsVelocity()

            angImpulse = AngularImpulse()
            angImpulse = RandomAngularImpulse(-180, 180)

            pChunk.SetAbsVelocity(vecVelocity)
            pPhysicsObject.SetVelocity(vecVelocity, angImpulse)

        pFlame = CEntityFlame.Create(pChunk, False)
        if pFlame != None:
            pFlame.SetLifetime(pChunk.lifetime)
    def RepairStep(self, intervalamount, repairhpps):
        if self.health >= self.maxhealth:
            return True
            
        # Cap speed at four or more workers
        n = len(self.constructors)
        if n > 1:
            intervalamount *= (1 + ((n - 1) ** 0.5)) / n
            
        self.health += int(ceil(intervalamount*repairhpps))
        self.health = min(self.health, self.maxhealth)
        if self.health >= self.maxhealth:
            self.OnHealed()
            return True
        return False  
    def OnHealed(self):pass
    def NeedsUnitConstructing(self, unit=None):
        return True
    repairable = True
    constructors = SetField(networked=True, save=False)
    constructability = 'combine_repair'
    if isserver:
        class BehaviorGenericClass(BaseClass.BehaviorGenericClass):
            class ActionDie(BaseAction):
                def OnStart(self):
                    # Will remove the unit after explode:
                    self.outer.PreDetonate()

        aetable = {
            'AE_SYNTH_MORTAR_FIRE' : MortarSynthAttack,
        }
    maxspeed = UpgradeField(value = 112.0, abilityname = 'mortarsynth_upgrade') #TODO: REWORK THIS
    attackspeedboost = -1
    enemyorigin_abi = None
class MortarSynthInfo(UnitInfo):
    name = 'unit_mortar_synth'
    cls_name = 'unit_mortar_synth'
    displayname = '#CombMortarSynth_Name'
    description = '#CombMortarSynth_Description'
    image_name = 'vgui/combine/units/unit_mortar_synth'
    modelname = 'models/MortarSynth.mdl'
    health = 120
    buildtime = 35.0
    costs = [[('requisition', 60), ('power', 90)], [('kills', 6)]]
    attributes = ['synth', 'mechanic']
    #maxspeed = 112
    hulltype = 'HULL_MEDIUM_TALL'
    turnspeed = 200
    viewdistance = 768
    sensedistance = 1792
    techrequirements = ['build_comb_tech_center']
    population = 3
    scalebounds = 0.70
    grenades = 1
    sound_select = 'unit_scanner_select'
    sound_move = 'unit_scanner_move'
    abilities = {
        #0 : 'overrun_mortarattack',
        0 : 'mortarattack',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    class AttackRange(UnitInfo.AttackRange):
        cone = 0.7
        damage = 300.0
        attackspeed = 7.0
        minrange = 128.0
        maxrange = 1792.0
        radiusdamage = 192
    attacks = ['AttackRange']
class OverrunMortarSynthInfo(MortarSynthInfo):
    name = 'overrun_unit_mortar_synth'
    techrequirements = ['or_tier3_research']
    buildtime = 0
    costs = [('kills', 60)]
    abilities = {
        0 : 'overrun_mortarattack',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
class MortarSynthSpeedUpgrade(AbilityUpgradeValue):
    name = 'mortarsynth_upgrade'
    displayname = '#MortarSynthSpeedUpgrade_Name'
    description = '#MortarSynthSpeedUpgrade_Description'
    buildtime = 60.0
    upgradevalue = 144
    costs = [[('requisition', 25), ('power', 25)], [('kills', 2)]]
    techrequirements = []
    image_name = 'vgui/combine/abilities/mortarsynth_upgrade'
    def OnUpgraded(self):
        super().OnUpgraded()
        units = list(unitlistpertype[self.ownernumber]['unit_mortar_synth'])
        for unit in units:
            unit.UpdateLocomotionSettings()