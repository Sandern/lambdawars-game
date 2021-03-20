"""
A building that launches ignited barrels in the direction of nearby enemies.
"""
from srcbase import *
from vmath import *
from core.buildings import WarsBuildingInfo, UnitBaseBuilding as BaseClass
from core.abilities import AbilityTarget
from core.units import CreateUnit
from entities import entity, MouseTraceData, FClassnameIs
from fow import FogOfWarMgr
import random
from fields import FloatField, ListField, IntegerField

if isserver:
    from entities import CreateEntityByName, DispatchSpawn, variant_t, CPhysicsProp, PropBreakablePrecacheAll, CTakeDamageInfo, RadiusDamage, Class_T
    from core.units import UnitCombatSense
    from utils import UTIL_Remove, ExplosionCreate
    @entity('wars_barrel')
    class Barrel(CPhysicsProp):
        damagecontroller = None
        def UpdateOnRemove(self):
            if self.damagecontroller:
                self.damagecontroller.Remove()
            
            super().UpdateOnRemove()
        def OnTakeDamage(self, info): return 0
        def SetIgnite(self, lifetime):
            self.SetThink(self.Detonate, gpGlobals.curtime + lifetime - 0.1, 'SelfDestructThink')
            self.Ignite(lifetime, False)
        def Detonate(self):
            self.damagecontroller = CreateUnit('grenade_frag_damage', owner_number=self.GetOwnerNumber())
            self.damagecontroller.unit_owner = self.GetOwnerEntity()
            origin = self.GetAbsOrigin()
            ExplosionCreate(origin, self.GetAbsAngles(), self.damagecontroller, self.damage, self.damageradius, True )
            #info = CTakeDamageInfo(self, self.damagecontroller, self.damage, self.damagetype)
            #info.attributes = {ExplosiveAttribute.name : ExplosiveAttribute(self.GetThrower())}
            #RadiusDamage(info, origin, self.damageradius, Class_T.CLASS_NONE, self.GetOwnerEntity())
            UTIL_Remove(self)
        damage = 500
        damageradius = 300
        damagetype = DMG_BLAST
        


@entity('build_reb_barreltrap', networked=True)
class RebelsBarrelTrap(BaseClass):
    autoconstruct = False
    buildtarget = Vector(0, -280, 32)
    buildangle = QAngle(0, 0, 0)
    
    senses = None
    
    barrels = ListField()
    barrelcount = IntegerField(value=0, networked=True)

    sai_hint = set(['sai_defense'])
    
    def Spawn(self):
        super().Spawn()
        
        if isserver:
            self.senses = UnitCombatSense(self)
            self.senses.testlos = True
            self.senses.sensedistance = 1408.0
            
            self.SetThink(self.AutocastThink, gpGlobals.curtime, 'AutocastThink')
            
    def UpdateOnRemove(self):
        super().UpdateOnRemove()
        
        self.senses = None
        
        if isserver:
            self.RemoveExplosiveBarrels()
            
    def Event_Killed(self, info):
        self.ReleaseExplosiveBarrels(launch=False)
        
        super().Event_Killed(info)
        
    def OnConstructed(self):
        super().OnConstructed()
    
        if isserver:
            self.LoadExplosiveBarrels()
            
    def OnTakeDamage_Alive(self, info):
        # Don't take damage by launched barrels
        attacker = info.GetAttacker()
        inflictor = info.GetInflictor()
        if attacker and FClassnameIs(attacker, 'entityflame'):
            return 0
            
        return super().OnTakeDamage_Alive(info)
            
    def RemoveExplosiveBarrels(self):
        for barrel in self.barrels: 
            barrel.Remove()
        del self.barrels[:]
        self.barrelcount = 0
        
    def LoadExplosiveBarrels(self):
        forward = Vector()
        sideward = Vector()
        self.GetVectors(forward, sideward, None)
        
        angles = self.GetAbsAngles()
        
        for i in range(0, 2):
            #barrel = CreateEntityByName( "prop_physics" )
            barrel = CreateEntityByName( "wars_barrel" )
            barrel.KeyValue('model', 'models/props_c17/oildrum001_explosive_small.mdl')
            if i == 0:
                barrel.SetAbsOrigin(self.GetAbsOrigin() + Vector(0, 30, 150))
            else:
                barrel.SetAbsOrigin(self.GetAbsOrigin() + Vector(0, -30, 150))
            barrel.SetAbsAngles(angles+QAngle(0, 20*i, 0))
            barrel.AcceptInput('Wake', None, None, variant_t(), 0)
            barrel.SetOwnerEntity(self)
            barrel.SetOwnerNumber(self.GetOwnerNumber())
            barrel.AddFOWFlags(self.fowflags)
            DispatchSpawn( barrel )      
            barrel.Activate()
            barrel.VPhysicsGetObject().EnableMotion(False)
            barrel.damage = self.unitinfo.barreldmg
            barrel.damageradius = self.unitinfo.barrelradius
            self.barrels.append(barrel)
        self.barrelcount = len(self.barrels)
    
    def ReleaseExplosiveBarrels(self, direction=None, speed=4000.0, launch=True, reloadtime=8.0):
        if not self.barrels:
            return False
            
        if not direction:
            direction = Vector()
            self.GetVectors(direction, None, None)
        
        for barrel in self.barrels: 
            if not barrel:
                continue
            physobj = barrel.VPhysicsGetObject()
            #barrel.Ignite(4.0, False)
            barrel.SetIgnite(self.unitinfo.barreltime)
            physobj.EnableMotion(True)
            if launch:
                angvel = Vector(random.uniform(-30, 30), random.uniform(-30, 30), random.uniform(-30, 30))
                physobj.AddVelocity(direction * speed, angvel)
            else:
                physobj.Wake()
        del self.barrels[:]
        self.barrelcount = 0
        
        self.SetThink(self.ReloadBarrelsThink, gpGlobals.curtime + reloadtime, 'ReloadBarrelsThink')
        return True
        
    def ReloadBarrelsThink(self):
        if not self.IsAlive():
            return
        self.LoadExplosiveBarrels()
        
    def AutocastThink(self):
        info = self.abilitiesbyname.get('release_barrels', None)
        if info and self.abilitycheckautocast.get(info.uid, False):
            self.senses.PerformSensing()
            info.CheckAutoCast(self)
        
        self.SetNextThink(gpGlobals.curtime + 0.5, 'AutocastThink')

