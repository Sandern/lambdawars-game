from srcbase import (SOLID_BBOX, MOVETYPE_FLY, LIFE_DYING,
                     DAMAGE_YES, DAMAGE_EVENTS_ONLY, DAMAGE_NO, DONT_BLEED, FL_OBJECT, FSOLID_NOT_SOLID, MASK_SHOT,
                     SURF_SKY, MAX_TRACE_LENGTH, EF_NOSHADOW, FSOLID_TRIGGER,
                     FSOLID_VOLUME_CONTENTS, COLLISION_GROUP_WEAPON, COLLISION_GROUP_NONE, SOLID_NONE)
from vmath import Vector, QAngle, VectorAngles, AngleVectors, VectorNormalize, VectorSubtract, vec3_origin
from math import sqrt
import random
from entities import entity, WeaponSound
from core.weapons import WarsWeaponBase
from core.ents.homingprojectile import HomingProjectile
if isserver:
    from entities import CBaseEntity, RocketTrail
    from utils import (UTIL_SetSize, UTIL_Remove, ExplosionCreate, SF_ENVEXPLOSION_NOSPARKS, SF_ENVEXPLOSION_NODLIGHTS, SF_ENVEXPLOSION_NOSMOKE,
                       UTIL_TraceLine, trace_t, UTIL_PrecacheOther)
    from te import DispatchEffect, CEffectData
    from gameinterface import ConVar
    
RPG_SPEED = 1500
    
if isserver:
    @entity('rpg_missile')
    class Missile(HomingProjectile):
        """ Python implementation of the missile entity """
        def Precache(self):
            super().Precache()
        
            self.PrecacheModel('models/weapons/w_missile.mdl')
            self.PrecacheModel('models/weapons/w_missile_launch.mdl')
            self.PrecacheModel('models/weapons/w_missile_closed.mdl')
            
        def Spawn(self):
            super().Spawn()
            
            # self.SetCollisionGroup(self.CalculateIgnoreOwnerCollisionGroup())

            # self.SetSolid(SOLID_BBOX)
            # self.SetModel('models/weapons/w_missile_launch.mdl')
            # UTIL_SetSize(self, -Vector(4,4,4), Vector(4,4,4))

            self.SetThink(self.IgniteThink, gpGlobals.curtime + 0.3, 'IgniteThink')
            
            self.damage = 150.0

            self.AddFlag(FL_OBJECT)
            
        def UpdateOnRemove(self):
            self.StopSound("Missile.Ignite") # Just to be sure, in case we are removed some other way.
            
            super().UpdateOnRemove()

        EXPLOSION_RADIUS = 96
        def DoExplosion(self):
            """ The actual explosion  """
            # Explode
            # TODO: Pass right attributes here. Currently derived from owner unit.
            ExplosionCreate(self.GetAbsOrigin(), self.GetAbsAngles(), self.GetOwnerEntity(), int(self.damage), self.EXPLOSION_RADIUS,
                            SF_ENVEXPLOSION_NOSPARKS | SF_ENVEXPLOSION_NODLIGHTS | SF_ENVEXPLOSION_NOSMOKE, 0.0, self)

        def Explode(self):
            # Don't explode against the skybox. Just pretend that 
            # the missile flies off into the distance.
            forward = Vector()
            self.GetVectors(forward, None, None)

            tr = trace_t()
            UTIL_TraceLine(self.GetAbsOrigin(), self.GetAbsOrigin() + forward * 16, MASK_SHOT, self, COLLISION_GROUP_NONE, tr)

            self.takedamage = DAMAGE_NO
            self.SetSolid(SOLID_NONE)
            if tr.fraction == 1.0 or not (tr.surface.flags & SURF_SKY):
                self.DoExplosion()

            if self.rockettrail:
                self.rockettrail.SetLifetime(0.1)
                self.rockettrail = None

            if self.owner:
                self.owner.NotifyRocketDied()
                self.owner = None

            self.StopSound("Missile.Ignite")
            UTIL_Remove(self)

        def MissileTouch(self, pOther):
            assert( pOther )
            
            # Don't touch triggers (but DO hit weapons)
            if pOther.IsSolidFlagSet(FSOLID_TRIGGER|FSOLID_VOLUME_CONTENTS) and pOther.GetCollisionGroup() != COLLISION_GROUP_WEAPON:
                # Some NPCs are triggers that can take damage (like antlion grubs). We should hit them.
                if (pOther.takedamage == DAMAGE_NO) or (pOther.takedamage == DAMAGE_EVENTS_ONLY):
                    return

            self.Explode()

        def CreateSmokeTrail(self):
            if self.rockettrail:
                return

            # Smoke trail.
            self.rockettrail = RocketTrail.CreateRocketTrail()
            if self.rockettrail:
                self.rockettrail.opacity = 0.2
                self.rockettrail.spawnrate = 100
                self.rockettrail.particlelifetime = 0.5
                self.rockettrail.startcolor = Vector( 0.65, 0.65 , 0.65 )
                self.rockettrail.endcolor = Vector( 0.0, 0.0, 0.0 )
                self.rockettrail.startsize = 8
                self.rockettrail.endsize = 32
                self.rockettrail.spawnradius = 4
                self.rockettrail.minspeed = 2
                self.rockettrail.maxspeed = 16
                
                self.rockettrail.SetLifetime( 999 )
                self.rockettrail.FollowEntity( self, "0" )
            
        def IgniteThink(self):
            self.SetModel('models/weapons/w_missile.mdl')

            #TODO: Play opening sound
            self.EmitSound( "Missile.Ignite" )

            self.velocity = RPG_SPEED
            
            self.CreateSmokeTrail()

        @classmethod
        def Create(cls, vecOrigin, vecAngles, owner, enemy, damage=150, attributes=None):
            missile = CBaseEntity.Create("rpg_missile", vecOrigin, vecAngles, owner)
            missile.attackattributes = attributes
            missile.SetOwnerEntity(owner)
            if owner:
                missile.SetOwnerNumber(owner.GetOwnerNumber())
            
            missile.dietime = gpGlobals.curtime + 6.0
            missile.velocity = 320
            
            missile.Spawn()
            missile.AddEffects(EF_NOSHADOW)
            missile.damage = damage
            
            vecForward = Vector()
            AngleVectors(vecAngles, vecForward)

            missile.SetTargetAndFire(enemy)
            #missile.SetAbsVelocity(vecForward * 300 + Vector(0,0, 128))

            return missile

        rockettrail = None
        damage = 200.0
        modelname = 'models/weapons/w_missile_launch.mdl'
        
