from srcbase import MAX_TRACE_LENGTH
from entities import entity, FireBulletsInfo_t, WeaponSound
from core.weapons import WarsWeaponBase, VECTOR_CONE_15DEGREES
from core.units import UnitInfo
from gamerules import GetAmmoDef
from vmath import Vector

@entity('weapon_pulse_shotgun', networked=True)
class WeaponPulseShotgun(WarsWeaponBase):
    def __init__(self):
        super().__init__()

        self.bulletspread = VECTOR_CONE_15DEGREES
        self.tracercolor = Vector(0.1882, 0.502, 0.596)
        self.ammotype = GetAmmoDef().Index("AR2")
		
    def GetTracerType(self): return "AR2Tracer"    
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
        info.shots = 6
        info.vecsrc = vecShootOrigin
        info.vecdirshooting = vecShootDir
        info.vecspread = self.bulletspread
        info.distance = self.maxbulletrange
        #info.ammotype = self.primaryammotype
        info.ammotype = self.ammotype
        info.tracerfreq = 1
        info.damage = float(self.AttackPrimary.damage) / info.shots
        info.attributes = self.primaryattackattributes

        owner.FireBullets(info)

    clientclassname = 'weapon_pulse_shotgun'
    muzzleoptions = 'COMBINE MUZZLE'

    class AttackPrimary(WarsWeaponBase.AttackRange):
        maxrange = 512.0
        attackspeed = 0.8
        damage = 60
        cone = WarsWeaponBase.AttackRange.DOT_6DEGREE
        attributes = ['pulse_shotgun']