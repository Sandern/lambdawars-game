from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from .basepowered import PoweredBuildingInfo, BaseFactoryPoweredBuilding
from entities import entity
from particles import PATTACH_POINT_FOLLOW

if isserver:
    from particles import PrecacheParticleSystem

@entity('build_comb_synthfactory', networked=True)
class CombineSynthFactory(BaseFactoryPoweredBuilding, BaseClass):
    if isclient:
        def OnBuildStateChanged(self):
            super(CombineSynthFactory, self).OnBuildStateChanged()
            
            if self.isproducing:
                self.StartWorkParticals()
            else:
                self.StopWorkParticals()
                
        def UpdateOnRemove(self):
            super(CombineSynthFactory, self).UpdateOnRemove()
            
            self.StopWorkParticals()

        def StartWorkParticals(self):
            if self.workparticalsfx:
                return
            self.workparticalsfx = self.ParticleProp().Create("pg_light_cylinder", PATTACH_POINT_FOLLOW, 'light_a01')
            self.workparticalsfx2 = self.ParticleProp().Create("pg_light_cylinder", PATTACH_POINT_FOLLOW, 'light_a02')
            self.workparticalsfx3 = self.ParticleProp().Create("pg_light_cylinder", PATTACH_POINT_FOLLOW, 'light_a03')
            
        def StopWorkParticals(self):
            if not self.workparticalsfx:
                return
            self.ParticleProp().StopEmission(self.workparticalsfx)
            self.ParticleProp().StopEmission(self.workparticalsfx2)
            self.ParticleProp().StopEmission(self.workparticalsfx3)
            self.workparticalsfx = None
            self.workparticalsfx2 = None
            self.workparticalsfx3 = None
            
    else:
        def Precache(self):
            super(CombineSynthFactory, self).Precache()
            
            PrecacheParticleSystem( "pg_light_cylinder" )

    def FindPositionForUnit(self, unitinfo):
        return self.buildtargetabs
        
    # Settings
    autoconstruct = False
    buildtarget = Vector(0, 0, 64)
    buildangle = QAngle(0, 0, 0) 

    workparticalsfx = None
    workparticalsfx2 = None
    workparticalsfx3 = None	
    
# Register unit
class SynthFactoryInfo(PoweredBuildingInfo):
    name = "build_comb_synthfactory" 
    displayname = "#BuildCombSyntFact_Name"
    description = "#BuildCombSyntFact_Description"
    cls_name = "build_comb_synthfactory"
    image_name = "vgui/combine/buildings/build_comb_synthfactory.vmt"
    image_dis_name = 'vgui/combine/buildings/build_comb_synthfactory_dis.vmt'
    modelname = 'models/pg_props/pg_buildings/combine/pg_synth_factory.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_synth_factory_des.mdl'
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_CONSTRUCTION'
    workactivity = 'ACT_WORK'
    explodeactivity = 'ACT_EXPLODE'
    techrequirements = ['build_comb_armory']
    costs = [('requisition', 100), ('power', 100)]
    health = 1100
    buildtime = 98.0
    abilities   = {
		0 : 'unit_hunter',
		1 : 'unit_strider',
		2 : 'unit_mortar_synth',
		3 : 'unit_clawscanner',
		4 : 'unit_crab_synth',
		8 : 'cancel',
    } 
    sound_select = 'build_comb_synthfactory'
    sound_death = 'build_comb_synthfactory_destroy'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = PoweredBuildingInfo.sai_hint | set(['sai_building_barracks', 'sai_building_synth'])