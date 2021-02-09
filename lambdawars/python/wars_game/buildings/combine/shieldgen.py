import random

from srcbase import SOLID_OBB, FSOLID_NOT_SOLID, DMG_SHOCK, Color
from vmath import (VectorNormalize, VectorAngles, AngleVectors, QAngle, Vector, VectorYawRotate, DotProduct, 
                  matrix3x4_t, AngleMatrix, TransformAABB)
            
from core.buildings import WarsBuildingInfo, UnitBaseBuilding as BaseClass
from .basepowered import PoweredBuildingInfo, BasePoweredBuilding
from core.abilities import AbilityUpgrade

from fields import GenericField, IntegerField, FloatField
from entities import entity, SF_TRIGGER_ALLOW_NPCS
if isserver:
    from entities import gEntList, CTriggerMultiple as BaseClassShield, CreateEntityByName, DispatchSpawn, CTakeDamageInfo, DoSpark, SpawnBlood, D_LI, FL_EDICT_ALWAYS
    from particles import PrecacheParticleSystem, DispatchParticleEffect, ParticleAttachment_t
    from utils import UTIL_SetSize, UTIL_Remove
    from core.units import UnitCombatSense
else:
    from vgui import surface, scheme
    from vgui.entitybar import UnitBarScreen
    from entities import DataUpdateType_t, CLIENT_THINK_ALWAYS, C_BaseTrigger as BaseClassShield
    from particles import ParticleAttachment_t
    from te import FXCube
    from utils import GetVectorInScreenSpace
    
FORCEFIELD_PARTICLEEFFECT = 'st_elmos_fire'

if isclient:
    class UnitEnergyBarScreen(UnitBarScreen):
        """ Draws the unit health bar. """
        def __init__(self, unit):
            super(UnitEnergyBarScreen, self).__init__(unit,
                Color(0, 0, 255, 200), Color(40, 40, 40, 250), Color(150, 150, 150, 200), 
                offsety=4.0)
            
        def Draw(self):
            panel = self.GetPanel()
            if self.unit.shield:
                shield = self.unit.shield
                panel.weight = shield.energy/shield.energymax
            else:
                panel.weight = 0.0
                    
            super(UnitEnergyBarScreen, self).Draw()

# Shield
@entity('comb_shield', networked=True)
class CombineShield(BaseClassShield):
    if isserver:
        def Spawn(self):
            self.AddSpawnFlags( SF_TRIGGER_ALLOW_NPCS )
            
            self.Precache()
            
            self.touchinglist = []
            
            super().Spawn()
            
            self.SetSolid(SOLID_OBB)

            self.SetThink(self.ForceThink, gpGlobals.curtime, 'ForceThink')
            
        def UpdateOnRemove(self):
            super().UpdateOnRemove()
            
            self.gen1.RemoveLink(self)
            self.gen2.RemoveLink(self)
        
        def UpdateTransmitState(self):
            return self.SetTransmitState( FL_EDICT_ALWAYS )
        
        # TODO: Should put this in the unit ai. The movement code will try to zero out the velocity.
        def StartTouch(self, entity):
            #super().StartTouch(entity)
            if not entity.IsUnit() or entity.isbuilding or entity.IRelationType(self) == D_LI: 
                return
            
            dir = Vector()
            AngleVectors(self.GetAbsAngles(), dir)
            VectorYawRotate(dir, 90.0, dir)

            # Use steporigin since the abs origin might already be passed the forcefield
            dirent = entity.GetStepOrigin() - self.GetAbsOrigin()
            VectorNormalize(dirent)
            dot = DotProduct(dir, dirent)

            if dot < 0.0:
                VectorYawRotate(dir, 180.0, dir)
            
            self.touchinglist.append( (entity, dir) )
            self.PushEntity(entity, dir)
            
        def EndTouch(self, entity):
            for i in self.touchinglist:
                if i[0] == entity:
                    self.touchinglist.remove(i)
                    break
                    
        def PushEntity(self, entity, dir):
            if hasattr(entity, 'DispatchEvent'):
                entity.DispatchEvent('OnForceField', self)
                
            speed = 750.0
            entity.SetGroundEntity(None)
           
            entity.SetAbsVelocity(dir * speed + Vector(0, 0, 250.0))
            
            damage = 6.0
            info = CTakeDamageInfo(self, self.gen1, damage, DMG_SHOCK)
            entity.TakeDamage(info)
            
            SpawnBlood(entity.GetAbsOrigin(), Vector(0,0,1), entity.BloodColor(), damage)
            dir = Vector()
            dir.Random(-1.0, 1.0)
            DoSpark(entity, entity.GetAbsOrigin(), 100, 100, True, dir)
            
            self.energy -= self.drainperentity*self.pushfrequency

        def ForceThink(self):
            self.energy = min(self.energymax, self.energy + self.pushfrequency*self.energypersecond)
            for i in self.touchinglist:
                self.PushEntity(i[0], i[1])
            if self.energy < 0:
                self.OutOfEnergy()
            self.SetNextThink(gpGlobals.curtime + self.pushfrequency, 'ForceThink')
            
        def OutOfEnergy(self):
            self.gen1.AddDelayedLink(self.gen2, 5.0)
            self.Remove()
            
        gen1 = None
        gen2 = None
    else:
        def OnDataChanged(self, type):
            super().OnDataChanged(type)
            
            if type == DataUpdateType_t.DATA_UPDATE_CREATED:
                mins = self.WorldAlignMins()
                maxs = self.WorldAlignMaxs()
                mins.y = -2.0
                maxs.y = 2.0
                self.mesh = FXCube("effects/combineshield/comshieldwall4", Vector(1.0, 1.0, 1.0), mins, maxs, self.GetAbsOrigin(), self.GetAbsAngles())
            
        def UpdateOnRemove(self):
            super().Spawn()
            if self.mesh:
                self.mesh.Destroy()
                self.mesh = None
            
        mesh = None
    
    pushfrequency = FloatField(value=0.10)
    energymax = IntegerField(value=100, networked=True)
    energy = IntegerField(value=energymax.default, networked=True)
    energypersecond = IntegerField(value=1)
    drainperentity = IntegerField(value=15)
                    
