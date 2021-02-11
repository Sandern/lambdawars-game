from srcbase import *
from math import ceil
from core.resources import TakeResources, resources
from te import CEffectData, DispatchEffect, te
from vmath import *
from entities import networked, entity, Activity, FireBulletsInfo_t, CreateEntityByName
from fields import BooleanField, UpgradeField, SetField
from gamerules import GetAmmoDef
from core.abilities import AbilityUpgrade, AbilityUpgradeValue, AbilityInstant
from core.units import (UnitInfo, UnitBaseCombat as BaseClass, UnitBaseAirLocomotion, CreateUnitNoSpawn,
    EventHandlerAnimation, GetUnitInfo, UnitBaseAnimState, UnitCombatLocomotion)
from gameinterface import CPASAttenuationFilter, CPVSFilter, CPASFilter

if isserver:
    from core.units import UnitCombatAirNavigator, BaseAction, UnitCombatNavigator
    from entities import CSprite, CGib, CEntityFlame, SmokeTrail
    from utils import UTIL_Remove, UTIL_PrecacheOther, ExplosionCreate
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
    from sound import ATTN_NONE
    from gameinterface import CPASAttenuationFilter
import random

@entity('unit_crab_synth', networked=True)
class UnitCrabSynth(BaseClass):
    def __init__(self):
        super().__init__()

        self.serverdoimpactandtracer = True
        
        self.tracercolor = Vector(0.1882, 0.502, 0.596)
    
    gibmodelnames = [
		'models\Gibs\synth_gib1.mdl',
		'models\Gibs\synth_gib2.mdl',
		'models\Gibs\synth_gib3.mdl',
		'models\Gibs\synth_gib4.mdl',
		'models\Gibs\synth_gib5.mdl',
		'models\Gibs\synth_gib6.mdl',
		'models\Gibs\synth_gib7.mdl',
    ]
    if isserver:
        def Precache(self):
            super().Precache()
            if self.shouldgib:
                for gibmodelname in self.gibmodelnames:
                    self.PrecacheModel(gibmodelname)
        
            self.PrecacheScriptSound('Weapon_AR2.Single') 
            self.PrecacheScriptSound('NPC_HeadCrab.Die')
        __firetimeout = 0.25
        
        def StartRangeAttack(self, enemy):
            if (gpGlobals.curtime - self.nextattacktime) > self.__firetimeout:
                self.nextattacktime = gpGlobals.curtime - 0.001
        
            while self.nextattacktime < gpGlobals.curtime:
                attackinfo = self.unitinfo.AttackRange
                self.nextattacktime += attackinfo.attackspeed
                self.FireCannon()
                #self.DoAnimation(self.ANIM_RANGE_ATTACK1)
            return False
    else:
        def StartRangeAttack(self, enemy):
            #self.DoAnimation(self.ANIM_RANGE_ATTACK1)
            return False
    def Spawn(self):
        super().Spawn()
        ammodef = GetAmmoDef()
        self.ammotype = ammodef.Index("AR2")
        self.SetBloodColor(DONT_BLEED)
    def FireCannon(self):
        if not self.enemy:
            return

        # Fire directly at the target
        target_pos = self.enemy.BodyTarget(self.GetAbsOrigin())
        #vecMuzzle = Vector()
        angAimDir = QAngle()
        vecMuzzle = self.GetAbsOrigin() + Vector(0,0,100)
        vecToEnemy = target_pos - vecMuzzle

        VectorNormalize( vecToEnemy )
        info = FireBulletsInfo_t()
        info.ammotype = self.ammotype
        info.shots = 1
        info.vecsrc = vecMuzzle
        info.vecdirshooting = vecToEnemy
        info.vecspread = vec3_origin
        info.distance = self.unitinfo.AttackRange.maxrange + 128
        info.tracerfreq = 1
        info.damage = self.unitinfo.AttackRange.damage

        self.FireBullets(info)
        self.DoMuzzleFlash()

        self.EmitSound('Weapon_AR2.Single')
    def DoMuzzleFlash(self):
        super().DoMuzzleFlash()
        
        data = CEffectData()
        
        data.attachmentindex = self.LookupAttachment( "muzzle" )
        data.entindex = self.entindex()
        DispatchEffect( "AR2Impact", data )
            
            
    def GetTracerType(self): return "AR2Tracer"
    #events = dict(BaseClass.events)
    #events.update( {
    #    'ANIM_RANGE_ATTACK1' : EventHandlerAnimation(Activity.ACT_RANGE_ATTACK1),
    #} )
    acttables = {
        Activity.ACT_IDLE : Activity.ACT_IDLE,
        Activity.ACT_RUN : Activity.ACT_WALK,
        Activity.ACT_WALK : Activity.ACT_WALK,
    }

    def PreDetonate(self):

        self.SetTouch(None)
        self.SetThink(self.Explode)
        self.SetNextThink(gpGlobals.curtime + 0.1)
        #self.SetNextThink(gpGlobals.curtime + 1.0)

    shouldgib = True
    def Explode(self):
        self.takedamage = DAMAGE_NO
        ExplosionCreate(self.WorldSpaceCenter(), self.GetLocalAngles(), self, 1, 128, True )

        info = CTakeDamageInfo(self, self, 1, DMG_GENERIC)
        self.Event_Killed(info)

        # Remove myself a frame from now to avoid doing it in the middle of running AI
        self.SetThink(self.SUB_Remove)
        self.SetNextThink(gpGlobals.curtime)

        nGib = random.randint(3,6)
        if self.shouldgib:
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

    if isserver:
        class BehaviorGenericClass(BaseClass.BehaviorGenericClass):
            class ActionDie(BaseAction):
                def OnStart(self):
                    self.outer.PreDetonate()

    regenerationtime = 0
    def UnitThink(self):
        super().UnitThink()
        if self.health < self.maxhealth and self.unitinfo.regeneration:
            self.Regeneration()
    def Regeneration(self):
        while self.regenerationtime < gpGlobals.curtime:
            coef = 1
            if self.energy * coef > self.unitinfo.regenerationamount: 
                regenerationamount = self.unitinfo.regenerationamount
                energy = self.unitinfo.regenerationamount/coef
            else: 
                regenerationamount = self.energy*coef
                energy = self.energy
                return
            self.regenerationtime = self.unitinfo.regenerationtime + gpGlobals.curtime
            self.health = min(self.health+regenerationamount, self.maxhealth) 
            self.TakeEnergy(energy)
