from . building import DotaBuilding, DotaBuildingInfo
from entities import entity, FOWFLAG_BUILDINGS_NEUTRAL_MASK

@entity('npc_dota_barracks')
@entity('dota_barracks')
class DotaBarracks(DotaBuilding):
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK
    
'''class DotaBarracksInfo(DotaBuildingInfo):
    name = 'dota_barracks'
    cls_name = 'dota_barracks'
    displayname = 'Barracks'
    '''