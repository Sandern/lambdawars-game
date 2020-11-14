from srcbase import *
from vmath import *
from .basedota import UnitDotaInfo, UnitDota as BaseClass
from entities import entity

@entity('hero_skeletonking', networked=True)
class UnitSkeletonKing(BaseClass):
    # Vars
    maxspeed = 290.0
    yawspeed = 40.0
    jumpheight = 40.0

# Register unit
class UnitSkeletonKing(UnitDotaInfo):
    name = "hero_skeletonking"
    cls_name = "hero_skeletonking"
    displayname = "#DOTA_SK_Name"
    description = "#DOTA_SK_Description"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = 'models/heroes/skeleton_king/skeleton_king.mdl'
    hulltype = 'HULL_HERO_LARGE'
    health = 500

    #sound_select = ''
    #sound_move = ''
    #sound_death = ''
    
    abilities = {
        8 : "attackmove",
        9 : "holdposition",
    }
    
    class AttackMelee(UnitDotaInfo.AttackMelee):
        maxrange = 150.0
        damage = 50
        damagetype = DMG_SLASH
        attackspeed = 1.6
    attacks = 'AttackMelee'
    