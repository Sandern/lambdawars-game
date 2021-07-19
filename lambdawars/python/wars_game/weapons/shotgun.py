from srcbase import MAX_TRACE_LENGTH
from entities import entity, FireBulletsInfo_t, WeaponSound
from core.weapons import WarsWeaponBase, VECTOR_CONE_15DEGREES
from core.units import UnitInfo

@entity('weapon_shotgun', networked=True)
class WeaponShotgun(WarsWeaponBase):
    def __init__(self):
        super().__init__()

        self.bulletspread = VECTOR_CONE_15DEGREES
        
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
        info.shots = 8
        info.vecsrc = vecShootOrigin
        info.vecdirshooting = vecShootDir
        info.vecspread = self.bulletspread
        info.distance = self.maxbulletrange
        info.ammotype = self.primaryammotype
        info.tracerfreq = 0
        info.damage = float(self.AttackPrimary.damage) / info.shots
        info.attributes = self.primaryattackattributes

        owner.FireBullets(info)

    clientclassname = 'weapon_shotgun'
    muzzleoptions = 'SHOTGUN MUZZLE'

    class AttackPrimary(WarsWeaponBase.AttackRange):
        maxrange = 512.0
        attackspeed = 0.65
        damage = 25
        cone = WarsWeaponBase.AttackRange.DOT_6DEGREE
        #attributes = ['bullet']
        attributes = ['bullet', 'buckshot']