from core.weapons import WarsWeaponMelee
from entities import entity
    
@entity('weapon_hammer', networked=True)
class WeaponHammer(WarsWeaponMelee):
    clientclassname = 'weapon_hammer' 
    
    class AttackPrimary(WarsWeaponMelee.AttackPrimary):
        damage = 40.0
        maxrange = 64.0
        attackspeed = 0.5
    
    def __init__(self):
        super().__init__()
        
        self.minrange2 = 0
        self.maxrange2 = 75.0