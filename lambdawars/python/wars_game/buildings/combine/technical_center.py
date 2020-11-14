from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from .basepowered import PoweredBuildingInfo, BaseFactoryPoweredBuilding
from entities import entity 
from particles import PATTACH_POINT_FOLLOW


@entity('build_comb_tech_center', networked=True)
class CombineArmory(BaseFactoryPoweredBuilding, BaseClass):

    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -210, 32)
    buildangle = QAngle(0, 0, 0)
    #customeyeoffset = Vector(0,0,150)
    rallylineenabled = False
    
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
    workactivity = 'ACT_WORK'
    techrequirements = ['build_comb_synthfactory']
    costs = [('requisition', 60), ('power', 40)]
    resource_category = 'technology'
    health = 900
    buildtime = 48.0
    abilities = {
        0 : 'strider_maxenergy_upgrade',
        #1 : 'combine_mine_unlock',
        #2 : 'strider_maxenergy_upgrade',
        #4 : 'weaponsg_comb_unlock',
        #5 : 'weaponar2_comb_unlock',
        #6 : 'combineball_unlock',
        8 : 'cancel',
    } 
    sound_work = 'combine_armory_working'
    sound_select = 'build_comb_armory'
    sound_death = 'build_comb_armory_destroy'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = PoweredBuildingInfo.sai_hint | set(['sai_building_research'])