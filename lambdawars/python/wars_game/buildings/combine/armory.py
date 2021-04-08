from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from .basepowered import PoweredBuildingInfo, BaseFactoryPoweredBuilding
from entities import entity 
from particles import PATTACH_POINT_FOLLOW

if isserver:
    from particles import PrecacheParticleSystem

@entity('build_comb_armory', networked=True)
class CombineArmory(BaseFactoryPoweredBuilding, BaseClass):

    if isclient:
        def OnBuildStateChanged(self):
            super(CombineArmory, self).OnBuildStateChanged()
            
            if self.isproducing:
                self.StartWorkParticals()
            else:
                self.StopWorkParticals()
                
        def UpdateOnRemove(self):
            super(CombineArmory, self).UpdateOnRemove()
            
            self.StopWorkParticals()

        def StartWorkParticals(self):
            if self.workparticalsfx:
                return
            self.workparticalsfx = self.ParticleProp().Create("pg_blue_flash", PATTACH_POINT_FOLLOW, 'antena')
            
        def StopWorkParticals(self):
            if not self.workparticalsfx:
                return
            self.ParticleProp().StopEmission(self.workparticalsfx)
            self.workparticalsfx = None
            
    else:
        def Precache(self):
            super(CombineArmory, self).Precache()
            
            PrecacheParticleSystem("pg_blue_flash")

    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -210, 32)
    buildangle = QAngle(0, 0, 0)
    #customeyeoffset = Vector(0,0,150)
    rallylineenabled = False

    workparticalsfx = None
    
# Register unit
class ArmoryInfo(PoweredBuildingInfo):
    name = 'build_comb_armory' 
    displayname = '#BuildCombArmory_Name'
    description = '#BuildCombArmory_Description'
    cls_name = 'build_comb_armory'
    image_name = 'vgui/combine/buildings/build_comb_armory'
    modelname = 'models/pg_props/pg_buildings/combine/pg_combine_armory.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_combine_armory_des.mdl'
    explodemodel_lightingoffset = Vector(0, 0, 250)
    idleactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    workactivity = 'ACT_WORK'
    #zoffset = -8.0
    techrequirements = ['build_comb_garrison']
    costs = [('requisition', 50), ('power', 25)]
    resource_category = 'technology'
    health = 750
    buildtime = 50.0
    abilities = {
        #0 : 'grenade_unlock_combine',
        #1 : 'combine_upgrade_tier_mid',
        #1 : 'combine_mine_unlock',
        0 : 'weaponsg_comb_unlock',
        1 : 'weaponar2_comb_unlock',
        2 : 'combine_hp_upgrade',
        3 : 'floor_turret_unlock',
        4 : 'combineball_unlock',
        8 : 'cancel',
    } 
    sound_work = 'combine_armory_working'
    sound_select = 'build_comb_armory'
    sound_death = 'build_comb_armory_destroy'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = PoweredBuildingInfo.sai_hint | set(['sai_building_research'])