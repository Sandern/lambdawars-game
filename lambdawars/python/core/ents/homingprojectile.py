"""Homing projectile entity for Lambda Wars.

Defines a projectile that homes in on a target and applies damage on impact,
with optional particle effects and explosion behavior.
"""
from srcbase import *
from vmath import *
from entities import CBaseAnimating as BaseClass, entity
from particles import *
from fields import StringField, EHandleField, FloatField, BooleanField
from playermgr import relationships
import ndebugoverlay
if isserver:
    from entities import CreateEntityByName, DispatchSpawn, FL_EDICT_ALWAYS, CTakeDamageInfo, D_HT
    from utils import UTIL_SetSize, UTIL_EntitiesInBox, UTIL_SetOrigin
    
@entity('projectile_homing', networked=True)
class HomingProjectile(BaseClass):
    """Projectile entity that steers toward a target. Always hits the target."""
    def UpdateTransmitState(self):
        return self.SetTransmitState(FL_EDICT_ALWAYS)
        
    projfx = None
    def OnDataChanged(self, type):
        """Client update hook used to keep the particle trail in sync."""
        super().OnDataChanged(type)

        if self.projfx:
            self.UpdateLastKnowOrigin()
            self.projfx.SetControlPoint(1, self.lastorigin)
            self.projfx.SetControlPoint(2, Vector(self.velocity, 0, 0))
            
            if (self.GetAbsOrigin() - self.lastorigin).Length() < 32.0:
                self.projfx.StopEmission()
                self.projfx.SetControlPoint(2, Vector(0, 0, 0))
                return
                
    def OnParticleEffectChanged(self):
        """(Client) Create or clear the homing particle effect if settings change."""
        if self.particleeffect and self.projtarget:
            prop = self.ParticleProp()
            
            self.UpdateLastKnowOrigin()
                
            # Assume the particle is using "pull toward control point".
            # Control point 1 is the target location.
            # Control point 2 is the force being used (of which only x is set)
            self.projfx = prop.Create(self.particleeffect, PATTACH_ABSORIGIN)
            if self.projfx:
                self.projfx.SetControlPoint(1, self.lastorigin)
                self.projfx.SetControlPoint(2, Vector(self.velocity, 0, 0))
        else:
            self.projfx = None

    def UpdateLastKnowOrigin(self):
        """Update the cached target position the projectile is steering toward."""
        if not self.projtarget:
            return
        self.lastorigin = self.projtarget.BodyTarget(self.GetAbsOrigin(), False)
            
    if isserver:
        def Precache(self):
            """Precache particle systems and model used by the projectile."""
            super().Precache()

            if self.particleeffect:
                PrecacheParticleSystem(self.particleeffect)
            if self.pexplosioneffect:
                PrecacheParticleSystem(self.pexplosioneffect)
            if self.modelname:
                self.PrecacheModel(self.modelname)
            
        def Spawn(self):
            """Initialize collision, model, and trigger/think behavior."""
            self.health = 1
            self.Precache()

            self.SetCollisionGroup(self.CalculateIgnoreOwnerCollisionGroup())

            self.SetSolid(SOLID_BBOX)
            if self.modelname:
                self.SetModel(self.modelname)
            radius = self.explodetolerance
            half_bounds = Vector(radius, radius, radius)
            UTIL_SetSize(self, -half_bounds, half_bounds)

            self.SetSolidFlags(FSOLID_NOT_STANDABLE|FSOLID_NOT_SOLID|FSOLID_TRIGGER)
            self.SetMoveType(MOVETYPE_STEP)
            self.SetTouch(self.ProjectileTouch)

        def SetTargetAndFire(self, projtarget):
            """Assign a target entity and start thinking toward it."""
            if not projtarget:
                PrintWarning("Firing projectile with invalid target!\n")
                self.Remove()
                return
            self.projtarget = projtarget
            self.UpdateLastKnowOrigin()
            self.SetThink(self.ProjectileThink, gpGlobals.curtime + self.thinkfreq)
            
        @classmethod
        def SpawnProjectile(cls, owner, origin, target, damage, velocity, particleeffect=None, modelname=None, pexplosioneffect=None):
            """Factory helper for spawning and launching a homing projectile."""
            projectile = CreateEntityByName('projectile_homing')
            projectile.SetOwnerEntity(owner)
            projectile.SetOwnerNumber(owner.GetOwnerNumber())
            projectile.SetAbsOrigin(origin)
            projectile.modelname = modelname
            projectile.particleeffect = particleeffect
            projectile.pexplosioneffect = pexplosioneffect
            projectile.velocity = velocity
            projectile.damage = damage
            DispatchSpawn(projectile)
            projectile.SetTargetAndFire(target)
            
        def ProjectileThink(self):
            """Advance the projectile toward its target and handle lifetime."""
            self.UpdateLastKnowOrigin()
            origin = self.GetAbsOrigin()
            dir = self.lastorigin - origin
            dist = VectorNormalize(dir)
            traveldist = self.velocity * self.thinkfreq
            if dist < traveldist: 
                traveldist = dist
            self.SetAbsOrigin(origin + (dir * traveldist))
            self.PhysicsTouchTriggers(origin)
            # UTIL_SetOrigin(self, origin + (dir * traveldist), True)

            angles = QAngle()
            VectorAngles(dir, Vector(0, 0, 1), angles)
            self.SetAbsAngles(angles)

            # May be caused by touch method
            if self.died:
                return

            # In case the touch event does not trigger, also trigger projectile impact when very close
            if (self.GetAbsOrigin() - self.lastorigin).Length() < 1.0:
                self.OnReachEndDestination()
                self.ProjectileImpact(self.projtarget)
                return

            if self.dietime and self.dietime < gpGlobals.curtime:
                self.OnReachEndDestination()
                self.ProjectileDie()
                return
            
            self.SetNextThink(gpGlobals.curtime + self.thinkfreq)

        def OnReachEndDestination(self):
            """Stop movement callbacks when the projectile has reached its end."""
            self.died = True
            self.SetTouch(None)
            self.SetThink(None)

        def ProjectileTouch(self, other):
            """Touch handler that only reacts to hostile entities."""
            if relationships[(self.GetOwnerNumber(), other.GetOwnerNumber())] != D_HT:
                return
            self.OnReachEndDestination()
            self.ProjectileImpact(other)

        def ProjectileImpact(self, projectile_target):
            """ Called when the homing projectile is within impact tolerance. """
            self.Explode()

        def ProjectileDie(self):
            """ Called when the projectile exceeds its lifetime. """
            self.Explode()
            
        def Explode(self):
            """Apply knockback and damage in a radius, then schedule removal."""
            if self.pexplosioneffect:
                DispatchParticleEffect(self.pexplosioneffect, PATTACH_ABSORIGIN, self)
            #StopParticleEffects(self)
            
            self.particleeffect = None
            
            vec_radius = Vector(radius, radius, radius)
            origin = self.GetAbsOrigin()
                
            speedKnockback = 250.0
            enemies = UTIL_EntitiesInBox(32, origin - vec_radius, origin + vec_radius, FL_NPC)
            for e in enemies:
                if not e or e == self or self.GetOwnerNumber() == e.GetOwnerNumber(): # TODO: Check relationtype
                    continue
                
                dir = (e.GetAbsOrigin() - origin)
                VectorNormalize(dir)
                dir[2] = 0.0
                
                impactVel = (dir * speedKnockback) + Vector(0, 0, 85)
                curvel = e.GetAbsVelocity().LengthSqr()
                if curvel < 2000.0 * 2000.0:
                    e.ApplyAbsVelocityImpulse(impactVel)
                
                # splat!
                dmgInfo = CTakeDamageInfo(self, self, impactVel, e.GetAbsOrigin(), self.damage, DMG_BLAST)
                dmgInfo.attributes = self.attackattributes
                e.TakeDamage(dmgInfo)
                
            self.SetThink(self.SUB_Remove, gpGlobals.curtime + 0.2)
            
    velocity = FloatField(value=320.0, networked=True)
    modelname = None
    particleeffect = StringField(value='', networked=True, clientchangecallback='OnParticleEffectChanged')
    pexplosioneffect = None
    projtarget = EHandleField(value=None, networked=True, clientchangecallback='OnParticleEffectChanged')
    lastorigin = None
    damage = 0
    thinkfreq = 0.1
    dietime = None
    died = BooleanField(value=False)
    explodetolerance = 32.0
    attackattributes = None
