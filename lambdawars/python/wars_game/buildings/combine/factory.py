from core.buildings import WarsBuildingInfo, UnitBaseBuilding as BaseClass
from entities import entity

@entity('build_comb_factory')
class CombineFactory(BaseClass):
    autoconstruct = False
    
class CombineFactoryInfo(WarsBuildingInfo):
    name = 'build_comb_factory'
    displayname = '#BuildCombFactory_Name'
    description = '#BuildCombFactory_Description'
    cls_name = 'build_comb_factory'
    modelname = 'models/pg_props/pg_buildings/combine/pg_scrap_power_generator.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_combine_energy_cell_des.mdl'
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_CONSTRUCTION'
    explodeactivity = 'ACT_EXPLODE'
    health = 500
    buildtime = 25.0
    costs = [('requisition', 30)]
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_scrapcollection_point'])
    
    placerestrictions = [
        {'unittype': 'scrap_marker', 'radius' : 180.0},
        {'unittype': 'scrap_marker_small', 'radius' : 180.0},
    ]
