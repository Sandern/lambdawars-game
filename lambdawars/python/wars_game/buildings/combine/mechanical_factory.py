from srcbase import SOLID_BBOX
from vmath import Vector, QAngle
from core.buildings import UnitBaseFactory as BaseClass
from .basepowered import PoweredBuildingInfo, BaseFactoryPoweredBuilding
from entities import entity 


@entity('build_comb_mech_factory', networked=True)
class CombineMechanicalFactory(BaseFactoryPoweredBuilding, BaseClass):
    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -210, 32)
    buildangle = QAngle(0, 0, 0)
    customeyeoffset = Vector(0, 0, 60)
    buildingsolidmode = SOLID_BBOX


class MechFactoryInfo(PoweredBuildingInfo):
    name = 'build_comb_mech_factory'
    displayname = '#BuildCombMechFactory_Name'
    description = '#BuildCombMechFactory_Description'
    cls_name = 'build_comb_mech_factory'
    image_name = 'vgui/combine/buildings/build_comb_mech'
    modelname = 'models/pg_props/pg_buildings/combine/pg_combine_mech_factory.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_combine_mech_factory_destruction.mdl'
    techrequirements = ['build_comb_garrison']
    idleactivity = 'ACT_IDLE'
    workactivity = 'ACT_WORK'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    costs = [('requisition', 35)]
    health = 500
    buildtime = 30.0
    abilities = {
        0: 'unit_scanner',
        1: 'unit_manhack',
        2: 'unit_rollermine',
        8: 'cancel',
    } 
    sound_work = 'combine_mech_factory_working'
    sound_select = 'build_combine_mech_factory'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'pg_combine_base_ex'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = PoweredBuildingInfo.sai_hint | set(['sai_building_mech_factory'])
