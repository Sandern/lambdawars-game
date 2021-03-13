from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from .basepowered import PoweredBuildingInfo, BaseFactoryPoweredBuilding
from entities import entity 
from particles import PATTACH_POINT_FOLLOW

if isserver:
    from particles import PrecacheParticleSystem

@entity('build_comb_tech_center', networked=True)
class TechCenterInfo(BaseFactoryPoweredBuilding, BaseClass):

    if isclient:
        def OnBuildStateChanged(self):
            super().OnBuildStateChanged()
            
            if self.isproducing:
                self.StartChimneySmoke()
            else:
                self.StopChimneySmoke()
                
        def UpdateOnRemove(self):
            super().UpdateOnRemove()
            
            self.StopChimneySmoke()
            
        def ExplodeHandler(self, event):
            self.StopChimneySmoke()
            super().ExplodeHandler(event)

        def StartChimneySmoke(self):
            if self.chimneyfx and self.chimneyfx1:
                return
            self.chimneyfx = self.ParticleProp().Create("pg_strider_up_center_base", PATTACH_POINT_FOLLOW, 'effect')
            
        def StopChimneySmoke(self):
            if not self.chimneyfx and not self.chimneyfx1:
                return
            self.ParticleProp().StopEmission(self.chimneyfx)
            self.chimneyfx = None
            self.ParticleProp().StopEmission(self.chimneyfx1)
            self.chimneyfx1 = None
            
    else:
        def Precache(self):
            super().Precache()
            
            PrecacheParticleSystem("pg_strider_up_center_base")

    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -210, 32)
    buildangle = QAngle(0, 0, 0)
    #customeyeoffset = Vector(0,0,150)
    rallylineenabled = False
    
    chimneyfx = None
    chimneyfx1 = None


# Register unit
class TechCenterInfo(PoweredBuildingInfo):
    name = 'build_comb_tech_center' 
    displayname = '#BuildCombTechCenter_Name'
    description = '#BuildCombTechCenter_Description'
    cls_name = 'build_comb_tech_center'
    image_name = 'vgui/combine/buildings/build_comb_tech_center'
    modelname = 'models/pg_props/pg_buildings/combine/pg_technical_center.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_technical_center_destruction.mdl'
    explodemodel_lightingoffset = Vector(0, 0, 250)
    idleactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    #workactivity = 'ACT_WORK'
    techrequirements = ['build_comb_synthfactory']
    costs = [('requisition', 50), ('power', 50)]
    resource_category = 'technology'
    health = 900
    buildtime = 64.0
    abilities = {
        0 : 'strider_maxenergy_upgrade',
        1 : 'combinemine_upgrade',
        2 : 'mortarsynth_upgrade',
        #4 : 'weaponsg_comb_unlock',
        #5 : 'weaponar2_comb_unlock',
        #6 : 'combineball_unlock',
        8 : 'cancel',
    } 
    sound_work = 'combine_armory_working'
    sound_select = 'build_comb_tech_center'
    sound_death = 'build_comb_armory_destroy'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = PoweredBuildingInfo.sai_hint | set(['sai_building_research'])