class CrabSynthInfo(UnitInfo):
    name = 'unit_crab_synth'
    cls_name = 'unit_crab_synth'
    displayname = '#CombCrabSynth_Name'
    description = '#CombCrabSynth_Description'
    image_name = 'vgui/combine/units/unit_crab_synth' 
    modelname = 'models/synth_crab.mdl'
    #sound_death = 'NPC_HeadCrab.Die' 
    #scalebounds = 0.375
    hulltype = 'HULL_LARGE'
    #scale = 0.75
    health = 800
    buildtime = 40.0
    costs = [('requisition', 50), ('power', 50)]
    attributes = ['synth', 'mechanic', 'pulse']
    maxspeed = 144
    turnspeed = 50
    viewdistance = 896
    sensedistance = 896
    techrequirements = ['build_comb_tech_center']
    population = 6
    regeneration = True
    regenerationamount = 10
    regenerationtime = 1.0
    unitenergy = 180
    unitenergy_initial = 180
    sound_select = 'unit_crab_synth_select'
    sound_move = 'unit_combine_elite_move'
    sound_attack = 'unit_combine_elite_attack'
    infest_zombietype = None
    abilities = {
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    class AttackRange(UnitInfo.AttackRange):
        cone = 0.7
        damage = 4.0
        attackspeed = 0.11
        usesbursts = False
        maxrange = 768.0
    attacks = ['AttackRange']
    sai_hint = set(['sai_unit_combat'])
class OverrunCrabSynthInfo(CrabSynthInfo):
    name = 'overrun_unit_crab_synth'
    costs = [('kills', 10)]
    techrequirements = ['or_tier3_research']
    buildtime = 0