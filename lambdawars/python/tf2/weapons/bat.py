from core.weapons import WarsWeaponMelee
from entities import entity, ACT_VM_HITCENTER

@entity('tf_weapon_bat', networked=True)
class WeaponBat(WarsWeaponMelee):
    clientclassname = 'tf_weapon_bat' 
    # Bat model has no miss activities
    missactivity1 = ACT_VM_HITCENTER
    missactivity2 = ACT_VM_HITCENTER
    
    class AttackPrimary(WarsWeaponMelee.AttackPrimary):
        damage = 5.0
        maxrange = 48.0
        attackspeed = 0.5