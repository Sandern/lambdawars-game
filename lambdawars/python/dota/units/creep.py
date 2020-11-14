from srcbase import *
from vmath import *
from .basedota import UnitDotaInfo, UnitDota as BaseClass
from entities import entity

@entity('npc_dota_creep')
@entity('npc_dota_creep_lane')
@entity('npc_dota_creep_neutral')
@entity('npc_dota_creep_diretide')
class UnitCreep(BaseClass):
    def __init__(self):
        super().__init__()
        
        self.minslope = 0.5
        
    # Vars
    maxspeed = 200.0
    yawspeed = 40.0
    jumpheight = 40.0
    
    def ImpactShock(self, origin, radius, magnitude, ignored = None):
        pass

class UnitBaseCreep(UnitDotaInfo):
    soundset = ''
    hulltype = 'DOTA_HULL_SIZE_REGULAR'
        
class UnitCreepBadguysMelee(UnitBaseCreep):
    name = "npc_dota_creep_badguys_melee"
    cls_name = "npc_dota_creep_lane"
    displayname = "#DOTA_Creep_Name"
    description = "#DOTA_Creep_Description"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = 'models/creeps/lane_creeps/creep_bad_melee/creep_bad_melee.mdl'
    hulltype = 'DOTA_HULL_SIZE_REGULAR'
    health = 550
    
    soundset = 'Creep_Good_Melee'

    #sound_select = ''
    #sound_move = ''
    #sound_death = ''
    
    abilities = {
        8 : "attackmove",
        9 : "holdposition",
    }
    
    class AttackMelee(UnitDotaInfo.AttackMelee):
        maxrange = 150.0
        damage = 20
        damagetype = DMG_SLASH
        attackspeed = 1.6
    attacks = 'AttackMelee'
    
class UnitCreepBadguysRange(UnitBaseCreep):
    name = "npc_dota_creep_badguys_ranged"
    modelname = 'models/creeps/lane_creeps/creep_bad_ranged/creep_bad_ranged.mdl'
    
class UnitCreepGoodguysMelee(UnitBaseCreep):
    name = "npc_dota_creep_goodguys_melee"
    cls_name = "npc_dota_creep_lane"
    displayname = "#DOTA_Creep_Name"
    description = "#DOTA_Creep_Description"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = 'models/creeps/lane_creeps/creep_radiant_melee/radiant_melee.mdl'
    hulltype = 'DOTA_HULL_SIZE_REGULAR'
    health = 550

    #sound_select = ''
    #sound_move = ''
    #sound_death = ''
    
    abilities = {
        8 : "attackmove",
        9 : "holdposition",
    }
    
    class AttackMelee(UnitDotaInfo.AttackMelee):
        maxrange = 150.0
        damage = 20
        damagetype = DMG_SLASH
        attackspeed = 1.6
    attacks = 'AttackMelee'
    
class UnitCreepGoodguysRange(UnitCreepGoodguysMelee):
    name = "npc_dota_creep_goodguys_ranged"
    modelname = 'models/creeps/lane_creeps/creep_radiant_ranged/radiant_ranged.mdl'