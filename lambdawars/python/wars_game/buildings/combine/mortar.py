'''
Combine Mortar.
'''
from srcbase import DMG_BLAST, DMG_DISSOLVE, MASK_SOLID_BRUSHONLY, COLLISION_GROUP_NONE
from vmath import Vector, QAngle, vec3_origin, VectorAngles
from core.buildings import UnitBaseBuilding as BaseClass, CreateDummy
from .basepowered import PoweredBuildingInfo, BaseFactoryPoweredBuilding
from core.abilities import AbilityTarget
from entities import entity, MouseTraceData
from fields import FloatField, input, fieldtypes
from particles import PrecacheParticleSystem, DispatchParticleEffect, PATTACH_CUSTOMORIGIN
from gameinterface import CPASAttenuationFilter
from fow import FogOfWarMgr

if isserver:
    from entities import CTakeDamageInfo, RadiusDamage, CLASS_NONE
    from core.units import UnitCombatSense
    from utils import UTIL_ScreenShake, SHAKE_START, UTIL_DecalTrace, UTIL_TraceLine, trace_t


@entity('build_comb_mortar', networked=True)
class CombineMortar(BaseFactoryPoweredBuilding, BaseClass):
    autoconstruct = False
    buildtarget = Vector(0, -280, 32)
    buildangle = QAngle(0, 0, 0)

    particlemortarbasebeam_name = 'particle_mortar_beam_base'
    
    particlemortarbeam_name = 'particle_mortar_beam'
    particlemortarelements_name = 'particle_mortar_elements'
    particlemortarsplash_name = 'particle_mortar_splash'
    
    senses = None

    isfiringmortar = False
    damage = 100.0
    dmgradius = 320.0
    fireposition = vec3_origin
    
    def __init__(self):
        super().__init__()
        
        self.friendlydamage = True

    def Spawn(self):
        super().Spawn()

        if isserver:
            self.senses = UnitCombatSense(self)
            self.senses.testlos = True
            self.senses.sensedistance = 1280.0

    def Precache(self):
        super().Precache()
        
        self.PrecacheScriptSound("comb_mortar_shot")
        self.PrecacheScriptSound("comb_mortar_land")
        
        PrecacheParticleSystem(self.particlemortarbasebeam_name)
        PrecacheParticleSystem(self.particlemortarbeam_name)
        PrecacheParticleSystem(self.particlemortarelements_name)
        PrecacheParticleSystem(self.particlemortarsplash_name)
    
    @input(inputname='FireMorter', helpstring='Fire Morter to a given position', fieldtype=fieldtypes.FIELD_EHANDLE)
    def InputFireMortar(self, inputdata):
        target = inputdata.value.Entity()
        #targetname = inputdata.value.String()
        #target = entitylist.FindEntityByName(None, targetname)
        if not target:
            targetname = inputdata.value.String()
            PrintWarning('#%d.InputFireMortar: Could not find target entity %s\n' % (self.entindex(), targetname))
            return

        self.FireMortar(target.GetAbsOrigin())

    def FireMortar(self, position):
        if self.isfiringmortar:
            return
            
        self.fireposition = position
        self.EmitSound("comb_mortar_shot")
        
        filter = CPASAttenuationFilter(position, "comb_mortar_land")
        self.EmitSoundFilter(filter, 0, "comb_mortar_land", position, 0.0)
        
        baseorigin = self.GetAbsOrigin()
        
        tr = trace_t()
        UTIL_TraceLine(self.fireposition + Vector(0, 0, 32), self.fireposition - Vector(0, 0, 128), MASK_SOLID_BRUSHONLY, self, COLLISION_GROUP_NONE, tr)
        
        angles = QAngle(0, 0, 0)
        anglesLanding = QAngle(0,0,0)
        VectorAngles(tr.plane.normal, anglesLanding)
        anglesLanding += QAngle(90, 0, 0)
        
        maxs = self.CollisionProp().OBBMaxs()
        DispatchParticleEffect(self.particlemortarbasebeam_name, baseorigin + Vector(0, 0, maxs.z), angles)
    
        #DispatchParticleEffect(self.particlemortarbeam_name, position + Vector(0, 0, 32), angles)
        DispatchParticleEffect(self.particlemortarelements_name, position + Vector(0, 0, 32), anglesLanding)
        DispatchParticleEffect(self.particlemortarsplash_name, position + Vector(0, 0, 32), anglesLanding)
        
        self.SetThink(self.DoMortarDamage, gpGlobals.curtime + 2.5, 'DoMortarDamageThink')
        self.isfiringmortar = True
        
    def DoMortarDamage(self):
        self.isfiringmortar = False
        
        tr = trace_t()
        UTIL_TraceLine(self.fireposition, self.fireposition - Vector(0, 0, 128), MASK_SOLID_BRUSHONLY, self, COLLISION_GROUP_NONE, tr)

        UTIL_DecalTrace(tr, "Scorch")
        
        damage = self.damage
        dmgradius = self.dmgradius
        vecreported = vec3_origin
        blastforce = Vector(0, 0, 1000.0)

        info = CTakeDamageInfo(self, self, None, blastforce, self.fireposition, damage, (DMG_BLAST|DMG_DISSOLVE), 0, vecreported)

        RadiusDamage(info, self.fireposition, dmgradius, CLASS_NONE, None)
        
        UTIL_ScreenShake(self.fireposition, 10, 60, 1.0, 550, SHAKE_START, True)


