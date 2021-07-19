from vmath import Vector, QAngle
from core.buildings import UnitBaseGarrisonableBuilding, CreateDummy
from wars_game.buildings.bunker import BunkerInfo
from entities import entity 
from particles import PATTACH_POINT_FOLLOW

if isserver:
    from particles import PrecacheParticleSystem

    
@entity('build_comb_bunker', networked=True)
class CombineBunker(UnitBaseGarrisonableBuilding):
    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -210, 32)
    buildangle = QAngle(0, 0, 0)
    #customeyeoffset = Vector(0,0,150)
    rallylineenabled = False
    playerowned = False
    maxpopulation = 8

    units_dmg_modifier = 0.20
    sense_distance = 1408
    sense_cone = -0.6  # 0 for 90 degrees each side, -1 for 360 degrees, 1 for vice versa


class CombineBunkerInfo(BunkerInfo):
    name = 'build_comb_bunker'
    displayname = '#BuildCombBunker_Name'
    description = '#BuildCombBunker_Description'
    cls_name = 'build_comb_bunker'
    image_name = 'vgui/combine/buildings/build_comb_bunker'
    
    modelname = 'models/pg_props/pg_buildings/combine/pg_combine_bunker.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_combine_bunker_des.mdl'
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_CONSTRUCTION'
    explodeactivity = 'ACT_EXPLODE'
    
    health = 1500
    garrisoned_attributes = ['bunker']
    attributes = ['defence']
    buildtime = 30.0
    attackpriority = 0
    #sense_distance = 2000
    techrequirements = ['build_comb_armory']
    costs = [[('requisition', 40), ('power', 10)], [('kills', 5)]]
    sound_select = 'build_comb_bunker'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 128) # Amplitude, frequence, duration, radius
    
    dummies = [
        CreateDummy(
            modelname='models/pg_props/pg_buildings/combine/pg_combine_bunker_shild.mdl',
            offset=Vector(0, 0, 0),
            constructionactivity='ACT_CONSTRUCTION',
            decorative=True,
        )
    ]
    
class OverrunCombineBunkerInfo(CombineBunkerInfo):
    name = 'overrun_build_comb_bunker'
    techrequirements = ['or_tier2_research']
    costs = [('kills', 25)]
    buildtime = 30.0
    health = 6000