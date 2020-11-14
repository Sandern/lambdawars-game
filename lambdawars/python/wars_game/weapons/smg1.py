from entities import entity, Activity
from core.weapons import WarsWeaponMachineGun, VECTOR_CONE_5DEGREES, VECTOR_CONE_3DEGREES

@entity('weapon_smg1', networked=True)
class WeaponSmg1(WarsWeaponMachineGun):
    def __init__(self):
        super().__init__()
        
        self.bulletspread = VECTOR_CONE_5DEGREES

    clientclassname = 'weapon_smg1'
    muzzleoptions = 'SMG1 MUZZLE'
    
    class AttackPrimary(WarsWeaponMachineGun.AttackPrimary):
        maxrange = 640.0
        attackspeed = 0.09 # Fire rate
        usesbursts = True
        minburst = 3
        maxburst = 3
        minresttime = 0.3
        maxresttime = 0.38
        attributes = ['bullet']

@entity('weapon_smg1_sw', networked=True)
class WeaponSmg1SW(WeaponSmg1):
    def __init__(self):
        super().__init__()

        self.bulletspread = VECTOR_CONE_3DEGREES

    class AttackPrimary(WarsWeaponMachineGun.AttackPrimary):
        maxrange = 650.0
        usesbursts = True
        minburst = 45
        maxburst = 45
        attackspeed = 0.07
        minresettime = 1.6
        maxresettime = 2.1
        attributes = ['bullet']
