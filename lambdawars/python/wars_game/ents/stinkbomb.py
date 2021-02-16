from srcbase import (SOLID_BBOX, FSOLID_NOT_STANDABLE, COLLISION_GROUP_PROJECTILE, COLLISION_GROUP_DEBRIS,
                     FSOLID_VOLUME_CONTENTS, FSOLID_TRIGGER, DAMAGE_NO, DAMAGE_EVENTS_ONLY)
from vmath import Vector
from entities import entity
from core.ents import ThrowableObject as BaseClass
from utils import UTIL_EntitiesInSphere
from particles import PrecacheParticleSystem, PATTACH_ABSORIGIN_FOLLOW
from wars_game.abilities.throwstinkbomb import StinkBombAttack
from fields import BooleanField, FloatField

if isserver:
    from entities import CTakeDamageInfo

@entity('stinkbomb', networked=True)
class StinkBomb(BaseClass):
    if isserver:
        def Precache(self):
            self.PrecacheModel(self.STINKBOMB_MODEL)

            PrecacheParticleSystem(self.stinkbomb_particle_name)

            super().Precache()

        def Spawn(self):
            self.Precache()

            super().Spawn()

            self.SetModel(self.STINKBOMB_MODEL)

            #self.SetSolid(SOLID_BBOX)
            #self.SetMoveType(MOVETYPE_FLYGRAVITY)
            self.SetSolidFlags(FSOLID_NOT_STANDABLE)
            #self.SetCollisionGroup(self.CalculateIgnoreOwnerCollisionGroup())
            # Get better collision group?
            self.SetCollisionGroup(COLLISION_GROUP_DEBRIS)

            self.CreateVPhysics()

            #self.SetTouch(self.MolotovTouch)
        
    def CreateVPhysics(self):
        # Create the object in the physics system
        self.VPhysicsInitNormal(SOLID_BBOX, 0, False)
        self.VPhysicsGetObject().EnableDrag(False)
        return True
        
    def Detonate(self, other):
        self.SetTouch(None)
        #self.SetAbsVelocity(vec3_origin)
        self.is_stinking_on_ground = True
        self.burn_start_thinktime = gpGlobals.curtime
        self.SetThink(self.MolotovBurnThink, gpGlobals.curtime)

    def VPhysicsCollision(self, index, event):
        super().VPhysicsCollision(index, event)
        
        # Require a short minimum time before we zero the velocity on collision
        if gpGlobals.curtime - self.spawntime < 0.15:
            return

        # Try merge with nearby dropped stinkbombs to reduce clutter
        targets = UTIL_EntitiesInSphere(320, self.GetAbsOrigin(), 32.0, 0)
        for target in targets:
            if target and target != self and target.GetClassname() == self.GetClassname() and target.is_stinking_on_ground:
                # Increase stink time
                target.burn_start_thinktime = gpGlobals.curtime
                # Remove our self
                self.SetThink(self.SUB_Remove, gpGlobals.curtime)
                return
            
        physobj = self.VPhysicsGetObject()
        vel = Vector()
        ang = Vector()
        physobj.GetVelocity(vel, ang)
        vel.x = vel.y = 0.0
        physobj.SetVelocity(vel, ang)

        self.Detonate(None)

    def MolotovTouch(self, other):
        if other.IsSolidFlagSet(FSOLID_VOLUME_CONTENTS | FSOLID_TRIGGER):
            # Some NPCs are triggers that can take damage (like antlion grubs). We should hit them.
            if (other.takedamage == DAMAGE_NO) or (other.takedamage == DAMAGE_EVENTS_ONLY):
                return

        if other.GetCollisionGroup() == COLLISION_GROUP_PROJECTILE:
            return
                
        self.Detonate(other)

    def MolotovBurnThink(self):
        if self.burn_start_thinktime + self.stinbomb_duration < gpGlobals.curtime:
            self.SetThink(self.SUB_Remove, gpGlobals.curtime)
            return

        srcdamage = self.GetAbsOrigin()
        attacker = self.GetThrower()

        # TODO: in a better way!?
        attributes = {}
        for attr in StinkBombAttack.attributes:
            attributes[attr.name] = attr(attacker)

        targets = UTIL_EntitiesInSphere(320, self.GetAbsOrigin(), self.stinkbomb_radius, 0)
        for target in targets:
            if not target or not target.IsUnit():
                continue

            dmg_info = CTakeDamageInfo(self, attacker, 0, 0)
            dmg_info.SetDamagePosition(srcdamage)
            dmg_info.attributes = attributes
            dmg_info.forcefriendlyfire = False

            target.TakeDamage(dmg_info)

        self.SetNextThink(gpGlobals.curtime + 3.0)

    if isclient:
        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            self.DestroyStinkBombParticle()

        def OnIsStinkingOnGround(self):
            self.CreateStinkBombParticle()

        def DestroyStinkBombParticle(self):
            if not self.stinkbomb_particle:
                return
            self.ParticleProp().StopEmission(self.stinkbomb_particle, False, True, False, True)
            self.stinkbomb_particle = None

        def CreateStinkBombParticle(self):
            if self.stinkbomb_particle:
                return
            self.stinkbomb_particle = self.ParticleProp().Create(self.stinkbomb_particle_name, PATTACH_ABSORIGIN_FOLLOW)
            self.stinkbomb_particle.SetControlPoint(1, Vector(self.stinkbomb_radius, 0, 0))

    burn_start_thinktime = 0
    #STINKBOMB_MODEL = 'models/pg_props/pg_weapons/pg_molotov.mdl'
    STINKBOMB_MODEL = "models/props_junk/garbage_glassbottle003a.mdl"

    stinkbomb_particle = None
    stinkbomb_particle_name = 'pg_stink_bomb'
    is_stinking_on_ground = BooleanField(value=False, networked=True, clientchangecallback='OnIsStinkingOnGround')
    stinkbomb_radius = FloatField(value=220.0)
    stinbomb_duration = FloatField(value=3.0)
