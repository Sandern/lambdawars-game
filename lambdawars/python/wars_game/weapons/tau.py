from srcbase import SURF_SKY, DMG_SHOCK, FL_NPC
from vmath import Vector, vec3_origin
from gameinterface import CPVSFilter
from utils import UTIL_ImpactTrace, UTIL_Tracer, TRACER_DONT_USE_ATTACHMENT
from entities import entity, Activity, WeaponSound, CBeam, FireBulletsInfo_t
from core.weapons import WarsWeaponMachineGun, VECTOR_CONE_1DEGREES, WarsWeaponBase
from te import CEffectData, DispatchEffect, te
from fields import FloatField
from wars_game.statuseffects import StunnedEffectInfo
from wars_game.attributes import TauCannonAltAttribute
if isserver:
    from entities import CTakeDamageInfo, RadiusDamage, CLASS_NONE
    from utils import UTIL_EntitiesInBox


@entity('weapon_tau', networked=True)
class WeaponTau(WarsWeaponBase):
    def __init__(self):
        super().__init__()

        self.bulletspread = VECTOR_CONE_1DEGREES
        self.serverdoimpactandtracer = True
    
    def DoImpactEffect(self, tr, damagetype):
        # Draw our beam
        self.DrawBeam(tr.startpos, tr.endpos, 2.4)
        
        if (tr.surface.flags & SURF_SKY) == False:
            filter = CPVSFilter(tr.endpos)
            te.GaussExplosion(filter, 0.0, tr.endpos, tr.plane.normal, 0)

            UTIL_ImpactTrace(tr, self.primaryammotype)
        
    def DrawBeam(self, startPos, endPos, width):
        if isclient:
            # Tracer down the middle
            UTIL_Tracer(startPos, endPos, 0, TRACER_DONT_USE_ATTACHMENT, 6500, False, "GaussTracer")
        else:
            #Draw the main beam shaft
            beam = CBeam.BeamCreate(self.GAUSS_BEAM_SPRITE, 0.5)
            
            beam.SetStartPos( startPos )
            beam.PointEntInit( endPos, self )
            beam.SetEndAttachment(self.LookupAttachment("Muzzle"))
            beam.SetWidth( width )
            beam.SetEndWidth( 0.05 )
            beam.SetBrightness( 255 )
            beam.SetColor( 255, 185+random.randint( -16, 16 ), 40 )
            beam.RelinkBeam()
            beam.LiveForTime( 0.1 )

            #Draw electric bolts along shaft
            beam = CBeam.BeamCreate(self.GAUSS_BEAM_SPRITE, 3.0)
            
            beam.SetStartPos( startPos )
            beam.PointEntInit( endPos, self )
            beam.SetEndAttachment(self.LookupAttachment("Muzzle") )

            beam.SetBrightness( random.randint( 64, 255 ) )
            beam.SetColor( 255, 255, 150+random.randint( 0, 64 ) )
            beam.RelinkBeam()
            beam.LiveForTime( 0.1 )
            beam.SetNoise( 1.6 )
            beam.SetEndWidth( 0.1 )
    def PrimaryAttack(self):
        owner = self.GetOwner()

        #owner.DoMuzzleFlash()
        
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
        info.damage = float(self.AttackPrimary.damage) / info.shots
        info.attributes = self.primaryattackattributes

        owner.FireBullets(info)
    def SecondaryAttack(self, origin, dmg, radius, duration=1.1, target=None):
        self.nextprimaryattack = self.nextsecondaryattack = gpGlobals.curtime + duration
        self.WeaponSound(WeaponSound.WPN_DOUBLE, gpGlobals.curtime) 
        self.SendWeaponAnim(Activity.ACT_VM_FIDGET)
        self.dmg = dmg
        self.origin = origin
        self.radius = radius
        self.target = target
        self.SetThink(self.DelayedAttack, self.nextprimaryattack, "DelayedFire")
    origin = None
    dmg = 0
    radius = 0
    target = None
    def DelayedAttack(self):
        dmg = self.dmg
        radius = self.radius
        target = self.target
        if target:
            origin = self.target.GetAbsOrigin()
        else:
            origin = self.origin
        owner = self.GetOwner()
        #owner.DoMuzzleFlash()
        
        self.SendWeaponAnim(Activity.ACT_VM_SECONDARYATTACK)

        #self.clip1 = self.clip1 - 1

        vecShootOrigin, vecShootDir = self.GetShootOriginAndDirection()
        
        # NOTE: Do not use nextprimaryattack for attack time sound, otherwise it fades out too much.
        self.WeaponSound(WeaponSound.SPECIAL1, gpGlobals.curtime)
        self.nextprimaryattack = self.nextsecondaryattack = gpGlobals.curtime + 1.5

        info = FireBulletsInfo_t()
        info.shots = 1
        info.vecsrc = vecShootOrigin
        info.vecdirshooting = vecShootDir
        info.vecspread = self.bulletspread
        info.distance = self.maxbulletrange
        info.ammotype = self.primaryammotype
        info.tracerfreq = 0
        info.damage = 0

        owner.FireBullets(info)
        owner.DoAnimation(owner.ANIM_ALTFIRE)
        self.RadiusDamage(origin, dmg, radius)
    def RadiusDamage(self, origin, dmg, radius):
        owner = self.GetOwner()
        dmg_info = CTakeDamageInfo(self, owner, dmg, DMG_SHOCK) 
        dmg_info.attributes = {TauCannonAltAttribute.name: TauCannonAltAttribute(owner)}
        #dmg_info.attributes = None

        RadiusDamage(dmg_info, origin, radius, CLASS_NONE, None) 
        vec_radius = Vector(radius, radius, radius)
        enemies = UTIL_EntitiesInBox(32, origin-vec_radius, origin+vec_radius, FL_NPC)
        for enemy in enemies:
            if not owner.IsValidEnemy(enemy):
                continue
            if not enemy.IsAlive():
                continue
            StunnedEffectInfo.CreateAndApply(enemy, attacker=owner, duration=3)
    

    clientclassname = 'weapon_tau'
    muzzleoptions = ''
    
    class AttackPrimary(WarsWeaponBase.AttackRange):
        maxrange = 896.0
        attackspeed = 0.30
        shots = 1
        damage = 10
        attributes = ['tau']