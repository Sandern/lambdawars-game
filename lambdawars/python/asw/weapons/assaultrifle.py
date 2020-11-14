from entities import entity, Activity
from core.weapons import WarsWeaponMachineGun, VECTOR_CONE_5DEGREES

@entity('asw_weapon_rifle', networked=True)
class WeaponAssaultRifle(WarsWeaponMachineGun):
    def __init__(self):
        super(WeaponAssaultRifle, self).__init__()

        self.bulletspread = VECTOR_CONE_5DEGREES
 
    clientclassname = 'asw_weapon_rifle'
    
    class AttackPrimary(WarsWeaponMachineGun.AttackPrimary):
        maxrange = 820.0
        attackspeed = 0.075 # Fire rate
        usesbursts = True
        minburst = 3
        maxburst = 5
        minresttime = 0.4
        maxresttime = 0.6

