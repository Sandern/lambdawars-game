from srcbase import MAX_TRACE_LENGTH
from vmath import Vector, QAngle
from entities import entity, FireBulletsInfo_t, WeaponSound
from core.units import UnitInfo
from core.weapons import WarsWeaponBase, VECTOR_CONE_7DEGREES
from particles import PrecacheParticleSystem, DispatchParticleEffect, PATTACH_POINT_FOLLOW
from gameinterface import CPASFilter

@entity('tf_weapon_scattergun', networked=True)
class WeaponScatterGun(WarsWeaponBase):
    def __init__(self):
        super(WeaponScatterGun, self).__init__()
        
        self.minrange2 = 0.0
        self.maxrange2 = 200.0
        self.bulletspread = VECTOR_CONE_7DEGREES
        
        #if isserver:
        #    self.UseClientSideAnimation()
        
    if isserver:
        def Precache(self):
            super(WeaponScatterGun, self).Precache()
            
            PrecacheParticleSystem('muzzle_scattergun')
        
    def PrimaryAttack(self):
        owner = self.GetOwner()

        owner.DoMuzzleFlash()
        
        self.SendWeaponAnim( self.GetPrimaryAttackActivity() )

        #self.clip1 = self.clip1 - 1

        vecShootOrigin, vecShootDir = self.GetShootOriginAndDirection()
        
        # NOTE: Do not use nextprimaryattack for attack time sound, otherwise it fades out too much.
        self.WeaponSound(WeaponSound.SINGLE, gpGlobals.curtime)
        self.nextprimaryattack = gpGlobals.curtime + self.firerate
        
        info = FireBulletsInfo_t()
        info.shots = 7
        info.vecsrc = vecShootOrigin
        info.vecdirshooting = vecShootDir
        info.vecspread = self.bulletspread
        info.distance = MAX_TRACE_LENGTH
        info.ammotype = self.primaryammotype
        info.tracerfreq = 0

        owner.FireBullets(info)
        
        if isclient:
            # Muzzle flash
            filter = CPASFilter(self.GetAbsOrigin())
            filter.SetIgnorePredictionCull(True)
            DispatchParticleEffect("muzzle_scattergun", PATTACH_POINT_FOLLOW, self.GetMuzzleAttachEntity(), "muzzle", False, -1, filter)
            
    clientclassname = 'tf_weapon_scattergun' 
    
    class AttackPrimary(UnitInfo.AttackRange):
        maxrange = 500.0
        attackspeed = 0.625