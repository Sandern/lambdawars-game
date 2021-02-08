from vmath import Vector, QAngle, AngleVectors
from core.buildings import UnitBaseGarrisonableBuilding
from wars_game.buildings.bunker import BunkerInfo
from entities import entity 
from particles import PATTACH_POINT_FOLLOW

if isserver:
    from particles import PrecacheParticleSystem

    
@entity('build_reb_bunker', networked=True)
class RebelBunker(UnitBaseGarrisonableBuilding):
    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -210, 32)
    buildangle = QAngle(0, 0, 0)
    #customeyeoffset = Vector(0,0,150)
    rallylineenabled = False
    playerowned = False
    maxpopulation = 8

    units_dmg_modifier = 0.35
    sense_distance = 1280
    sense_cone = -0.6  # 90 degrees each side


class RebelBunkerInfo(BunkerInfo):
    name = 'build_reb_bunker'
    displayname = '#BuildRebBunker_Name'
    description = '#BuildRebBunker_Description'
    cls_name = 'build_reb_bunker'
    image_name = 'vgui/rebels/buildings/build_reb_bunker'
    
    modelname = 'models/pg_props/pg_buildings/rebels/pg_rebel_bunker.mdl'
    explodemodel = 'models/pg_props/pg_buildings/rebels/pg_rebel_bunker_des.mdl'
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_CONSTRUCTION'
    explodeactivity = 'ACT_EXPLODE'
    
    health = 800
    garrisoned_attributes = ['bunker']
    buildtime = 46.0
    attackpriority = 0
    techrequirements = ['build_reb_barracks']
    costs = [[('requisition', 20), ('scrap', 35)], [('kills', 5)]]
    sound_select = 'build_reb_bunker'
    sound_death = 'build_generic_explode1'

    abilities   = {
        0 : 'ungarrisonall',
        8: 'focusenemy_building',
        9 : 'focusclear',
        11: 'cancel',
    }

    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 128) # Amplitude, frequence, duration, radius

class DestroyHQRebelBunkerInfo(RebelBunkerInfo):
    name = 'build_reb_bunker_destroyhq'
    techrequirements = ['build_reb_barracks_destroyhq']
    
class RebelBunkerInfo(RebelBunkerInfo):
    name = 'overrun_build_reb_bunker'
    techrequirements = ['or_tier2_research']