# Forcefield Generator. Between nearby generators a forcefield is created.
@entity('build_comb_shieldgen', networked=True)
class CombineShieldGenerator(BaseClass):
    autoconstruct = False
    
    def __init__(self):
        super().__init__()

        self.links = []
        self.delayedlinks = []

    def RemoveLink(self, link):
        if link == self.shield:
            self.shield = None
        self.links.remove(link)
        
    if isserver:
        def UpdateOnRemove(self):
            super().UpdateOnRemove()
            
            self.DestroyAllLinks()
            
        def Precache(self):
            super().Precache()
            self.PrecacheScriptSound('DoSpark')
            #PrecacheParticleSystem(FORCEFIELD_PARTICLEEFFECT)
            
        def OnConstructed(self):
            super().OnConstructed()
            self.LinkToNearest()

        def LinkToNearest(self):
            # Find nearest forcefield generator
            bestgen = None
            gen = gEntList.FindEntityByClassnameWithin(None, self.link_target, self.GetAbsOrigin(), self.maxgenrange)
            while gen:
                if gen == self:
                    gen = gEntList.FindEntityByClassnameWithin(gen, self.link_target, self.GetAbsOrigin(), self.maxgenrange)
                    continue
                dist = (self.GetAbsOrigin() - gen.GetAbsOrigin()).Length2D()
                if not bestgen:
                    bestgen = gen
                    bestdist = dist
                else:
                    if dist < bestdist:
                        bestgen = gen
                        bestdist = dist
                gen = gEntList.FindEntityByClassnameWithin(gen, self.link_target, self.GetAbsOrigin(), self.maxgenrange)
                
            if bestgen and not self.GetLink(bestgen):
                self.CreateLink(bestgen)
                
        def GetLink(self, othergen):
            for link in self.links:
                if link.gen1 == othergen or link.gen2 == othergen:
                    return link
            return None
            
        def CreateLink(self, othergen):
            if othergen == self:
                return
            if othergen.powered_1:
                if not othergen.powered:
                    return
            if self.powered_1:
                if not self.powered:
                    return
            if not othergen.constructionstate is othergen.BS_CONSTRUCTED:
                return
            if not self.constructionstate is self.BS_CONSTRUCTED:
                return
                
            dir = othergen.GetAbsOrigin() - self.GetAbsOrigin()
            dir.z = 0.0
            dist = VectorNormalize(dir)
            angle = QAngle()
            VectorAngles(dir, angle)
            
            mins = -Vector((dist/2.0)-16.0, 48.0, -self.WorldAlignMins().z)
            maxs = Vector((dist/2.0)-16.0, 48.0, self.WorldAlignMaxs().z-32.0)
            
            origin = self.GetAbsOrigin() + dir * (dist/2.0)
            origin.z = self.GetAbsOrigin().z + self.WorldAlignMins().z + (maxs.z - mins.z)/2.0

            # Create the pusher
            link = CreateEntityByName('comb_shield')
            link.SetAbsOrigin(origin)
            link.SetOwnerNumber(self.GetOwnerNumber())
            DispatchSpawn(link)
            link.Activate()
            UTIL_SetSize(link, mins, maxs)
            link.SetAbsAngles(angle)
            link.Enable()
            
            link.gen1 = self.GetHandle()
            link.gen2 = othergen
            
            self.LinkToShield(link)

            othergen.LinkToShield(link)
            
        def LinkToShield(self, shield):
            self.links.append(shield)
            self.shield = shield
            
        def DestroyLink(self, link):
            UTIL_Remove(link)
            
        def DestroyAllLinks(self):
            links = self.links[:]
            for link in links:
                self.DestroyLink(link)
        
        def AddDelayedLink(self, othergen, delay):
            self.delayedlinks.append( (othergen, gpGlobals.curtime + delay ) )
            self.SetThink(self.DelayedLinkThink, 0.1, 'DelayedLinkThink')
        
        def DelayedLinkThink(self):
            if not self.delayedlinks:
                return
            delayedlinks = list(self.delayedlinks)
            for dl in delayedlinks:
                if dl[1] < gpGlobals.curtime:
                    if dl[0] and not self.GetLink(dl[0]):
                        self.CreateLink(dl[0])
                    self.delayedlinks.remove(dl)
                    
            self.SetThink(self.DelayedLinkThink, 0.1, 'DelayedLinkThink')
            
    else:
        def ShowBars(self):
            if self.barsvisible:
                return
                
            self.energybarscreen = UnitEnergyBarScreen(self)
                
            super().ShowBars()
            
        def HideBars(self):
            if not self.barsvisible:
                return
                
            self.energybarscreen.Shutdown()
            self.energybarscreen = None
            
            super().HideBars()

    maxgenrange = FloatField(value=1024.0)
    shield = GenericField(value=None, networked=True)
    link_target = 'build_comb_shieldgen'
    powered_1 = False

