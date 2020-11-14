from entities import entity
from core.weapons import WeaponFlamer as BaseClass, VECTOR_CONE_5DEGREES

@entity('asw_weapon_flamer', networked=True)
class ASWWeaponFlamer(BaseClass):
    def __init__(self):
        super(ASWWeaponFlamer, self).__init__()

        self.bulletspread = VECTOR_CONE_5DEGREES

    clientclassname = 'asw_weapon_flamer'
    
    class AttackPrimary(BaseClass.AttackRange):
        damage = 5
        minrange = 0.0
        maxrange = 350.0
        attackspeed = 0.1 # Fire rate
        usesbursts = True
        minburst = 3
        maxburst = 5
        minresttime = 0.4
        maxresttime = 0.6