RPG_BEAM_SPRITE = "effects/laser1_noz.vmt"
RPG_LASER_SPRITE = "sprites/redglow1.vmt"


@entity('weapon_rpg', networked=True)
class WeaponRPG(WarsWeaponBase):
    clientclassname = 'weapon_rpg'
    
    if isserver:
        def Precache(self):
            super().Precache()

            self.PrecacheScriptSound('Missile.Ignite')
            self.PrecacheScriptSound('Missile.Accelerate')

            # Laser dot...
            self.PrecacheModel('sprites/redglow1.vmt')
            self.PrecacheModel(RPG_LASER_SPRITE)
            self.PrecacheModel(RPG_BEAM_SPRITE)

            UTIL_PrecacheOther('rpg_missile')

    def StartRangeAttack(self, enemy):
        super().StartRangeAttack(enemy)

        owner = self.GetOwner()

        owner.DoMuzzleFlash()

        self.SendWeaponAnim(self.GetPrimaryAttackActivity())

        # self.clip1 = self.clip1 - 1

        vecShootOrigin, vecShootDir = self.GetShootOriginAndDirection()

        # NOTE: Do not use nextprimaryattack for attack time sound, otherwise it fades out too much.
        self.WeaponSound(WeaponSound.SINGLE, gpGlobals.curtime)
        self.nextprimaryattack = gpGlobals.curtime + self.firerate

        vecAngles = QAngle()
        VectorAngles(vecShootDir, vecAngles)

        if isserver:
            missile = Missile.Create(vecShootOrigin, vecAngles, owner, enemy,
                                     self.AttackPrimary.damage, attributes=self.primaryattackattributes)
            missile.owner = self.GetHandle()

            owner.DispatchEvent('OnOutOfClip')

    def PrimaryAttack(self):
        pass
            
    def NotifyRocketDied(self):
        pass
    
    class AttackPrimary(WarsWeaponBase.AttackRange):
        minrange = 128.0
        maxrange = 1024.0
        attackspeed = 2.392
        damage = 25
        cone = WarsWeaponBase.AttackRange.DOT_5DEGREE
        # TODO: Not applied right now due usage of ExplosionCreate. Instead attributes from unit are used.
        attributes = ['rpg']
