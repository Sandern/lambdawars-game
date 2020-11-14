from vmath import Vector
from core.buildings import WarsBuildingInfo
from core.buildings import UnitBaseGarrisonableBuilding as BaseClass, GarrisonableBuildingInfo
from entities import entity

@entity('build_rebel_outhouse')
class RebelsOutHouse(BaseClass):
    maxpopulation = 3
    playerowned = True
    autoconstruct = False
    
class RebelsAidStationInfo(GarrisonableBuildingInfo):
    name = "build_reb_outhouse"
    displayname = "#BuildRebOuthouse_Name"
    description = "#BuildRebOuthouse_Description"
    cls_name = "build_rebel_outhouse"
    image_name  = 'vgui/rebels/buildings/build_reb_billet'
    modelname = 'models/brush/rebels/outhouse.mdl'
    idleactivity = 'ACT_FINISHED'
    constructionactivity = 'ACT_CONSTRUCTION'
    explodeactivity = 'ACT_FINISHED'
    health = 65
    buildtime = 20.0
    viewdistance = 300
    costs = [[('scrap', 6)], [('kills', 5)]]
    techrequirements = ['build_reb_hq']
    abilities   = {
        0 : 'ungarrisonall',
        8 : 'cancel',
    } 
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_aid'])