@entity('build_comb_shieldgen_powered', networked=True )
class CombineShieldGeneratorPowered(BasePoweredBuilding, CombineShieldGenerator):
    def Spawn(self):
        super().Spawn()

        self.SetCanBeSeen(False)
    if isserver:
        def OnPoweredChanged(self):
            BasePoweredBuilding.OnPoweredChanged(self)
            if not self.powered:
                self.DestroyAllLinks()
                self.SetCanBeSeen(True)
            else:
                self.LinkToNearest()
                self.SetCanBeSeen(False)
                
        def CreateLink(self, othergen):
            if self.powered:
                super().CreateLink(othergen)
            
    autoconstruct = False
    buildtarget = Vector(0, -210, 0)
    buildangle = QAngle(0, 0, 0)
    #customeyeoffset = Vector(0,0,150)
    rallylineenabled = False
    link_target = 'build_comb_shieldgen_powered'
    powered_1 = True

class OverrunCombineShieldGenInfo(WarsBuildingInfo):
    name = 'overrun_build_comb_shieldgen'
    displayname = '#BuildCombShieldGen_Name'
    description = '#BuildCombShieldGen_Description'
    cls_name = 'build_comb_shieldgen' #they dont need power in overeun
    image_name = 'vgui/combine/buildings/build_comb_shield.vmt'
    image_dis_name = 'vgui/combine/buildings/build_comb_shield.vmt'
    modelname = 'models/props_combine/combine_generator01.mdl'
    health = 300
    buildtime = 25.0
    attributes = ['building', 'stun']
    placemaxrange = 96.0
    placeatmins = True
    viewdistance = 896
    costs = [('kills', 3)]
    techrequirements = ['or_tier3_research']
    abilities = {
        0 : 'genconnect',
        1 : 'gendestroylinks',
        8 : 'cancel',
    }
    sound_death = 'build_comb_mturret_explode'
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_shieldgen'])

class CombineShieldGenInfo(PoweredBuildingInfo):
    name = 'build_comb_shieldgen'
    cls_name = 'build_comb_shieldgen_powered'
    displayname = '#BuildCombShieldGen_Name'
    description = '#BuildCombShieldGen_Description'
    image_name = 'vgui/combine/buildings/build_comb_shield.vmt'
    image_dis_name = 'vgui/combine/buildings/build_comb_shield.vmt'
    modelname = 'models/props_combine/combine_generator01.mdl'
    health = 500
    buildtime = 20.0
    placemaxrange = 96.0
    placeatmins = True
    viewdistance = 640
    attributes = ['building', 'stun']
    costs = [('requisition', 15), ('power', 15)]
    techrequirements = ['build_comb_armory']
    abilities = {
        0 : 'genconnect_powered',
        1 : 'gendestroylinks',
        8 : 'cancel',
    }
    sound_death = 'build_comb_mturret_explode'
    sai_hint = PoweredBuildingInfo.sai_hint | set(['sai_building_shieldgen'])

class AbilityDefenseCombineUnlock(AbilityUpgrade):
    name = 'combine_defense_buildings_unlock'
    displayname = '#DefenseCombineUnlock_Name'
    description = '#DefenseCombineUnlock_Description'
    image_name = "vgui/abilities/unlock_defense.vmt"
    buildtime = 60.0
    costs = [('requisition', 50), ('power', 50)]