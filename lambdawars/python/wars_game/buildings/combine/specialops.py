from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from .basepowered import PoweredBuildingInfo, BaseFactoryPoweredBuilding
from entities import entity 

@entity('build_comb_specialops', networked=True)
class CombineSpecialOps(BaseFactoryPoweredBuilding, BaseClass):
    autoconstruct = False
    buildtarget = Vector(0, -210, 32)
    buildangle = QAngle(0, 0, 0)
    customeyeoffset = Vector(0,0,96)
    
class SpecialOpsInfo(PoweredBuildingInfo):
    name = 'build_comb_specialops'
    displayname = '#BuildCombSpecOps_Name'
    description = '#BuildCombSpecOps_Description'
    cls_name = 'build_comb_specialops'
    image_name = 'vgui/combine/buildings/build_comb_specialops'
    modelname = 'models/pg_props/pg_buildings/combine/pg_specops.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_specops_destruction.mdl'
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_CONSTRUCTION'
    workactivity = 'ACT_WORK'
    explodeactivity = 'ACT_EXPLODE'
    techrequirements = ['build_comb_armory']
    costs = [('requisition', 75), ('power', 75)]
    health = 750
    buildtime = 70.0
    abilities   = {
		0 : 'unit_combine_elite',
		1 : 'unit_combine_sniper',
		#2 : 'unit_combine_heavy',
		8 : 'cancel',
    } 
    sound_select = 'build_comb_specialops'
    sound_work = 'combine_special_ops_working'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = PoweredBuildingInfo.sai_hint | set(['sai_building_barracks', 'sai_building_specops'])