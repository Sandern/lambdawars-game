from core.weapons import WeaponFlamer as BaseClass, VECTOR_CONE_5DEGREES
from entities import entity

@entity('wars_weapon_flamer', networked=True)
class WarsWeaponFlamer(BaseClass): 
    clientclassname = 'wars_weapon_flamer'
    
    def __init__(self):
        super().__init__()

        self.bulletspread = VECTOR_CONE_5DEGREES

    class AttackPrimary(BaseClass.AttackRange):
        damage = 3
        minrange = 0.0
        maxrange = 384.0
        attackspeed = 0.10 # Fire rate
        usesbursts = False
        minburst = 3
        maxburst = 5
        minresttime = 0.4
        maxresttime = 0.6
        attributes = ['fire']