from entities import entity, FireBulletsInfo_t, WeaponSound
from core.weapons import WarsWeaponBase, VECTOR_CONE_15DEGREES, VECTOR_CONE_10DEGREES, WarsWeaponMachineGun, VECTOR_CONE_1DEGREES


@entity('weapon_winchester1886', networked=True)
class WeaponShotgunWinchester(WarsWeaponBase):
    def __init__(self):
        super().__init__()
        self.bulletspread = VECTOR_CONE_1DEGREES
    def PrimaryAttack(self):
        owner = self.GetOwner()

        owner.DoMuzzleFlash()
        
        self.SendWeaponAnim(self.GetPrimaryAttackActivity())

        #self.clip1 = self.clip1 - 1

        vecShootOrigin, vecShootDir = self.GetShootOriginAndDirection()
        
        # NOTE: Do not use nextprimaryattack for attack time sound, otherwise it fades out too much.
        self.WeaponSound(WeaponSound.SINGLE, gpGlobals.curtime)
        self.nextprimaryattack = gpGlobals.curtime + self.firerate
        
        info = FireBulletsInfo_t()
        info.shots = 1
        info.vecsrc = vecShootOrigin
        info.vecdirshooting = vecShootDir
        info.vecspread = self.bulletspread
        info.distance = self.maxbulletrange
        info.ammotype = self.primaryammotype
        info.tracerfreq = 0
        info.damage = float(self.overrideammodamage) / info.shots
        info.attributes = self.primaryattackattributes

        owner.FireBullets(info)
    clientclassname = 'weapon_winchester1886'
    muzzleoptions = 'SHOTGUN MUZZLE'
    class AttackPrimary(WarsWeaponBase.AttackRange):
        maxrange = 768.0
        attackspeed = 2.0
        damage = 10
        cone = WarsWeaponBase.AttackRange.DOT_1DEGREE
        attributes = ['winchester']