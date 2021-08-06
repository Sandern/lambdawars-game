from entities import entity, FireBulletsInfo_t, WeaponSound, Activity
from core.weapons import WarsWeaponBase, WarsWeaponMachineGun, VECTOR_CONE_1DEGREES
from wars_game.attributes import WinchesterAltAttribute


@entity('weapon_winchester1886', networked=True)
class WeaponWinchester(WarsWeaponBase):
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
        owner.DoAnimation(owner.ANIM_ALTFIRE)
    def SecondaryAttack(self, duration=2.0):
        self.nextprimaryattack = self.nextsecondaryattack = gpGlobals.curtime + duration
        #self.WeaponSound(WeaponSound.WPN_DOUBLE, gpGlobals.curtime) 
        self.SendWeaponAnim(Activity.ACT_VM_FIDGET)
        self.SetThink(self.DelayedAttack, self.nextprimaryattack, "DelayedFire")
    def DelayedAttack(self):
        owner = self.GetOwner()

        owner.DoMuzzleFlash()
        
        self.SendWeaponAnim(Activity.ACT_VM_SECONDARYATTACK)

        #self.clip1 = self.clip1 - 1

        vecShootOrigin, vecShootDir = self.GetShootOriginAndDirection()
        
        # NOTE: Do not use nextprimaryattack for attack time sound, otherwise it fades out too much.
        self.WeaponSound(WeaponSound.SINGLE, gpGlobals.curtime)

        self.nextprimaryattack = self.nextsecondaryattack = gpGlobals.curtime + self.firerate

        info = FireBulletsInfo_t()
        info.vecsrc = vecShootOrigin
        info.vecdirshooting = vecShootDir
        info.vecspread = self.bulletspread
        info.distance = self.maxbulletrange + 256
        info.ammotype = self.primaryammotype
        info.tracerfreq = 0
        info.damage = (2 * float(self.overrideammodamage)) # * self.dmg
        #info.attributes = self.primaryattackattributes
        info.attributes = {WinchesterAltAttribute.name: WinchesterAltAttribute(owner)}

        owner.FireBullets(info)
        owner.DoAnimation(owner.ANIM_ALTFIRE)

    clientclassname = 'weapon_winchester1886'
    muzzleoptions = 'SHOTGUN MUZZLE'
    class AttackPrimary(WarsWeaponBase.AttackRange):
        maxrange = 896.0
        attackspeed = 2.0
        damage = 75
        cone = WarsWeaponBase.AttackRange.DOT_1DEGREE
        attributes = ['winchester', 'bullet']