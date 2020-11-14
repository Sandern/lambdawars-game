from core.buildings import WarsBuildingInfo
from . building import DotaBuilding, DotaBuildingInfo
from entities import entity, FOWFLAG_BUILDINGS_NEUTRAL_MASK

@entity('npc_dota_fort')
@entity('dota_fort')
class DotaFort(DotaBuilding):
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK
    
'''
class DotaFortInfo(DotaBuildingInfo):
    name = 'dota_fort'
    cls_name = 'dota_fort'
    displayname = 'Fort'
'''