class AbilityReleaseBarrels(AbilityTarget):
    name = 'release_barrels'
    displayname = "#AbilityReleaseBarrels_Name"
    description = "#AbilityReleaseBarrels_Description"
    image_name  = 'vgui/rebels/abilities/rebels_release_barrels.vmt'
    rechargetime = 12
    #costs = [('scrap', 4)]
    maxrange = FloatField(value=1408.0)
    supportsautocast = True
    defaultautocast = True

    sai_hint = AbilityTarget.sai_hint | set(['sai_grenade'])
    
    @classmethod 
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)

        if not unit.barrelcount:
            requirements.add('barrels')
        return requirements
    
    def DoAbility(self):
        data = self.player.GetMouseData()
        targetpos = data.endpos
        owner = self.ownernumber

        if not self.SelectSingleUnit():
            self.Cancel(cancelmsg='No unit', debugmsg='no unit')
            return
        
        if not isserver:
            return
            
        if not self.TakeResources(refundoncancel=True):
            self.Cancel(cancelmsg='#Ability_NotEnoughResources', debugmsg='not enough resources')
            return

        if FogOfWarMgr().PointInFOW(targetpos, owner):
            self.Cancel(cancelmsg='#Ability_NoVision', debugmsg='Player has no vision at target point')
            return
            
        data = self.mousedata
        direction = data.endpos - self.unit.GetAbsOrigin() + Vector(0, 0, 300)
        speed = VectorNormalize(direction)
        speed = min(speed, self.maxrange)
        
        if not self.unit.ReleaseExplosiveBarrels(direction=direction, speed=speed, launch=True, reloadtime=self.rechargetime):
            self.Cancel(cancelmsg='Could not launch barrels', debugmsg='barrel launch method failed')
            return
            
        self.SetRecharge(self.unit)
        self.Completed()
            
    @classmethod
    def CheckAutoCast(info, unit):
        enemy = unit.senses.GetNearestEnemy()
        if not enemy:
            return
            
        enemyorigin = enemy.GetAbsOrigin()
        
        if info.CanDoAbility(None, unit=unit):
            leftpressed = MouseTraceData()
            leftpressed.endpos = enemyorigin
            leftpressed.groundendpos = enemyorigin
            leftpressed.ent = enemy
            unit.DoAbility(info.name, mouse_inputs=[('leftpressed', leftpressed)])
            return True
        return False
    
    def UpdateParticleEffects(self, inst, targetpos):
        if not self.unit:
            return
        inst.SetControlPoint(0, self.unit.GetAbsOrigin() + self.particleoffset)
        inst.SetControlPoint(2, Vector(self.maxrange, self.maxrange, 0))
        inst.SetControlPoint(4, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
        
    infoparticles = ['range_radius']

class BarrelTrapInfo(WarsBuildingInfo):
    name = "build_reb_barreltrap" 
    cls_name = "build_reb_barreltrap"
    displayname = '#BuildRebBarrelTrap_Name'
    description = '#BuildRebBarrelTrap_Description'
    image_name  = 'vgui/rebels/buildings/build_reb_barreltrap'
    modelname = 'models/pg_props/pg_buildings/rebels/pg_barrel_trap.mdl'
    explodemodel = 'models/pg_props/pg_buildings/rebels/pg_barrel_trap_des.mdl'
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_CONSTRUCTION'
    explodeactivity = 'ACT_EXPLODE'
    costs = [('requisition', 25), ('scrap', 10)]
    techrequirements = ['build_reb_munitiondepot']
    health = 300
    viewdistance = 896
    buildtime = 20.0
    scale = 0.9

    barreldmg = 300
    barrelradius = 192
    barreltime = 4

    abilities   = {
        0 : 'release_barrels',
        8 : 'cancel',
    }
    sound_select = 'build_reb_barreltrap'
    sound_death = 'build_reb_barreltrap_destruction'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    
    # Target ability setting
    requirerotation = False
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_tp_defense', 'sai_building'])
    
    def UpdateParticleEffects(self, inst, targetpos):
        inst.SetControlPoint(0, targetpos)
        inst.SetControlPoint(1, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
        inst.SetControlPoint(2, Vector(128, 0, 0))
        forward = Vector()
        AngleVectors(self.targetangle, forward)
        inst.SetControlPoint(3, targetpos + forward * 32.0)
        
    #infoparticles = ['direction_indicator']
	
class DestroyHQBarrelTrapInfo(BarrelTrapInfo):
    name = 'build_reb_barreltrap_destroyhq'
    techrequirements = ['build_reb_munitiondepot_destroyhq']

class BarrelTrapCharInfo(BarrelTrapInfo):
    name = 'build_reb_char_barreltrap'
    techrequirements = []
    costs = []
    rechargetime = 90.0