class AbilityCombFireMortar(AbilityTarget):
    name = 'fire_mortar'
    displayname = "#AbilityCombineFireMortar_Name"
    description = "#AbilityCombineFireMortar_Description"
    image_name  = 'vgui/combine/abilities/combine_fire_mortar.vmt'
    rechargetime = 6
    #costs = [('power', 20)]
    energy = 40
    maxrange = FloatField(value=1280.0)
    supportsautocast = True
    defaultautocast = True

    sai_hint = AbilityTarget.sai_hint | set(['sai_grenade'])
    
    def DoAbility(self):
        if not self.SelectSingleUnit():
            self.Cancel(cancelmsg='No unit', debugmsg='no unit')
            return
            
        if not isserver:
            return
            
        data = self.mousedata
        targetpos = data.endpos
        owner = self.ownernumber
        
        if self.ischeat:
            self.unit.FireMortar(targetpos)
            self.Completed()
            return
            
        if FogOfWarMgr().PointInFOW(targetpos, owner):
            self.Cancel(cancelmsg='#Ability_NoVision', debugmsg='Player has no vision at target point')
            return
            
        if not self.unit.powered:
            self.Cancel(cancelmsg='#Ability_NotPowered', debugmsg='Not in power generator range')
            return
            
        startpos = self.unit.GetAbsOrigin()
        dist = startpos.DistTo(targetpos)
        if dist > self.maxrange:
            self.Cancel(cancelmsg='#Ability_OutOfRange', debugmsg='must be fired within range')
            return
            
        if not self.TakeResources(refundoncancel=True):
            self.Cancel(cancelmsg='#Ability_NotEnoughResources', debugmsg='not enough resources')
            return
            
        self.unit.FireMortar(targetpos)
        
        unit = self.TakeEnergy(self.unit)
        self.SetRecharge(self.unit)
        self.Completed()

    @classmethod
    def CheckAutoCast(info, unit):
        unit.senses.PerformSensing()

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

    @classmethod
    def OnUnitThink(info, unit):
        if not unit.AllowAutoCast() or not unit.abilitycheckautocast[info.uid]:
            return

        info.CheckAutoCast(unit)

    def UpdateParticleEffects(self, inst, targetpos):
        if not self.unit:
            return
        inst.SetControlPoint(0, self.unit.GetAbsOrigin() + self.particleoffset)
        inst.SetControlPoint(2, Vector(self.maxrange, self.maxrange, 0))
        inst.SetControlPoint(4, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
        
    infoparticles = ['range_radius']
    #stuff for later:
    #maxhealth = UpgradeField(abilityname='defensecombine_tier_1', cppimplemented=True)
    #health = UpgradeField(abilityname='defensecombine_tier_1', cppimplemented=True)
        
    
class MortarInfo(PoweredBuildingInfo):
    name = "build_comb_mortar" 
    cls_name = "build_comb_mortar"
    displayname = '#BuildCombMortar_Name'
    description = '#BuildCombMortar_Description'
    image_name  = 'vgui/combine/buildings/build_comb_mortar'
    modelname = 'models/props_combine/combine_mortar01a.mdl'
    attributes = ['building', 'mortar']
    modelname = 'models/pg_props/pg_buildings/combine/pg_combine_mortar.mdl'
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_CONSTRUCTION'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_combine_mortar_destruction.mdl'
    explodeactivity = 'ACT_EXPLODE'
    costs = [('requisition', 50), ('power', 20)]
    unitenergy = 100
    unitenergy_initial = 40
    techrequirements = ['build_comb_armory']
    viewdistance = 768.0
    health = 200
    buildtime = 25.0
    scale = 0.9
    abilities = {
        0: 'fire_mortar',
        8: 'cancel',
    }
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sound_death = 'build_comb_mturret_explode'
    
    # Target ability setting
    requirerotation = False
    sai_hint = PoweredBuildingInfo.sai_hint | set(['sai_tp_defense', 'sai_building'])